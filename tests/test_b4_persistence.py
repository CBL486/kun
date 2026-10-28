from __future__ import annotations

import copy
import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memory_core import ConflictError, MemoryCore, Scope, ValidationError
from memory_core.core import lifecycle_state
from rpg_agent.loop import AgentLoop
from rpg_sim.engine import WorldEngine
from rpg_sim.scenario import initial_world
from rpg_storage.errors import StorageError
from rpg_storage.migrations import connect, migrate, rollback, schema_version
from rpg_storage.repository import WorldRepository


def run_agent_step(
    loop: AgentLoop,
    operation_id: str,
) -> tuple[dict, dict, dict, dict]:
    before = copy.deepcopy(loop.engine.snapshot())
    step = loop.run_once(operation_id)
    after = loop.engine.snapshot()
    if not step.world_result["ok"]:
        raise AssertionError(step.world_result)
    return (
        before,
        after,
        step.intent.to_dict(),
        step.world_result["event"],
    )


def committed_fixture(
    directory: str,
    *,
    simulate_projection_failure: bool = False,
):
    db_path = Path(directory) / "world.db"
    repo = WorldRepository(db_path)
    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare("2026-11-02", "08:00", "morning_1")
    before, after, action, event = run_agent_step(loop, "op_b4_fixture_001")
    repo.initialize_world(before)
    result = repo.commit_step(
        state_before=before,
        state_after=after,
        event=event,
        action=action,
        simulate_projection_failure=simulate_projection_failure,
    )
    return repo, loop, db_path, result, before, after, action, event


def base_scope() -> Scope:
    return Scope(
        tenant_id="rpg-world",
        world_id="world_qinghe_v1",
        user_id="observer_demo_001",
        character_id="char_lin_cheng",
        surface="school",
        conversation_id="day-2026-11-02",
    )


class MigrationTests(unittest.TestCase):
    def test_migrate_and_rollback_are_repeatable(self) -> None:
        with TemporaryDirectory() as temporary:
            db_path = Path(temporary) / "migration.db"
            self.assertEqual(1, migrate(db_path))
            self.assertEqual(1, migrate(db_path))
            self.assertEqual(1, schema_version(db_path))
            with connect(db_path) as conn:
                tables = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
            self.assertTrue(
                {
                    "world_heads",
                    "world_versions",
                    "actions",
                    "events",
                    "memories",
                    "memory_projection_outbox",
                    "npc_memory_slots",
                }
                <= tables
            )
            self.assertEqual(0, rollback(db_path))
            self.assertEqual(0, schema_version(db_path))
            with connect(db_path) as conn:
                exists = conn.execute(
                    """
                    SELECT 1 FROM sqlite_master
                    WHERE type = 'table' AND name = 'events'
                    """
                ).fetchone()
            self.assertIsNone(exists)


class WorldRepositoryTests(unittest.TestCase):
    def test_commit_persists_world_action_event_and_memory(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, _, _, result, _, after, _, event = committed_fixture(temporary)
            self.assertEqual("projected", result.status)
            self.assertFalse(result.replayed)
            self.assertEqual(1, len(result.memory_ids))
            self.assertEqual(1, len(repo.list_actions()))
            self.assertEqual(1, len(repo.list_events()))
            self.assertEqual(after["state_version"], repo.get_world_state()["state_version"])
            self.assertEqual(event["event_id"], repo.get_event(event["event_id"])["event_id"])
            with connect(repo.db_path) as conn:
                recalled = repo.memory.recall(
                    conn,
                    scope=base_scope(),
                    current_time="2026-11-02T08:00:00+08:00",
                    query_tags=["dorm"],
                    max_items=5,
                    max_tokens=500,
                )
                conn.commit()
            self.assertEqual(1, len(recalled))
            self.assertEqual(
                event["event_id"],
                recalled[0].memory.source_event_id,
            )

    def test_operation_replay_does_not_duplicate_logs_or_memory(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, _, _, _, before, after, action, event = committed_fixture(temporary)
            replay = repo.commit_step(
                state_before=before,
                state_after=after,
                event=event,
                action=action,
            )
            self.assertTrue(replay.replayed)
            self.assertEqual(1, len(repo.list_actions()))
            self.assertEqual(1, len(repo.list_events()))
            with connect(repo.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            self.assertEqual(1, count)

    def test_reusing_operation_with_different_content_conflicts(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, _, _, _, before, after, action, event = committed_fixture(temporary)
            changed = copy.deepcopy(action)
            changed["target_id"] = "loc_canteen"
            with self.assertRaises(StorageError) as caught:
                repo.commit_step(
                    state_before=before,
                    state_after=after,
                    event=event,
                    action=changed,
                )
            self.assertEqual("duplicate_operation", caught.exception.code)
            self.assertEqual(1, len(repo.list_actions()))

    def test_database_failure_rolls_back_event_and_action(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, loop, _, _, _, first_after, _, _ = committed_fixture(temporary)
            before = first_after
            second_before, second_after, second_action, second_event = run_agent_step(
                loop,
                "op_b4_rollback_002",
            )
            self.assertEqual(before["state_version"], second_before["state_version"])
            invalid_event = copy.deepcopy(second_event)
            invalid_event["sequence"] = second_event["sequence"] - 1
            with self.assertRaises(StorageError) as caught:
                repo.commit_step(
                    state_before=second_before,
                    state_after=second_after,
                    event=invalid_event,
                    action=second_action,
                )
            self.assertEqual("event_conflict", caught.exception.code)
            self.assertIsNone(repo.get_action("op_b4_rollback_002"))
            self.assertIsNone(repo.get_event(invalid_event["event_id"]))
            self.assertEqual(
                second_before["state_version"],
                repo.get_world_state()["state_version"],
            )

    def test_projection_failure_is_durable_and_reconcilable(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, _, _, result, _, _, _, event = committed_fixture(
                temporary,
                simulate_projection_failure=True,
            )
            self.assertEqual("reconciliation_required", result.status)
            self.assertIsNotNone(repo.get_event(event["event_id"]))
            pending = repo.list_projections("pending")
            self.assertEqual(1, len(pending))
            with connect(repo.db_path) as conn:
                before = repo.memory.recall(
                    conn,
                    scope=base_scope(),
                    current_time="2026-11-02T08:05:00+08:00",
                )
            self.assertEqual([], before)

            recovered = repo.reconcile(event["event_id"])
            self.assertEqual(1, recovered["projected"])
            self.assertEqual(0, recovered["failed_events"])
            self.assertEqual(1, len(repo.list_projections("projected")))
            with connect(repo.db_path) as conn:
                after = repo.memory.recall(
                    conn,
                    scope=base_scope(),
                    current_time="2026-11-02T08:10:00+08:00",
                )
            self.assertEqual(1, len(after))

    def test_npc_slots_are_separate_and_limited(self) -> None:
        with TemporaryDirectory() as temporary:
            repo, _, _, _, _, _, _, event = committed_fixture(temporary)
            slots = [
                {
                    "slot_id": f"npc_chen_slot_{index:02}",
                    "kind": "public_fact",
                    "content_key": f"fact_{index}",
                    "source_event_id": event["event_id"],
                    "important": index == 0,
                    "expires_on": "2026-11-09",
                    "last_used_at": "2026-11-02T08:00:00+08:00",
                }
                for index in range(8)
            ]
            repo.save_npc_slots(
                "npc_chen",
                slots,
                updated_at="2026-11-02T08:00:00+08:00",
            )
            self.assertEqual(8, len(repo.load_npc_slots("npc_chen")))
            self.assertEqual([], repo.load_npc_slots("npc_su"))
            with self.assertRaises(StorageError) as caught:
                repo.save_npc_slots(
                    "npc_chen",
                    [
                        *slots,
                        {
                            **slots[-1],
                            "slot_id": "npc_chen_slot_09",
                        },
                    ],
                    updated_at="2026-11-02T08:05:00+08:00",
                )
            self.assertEqual("npc_memory_full", caught.exception.code)


class MemoryCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        (
            self.repo,
            _,
            self.db_path,
            _,
            _,
            _,
            _,
            self.event,
        ) = committed_fixture(self.temporary.name)
        self.conn = connect(self.db_path)
        self.core = MemoryCore()

    def tearDown(self) -> None:
        self.conn.close()
        self.temporary.cleanup()

    def _append(
        self,
        scope: Scope,
        *,
        dedupe: str,
        strength: float,
        tags: list[str],
        created_at: str = "2026-11-02T08:00:00+08:00",
    ):
        return self.core.append(
            self.conn,
            scope=scope,
            dedupe_key=dedupe,
            kind="event",
            source="school_event",
            content=f"记忆 {dedupe}",
            source_event_id=self.event["event_id"],
            importance=0.6,
            emotional_weight=0.3,
            confidence=0.98,
            strength=strength,
            scene_tags=tags,
            created_at=created_at,
        )[0]

    def test_all_six_scope_dimensions_are_exact(self) -> None:
        base = base_scope()
        variants = [
            Scope(**{**base.to_dict(), "tenant_id": "other"}),
            Scope(**{**base.to_dict(), "world_id": "world_other_v1"}),
            Scope(**{**base.to_dict(), "user_id": "observer_other"}),
            Scope(**{**base.to_dict(), "character_id": "char_other"}),
            Scope(**{**base.to_dict(), "surface": "qq"}),
            Scope(**{**base.to_dict(), "conversation_id": "day-2026-11-03"}),
        ]
        for index, scope in enumerate(variants):
            self._append(
                scope,
                dedupe=f"scope-variant-{index}",
                strength=0.8,
                tags=["private"],
            )
        self.conn.commit()
        for index, scope in enumerate(variants):
            results = self.core.recall(
                self.conn,
                scope=base,
                current_time="2026-11-02T09:00:00+08:00",
            )
            self.assertTrue(
                all(result.memory.scope.key == base.key for result in results),
                index,
            )
            variant_results = self.core.recall(
                self.conn,
                scope=scope,
                current_time="2026-11-02T09:00:00+08:00",
            )
            self.assertEqual(1, len(variant_results))
            self.assertEqual(f"scope-variant-{index}", variant_results[0].memory.dedupe_key)
            self.conn.commit()

    def test_private_reflection_does_not_enter_npc_slots(self) -> None:
        private_scope = Scope(
            **{
                **base_scope().to_dict(),
                "conversation_id": None,
            }
        )
        memory = self._append(
            private_scope,
            dedupe="private-diary",
            strength=0.7,
            tags=["private", "diary"],
        )
        self.conn.commit()
        self.assertEqual("mem", memory.memory_id[:3])
        self.assertEqual([], self.repo.load_npc_slots("npc_chen"))
        results = self.core.recall(
            self.conn,
            scope=base_scope(),
            current_time="2026-11-02T09:00:00+08:00",
        )
        self.assertNotIn(memory.memory_id, {item.memory.memory_id for item in results})

    def test_lifecycle_thresholds_are_stable(self) -> None:
        self.assertEqual("active", lifecycle_state(0.3))
        self.assertEqual("fuzzy", lifecycle_state(0.299999))
        self.assertEqual("fuzzy", lifecycle_state(0.1))
        self.assertEqual("archived", lifecycle_state(0.099999))

    def test_decay_and_lock_semantics(self) -> None:
        scope = Scope(**{**base_scope().to_dict(), "conversation_id": None})
        memory = self._append(
            scope,
            dedupe="decay",
            strength=0.8,
            tags=["library"],
            created_at="2026-01-01T00:00:00+08:00",
        )
        self.conn.execute(
            """
            UPDATE memories SET last_strength_update = ?
            WHERE memory_id = ?
            """,
            ("2026-01-01T00:00:00+08:00", memory.memory_id),
        )
        locked = self.core.set_locked(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            locked=True,
            current_time="2026-01-15T00:00:00+08:00",
        )
        self.core.decay(
            self.conn,
            scope=scope,
            current_time="2026-04-15T00:00:00+08:00",
        )
        still_locked = self.core.get(self.conn, memory.memory_id, scope)
        self.assertTrue(still_locked.locked)
        self.assertEqual(locked.strength, still_locked.strength)
        self.assertEqual("active", still_locked.state)

        self.core.set_locked(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            locked=False,
            current_time="2026-04-15T00:00:00+08:00",
        )
        self.core.decay(
            self.conn,
            scope=scope,
            current_time="2026-04-29T00:00:00+08:00",
        )
        halved = self.core.get(self.conn, memory.memory_id, scope)
        self.assertAlmostEqual(0.4, halved.strength, places=6)
        self.assertEqual("active", halved.state)

    def test_fuzzy_is_recalled_but_archived_is_not(self) -> None:
        scope = base_scope()
        fuzzy = self._append(scope, dedupe="fuzzy", strength=0.2, tags=["library"])
        archived = self._append(
            scope,
            dedupe="archived",
            strength=0.05,
            tags=["library"],
        )
        self.conn.commit()
        results = self.core.recall(
            self.conn,
            scope=scope,
            current_time="2026-11-02T08:00:00+08:00",
            query_tags=["library"],
            max_items=10,
            max_tokens=1_000,
        )
        ids = {result.memory.memory_id for result in results}
        self.assertIn(fuzzy.memory_id, ids)
        self.assertNotIn(archived.memory_id, ids)
        self.assertIn("state_fuzzy", next(
            item.reason_codes for item in results
            if item.memory.memory_id == fuzzy.memory_id
        ))

    def test_recall_budget_and_score_explanation(self) -> None:
        scope = base_scope()
        for index in range(4):
            self._append(
                scope,
                dedupe=f"rank-{index}",
                strength=0.5 + index * 0.1,
                tags=["library", f"tag-{index}"],
            )
        self.conn.commit()
        results = self.core.recall(
            self.conn,
            scope=scope,
            current_time="2026-11-02T08:00:00+08:00",
            query_tags=["library"],
            max_items=2,
            max_tokens=100,
        )
        self.assertLessEqual(len(results), 2)
        for result in results:
            self.assertAlmostEqual(result.score, sum(result.score_breakdown.values()))
            self.assertIn("scope_exact", result.reason_codes)

    def test_strengthen_is_operation_idempotent(self) -> None:
        scope = base_scope()
        memory = self._append(
            scope,
            dedupe="strengthen",
            strength=0.4,
            tags=["deadline"],
        )
        self.conn.commit()
        first, replayed = self.core.strengthen(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            operation_id="op_strengthen_001",
            amount=0.1,
            reason="share",
            source_event_id=self.event["event_id"],
            current_time="2026-11-02T09:00:00+08:00",
        )
        second, replayed_again = self.core.strengthen(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            operation_id="op_strengthen_001",
            amount=0.1,
            reason="share",
            source_event_id=self.event["event_id"],
            current_time="2026-11-02T09:00:00+08:00",
        )
        self.assertFalse(replayed)
        self.assertTrue(replayed_again)
        self.assertEqual(first.strength, second.strength)
        self.assertEqual(1, second.restated_count)
        with self.assertRaises(ConflictError):
            self.core.strengthen(
                self.conn,
                memory_id=memory.memory_id,
                scope=scope,
                operation_id="op_strengthen_001",
                amount=0.2,
                reason="share",
                source_event_id=self.event["event_id"],
                current_time="2026-11-02T09:00:00+08:00",
            )

    def test_strengthening_archived_memory_reactivates_it(self) -> None:
        scope = base_scope()
        memory = self._append(
            scope,
            dedupe="reactivate",
            strength=0.05,
            tags=["library"],
        )
        self.conn.commit()
        self.assertEqual("archived", self.core.get(
            self.conn, memory.memory_id, scope
        ).state)
        first, _ = self.core.strengthen(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            operation_id="op_reactivate_001",
            amount=0.2,
            reason="scene_trigger",
            source_event_id=self.event["event_id"],
            current_time="2026-11-02T09:00:00+08:00",
        )
        second, _ = self.core.strengthen(
            self.conn,
            memory_id=memory.memory_id,
            scope=scope,
            operation_id="op_reactivate_002",
            amount=0.2,
            reason="share",
            source_event_id=self.event["event_id"],
            current_time="2026-11-02T09:10:00+08:00",
        )
        self.assertEqual("fuzzy", first.state)
        self.assertEqual("active", second.state)
        self.assertAlmostEqual(0.45, second.strength)

    def test_conflicting_dedupe_key_and_missing_source_are_rejected(self) -> None:
        scope = base_scope()
        self._append(scope, dedupe="same-key", strength=0.4, tags=["library"])
        self.conn.commit()
        with self.assertRaises(ConflictError):
            self.core.append(
                self.conn,
                scope=scope,
                dedupe_key="same-key",
                kind="event",
                source="school_event",
                content="不同内容",
                source_event_id=self.event["event_id"],
                importance=0.4,
                emotional_weight=0.2,
                confidence=0.9,
                strength=0.4,
                scene_tags=["library"],
                created_at="2026-11-02T08:00:00+08:00",
            )
        with self.assertRaises(ValidationError):
            self.core.append(
                self.conn,
                scope=scope,
                dedupe_key="missing-source",
                kind="event",
                source="school_event",
                content="无来源",
                source_event_id="missing",
                importance=0.4,
                emotional_weight=0.2,
                confidence=0.9,
                strength=0.4,
                scene_tags=[],
                created_at="2026-11-02T08:00:00+08:00",
            )


if __name__ == "__main__":
    unittest.main()
