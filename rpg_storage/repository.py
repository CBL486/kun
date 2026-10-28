"""世界、事件、动作和记忆投影的事务仓库。"""

from __future__ import annotations

import copy
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory_core import MemoryCore, Scope
from rpg_sim.ids import canonical_json, stable_id

from .errors import StorageError
from .migrations import connect, migrate


@dataclass
class CommitResult:
    event_id: str
    operation_id: str
    replayed: bool
    memory_ids: list[str]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "operation_id": self.operation_id,
            "replayed": self.replayed,
            "memory_ids": self.memory_ids,
            "status": self.status,
        }


class WorldRepository:
    def __init__(
        self,
        db_path: str | Path,
        *,
        user_id: str = "observer_demo_001",
    ):
        self.db_path = Path(db_path).resolve()
        self.user_id = user_id
        migrate(self.db_path)
        self.memory = MemoryCore()

    def initialize_world(self, state: dict[str, Any]) -> None:
        with connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT state_version, state_json FROM world_heads WHERE world_id = ?",
                (state["world_id"],),
            ).fetchone()
            if existing:
                if json.loads(existing["state_json"]) != state:
                    raise StorageError("world_conflict", "初始世界状态与已有状态不一致")
                return
            conn.execute(
                """
                INSERT INTO world_heads (
                    world_id, state_version, logical_time, state_json, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    state["world_id"],
                    state["state_version"],
                    state["logical_time"],
                    canonical_json(state),
                    state["logical_time"],
                ),
            )
            conn.execute(
                """
                INSERT INTO world_versions (
                    world_id, state_version, logical_time, state_json,
                    event_id, created_at
                ) VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (
                    state["world_id"],
                    state["state_version"],
                    state["logical_time"],
                    canonical_json(state),
                    state["logical_time"],
                ),
            )

    def commit_step(
        self,
        *,
        state_before: dict[str, Any],
        state_after: dict[str, Any],
        event: dict[str, Any],
        action: dict[str, Any],
        simulate_projection_failure: bool = False,
    ) -> CommitResult:
        self._validate_step(state_before, state_after, event, action)
        operation_id = action["operation_id"]
        fingerprint = canonical_json(action)
        existing = self.get_action(operation_id)
        if existing:
            if existing["fingerprint"] != fingerprint:
                raise StorageError("duplicate_operation", "operation 内容不一致")
            memory_ids, status = self._project_event(existing["event_id"])
            return CommitResult(
                event_id=existing["event_id"],
                operation_id=operation_id,
                replayed=True,
                memory_ids=memory_ids,
                status=status,
            )

        projections = self._build_projections(
            event=event,
            action=action,
        )
        try:
            with connect(self.db_path) as conn:
                head = conn.execute(
                    "SELECT * FROM world_heads WHERE world_id = ?",
                    (state_after["world_id"],),
                ).fetchone()
                if not head:
                    raise StorageError("unknown_reference", "世界尚未初始化")
                if head["state_version"] != state_before["state_version"]:
                    raise StorageError("stale_state", "数据库世界版本已过期")
                if head["state_json"] != canonical_json(state_before):
                    raise StorageError("stale_state", "数据库世界快照已过期")
                conn.execute(
                    """
                    INSERT INTO actions (
                        operation_id, action_id, world_id, character_id,
                        action_type, tick_id, fingerprint, status, event_id,
                        payload_json, committed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?, ?, ?)
                    """,
                    (
                        operation_id,
                        action["action_id"],
                        action["world_id"],
                        action["character_id"],
                        action["action_type"],
                        action["tick_id"],
                        fingerprint,
                        event["event_id"],
                        canonical_json(action),
                        event["committed_at"],
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, world_id, world_date, sequence, slot_key,
                        occurred_at, event_type, summary, visibility, tick_id,
                        action_id, event_json, committed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["event_id"],
                        event["world_id"],
                        event["world_date"],
                        event["sequence"],
                        event["slot_key"],
                        event["occurred_at"],
                        event["event_type"],
                        event["summary"],
                        event["visibility"],
                        event["tick_id"],
                        event["action_id"],
                        canonical_json(event),
                        event["committed_at"],
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO world_versions (
                        world_id, state_version, logical_time, state_json,
                        event_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state_after["world_id"],
                        state_after["state_version"],
                        state_after["logical_time"],
                        canonical_json(state_after),
                        event["event_id"],
                        event["committed_at"],
                    ),
                )
                conn.execute(
                    """
                    UPDATE world_heads
                    SET state_version = ?, logical_time = ?, state_json = ?,
                        updated_at = ?
                    WHERE world_id = ?
                    """,
                    (
                        state_after["state_version"],
                        state_after["logical_time"],
                        canonical_json(state_after),
                        event["committed_at"],
                        state_after["world_id"],
                    ),
                )
                for projection in projections:
                    conn.execute(
                        """
                        INSERT INTO memory_projection_outbox (
                            projection_id, event_id, candidate_index,
                            character_id, dedupe_key, payload_json, status,
                            attempts, last_error, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, NULL, ?, ?)
                        """,
                        (
                            projection["projection_id"],
                            event["event_id"],
                            projection["candidate_index"],
                            projection["character_id"],
                            projection["dedupe_key"],
                            canonical_json(projection),
                            event["committed_at"],
                            event["committed_at"],
                        ),
                    )
            result = self._project_event(
                event["event_id"],
                simulate_failure=simulate_projection_failure,
            )
            return CommitResult(
                event_id=event["event_id"],
                operation_id=operation_id,
                replayed=False,
                memory_ids=result[0],
                status=result[1],
            )
        except sqlite3.IntegrityError as error:
            raise StorageError("event_conflict", "事务唯一约束失败，已整体回滚") from error
        except sqlite3.DatabaseError as error:
            raise StorageError("backend_unavailable", "SQLite 事务失败，已整体回滚") from error

    def reconcile(self, event_id: str | None = None) -> dict[str, int]:
        event_ids = [event_id] if event_id else [
            row["event_id"]
            for row in self._query(
                """
                SELECT DISTINCT event_id
                FROM memory_projection_outbox
                WHERE status != 'projected'
                ORDER BY event_id
                """
            )
        ]
        projected = 0
        failed = 0
        for current_event_id in event_ids:
            memory_ids, status = self._project_event(current_event_id)
            if status == "projected":
                projected += len(memory_ids)
            else:
                failed += 1
        return {"projected": projected, "failed_events": failed}

    def get_world_state(self) -> dict[str, Any]:
        rows = self._query("SELECT state_json FROM world_heads LIMIT 1")
        if not rows:
            raise StorageError("unknown_reference", "世界尚未初始化")
        return json.loads(rows[0]["state_json"])

    def get_action(self, operation_id: str) -> dict[str, Any] | None:
        rows = self._query(
            "SELECT * FROM actions WHERE operation_id = ?",
            (operation_id,),
        )
        return dict(rows[0]) if rows else None

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        rows = self._query(
            "SELECT * FROM events WHERE event_id = ?",
            (event_id,),
        )
        return dict(rows[0]) if rows else None

    def list_events(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._query(
                "SELECT * FROM events ORDER BY world_date, sequence, event_id"
            )
        ]

    def list_actions(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._query(
                "SELECT * FROM actions ORDER BY committed_at, operation_id"
            )
        ]

    def list_projections(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            rows = self._query(
                "SELECT * FROM memory_projection_outbox WHERE status = ? ORDER BY event_id, candidate_index",
                (status,),
            )
        else:
            rows = self._query(
                "SELECT * FROM memory_projection_outbox ORDER BY event_id, candidate_index"
            )
        return [dict(row) for row in rows]

    def save_npc_slots(
        self,
        npc_id: str,
        slots: list[dict[str, Any]],
        *,
        updated_at: str,
    ) -> None:
        if len(slots) > 8:
            raise StorageError("npc_memory_full", "NPC 记忆槽不能超过 8 条")
        if len({slot["slot_id"] for slot in slots}) != len(slots):
            raise StorageError("duplicate_slot", "NPC 记忆槽 ID 重复")
        with connect(self.db_path) as conn:
            conn.execute("DELETE FROM npc_memory_slots WHERE npc_id = ?", (npc_id,))
            for slot in slots:
                conn.execute(
                    """
                    INSERT INTO npc_memory_slots (
                        npc_id, slot_id, kind, content_key, source_event_id,
                        important, expires_on, last_used_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        npc_id,
                        slot["slot_id"],
                        slot["kind"],
                        slot["content_key"],
                        slot.get("source_event_id"),
                        int(bool(slot.get("important", False))),
                        slot.get("expires_on"),
                        slot.get("last_used_at"),
                        updated_at,
                    ),
                )

    def load_npc_slots(self, npc_id: str) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._query(
                """
                SELECT * FROM npc_memory_slots
                WHERE npc_id = ?
                ORDER BY important DESC, slot_id
                """,
                (npc_id,),
            )
        ]

    def _validate_step(
        self,
        state_before: dict[str, Any],
        state_after: dict[str, Any],
        event: dict[str, Any],
        action: dict[str, Any],
    ) -> None:
        if event["world_id"] != action["world_id"]:
            raise StorageError("scope_mismatch", "事件和动作 world_id 不一致")
        if event["action_id"] != action["action_id"]:
            raise StorageError("event_conflict", "事件 action_id 不一致")
        if state_before["state_version"] + 1 != state_after["state_version"]:
            raise StorageError("stale_state", "状态版本不是单步递增")
        if (
            event["state_version_before"] != state_before["state_version"]
            or event["state_version_after"] != state_after["state_version"]
        ):
            raise StorageError("stale_state", "事件状态版本不一致")
        if state_after.get("events") and state_before.get("events") is not None:
            if state_after["events"][-1]["event_id"] != event["event_id"]:
                raise StorageError("event_conflict", "快照末尾不是待提交事件")

    def _build_projections(
        self,
        *,
        event: dict[str, Any],
        action: dict[str, Any],
    ) -> list[dict[str, Any]]:
        projections = []
        for index, candidate in enumerate(event.get("memory_candidates", [])):
            conversation_id = (
                None
                if event["event_type"] == "journal_written"
                else f"day-{event['world_date']}"
            )
            scope = Scope(
                tenant_id="rpg-world",
                world_id=event["world_id"],
                user_id=self.user_id,
                character_id=action["character_id"],
                surface="school",
                conversation_id=conversation_id,
            )
            dedupe_key = (
                f"rpg:{event['event_id']}:{action['character_id']}:{index}"
            )
            projections.append(
                {
                    "projection_id": stable_id(
                        "proj",
                        [event["event_id"], index, action["character_id"]],
                    ),
                    "candidate_index": index,
                    "character_id": action["character_id"],
                    "dedupe_key": dedupe_key,
                    "scope": scope.to_dict(),
                    "kind": candidate["kind"],
                    "source": candidate["source"],
                    "content": candidate["summary"],
                    "source_event_id": event["event_id"],
                    "importance": candidate["importance"],
                    "emotional_weight": candidate["emotional_weight"],
                    "confidence": 0.98,
                    "strength": round(
                        0.45 + candidate["importance"] * 0.35,
                        4,
                    ),
                    "scene_tags": candidate["scene_tags"],
                    "created_at": event["committed_at"],
                    "metadata": {
                        "visibility": event["visibility"],
                        "template_id": event["template_id"],
                    },
                }
            )
        return projections

    def _project_event(
        self,
        event_id: str,
        *,
        simulate_failure: bool = False,
    ) -> tuple[list[str], str]:
        rows = self._query(
            """
            SELECT * FROM memory_projection_outbox
            WHERE event_id = ? AND status != 'projected'
            ORDER BY candidate_index
            """,
            (event_id,),
        )
        if not rows:
            existing = self._query(
                """
                SELECT m.memory_id
                FROM memory_projection_outbox o
                JOIN memories m
                  ON m.source_event_id = o.event_id
                 AND m.dedupe_key = o.dedupe_key
                WHERE o.event_id = ?
                ORDER BY o.candidate_index
                """,
                (event_id,),
            )
            return [row["memory_id"] for row in existing], "projected"
        if simulate_failure:
            now = rows[0]["updated_at"]
            for row in rows:
                self._execute(
                    """
                    UPDATE memory_projection_outbox
                    SET attempts = attempts + 1,
                        last_error = 'simulated_projection_failure',
                        updated_at = ?
                    WHERE projection_id = ?
                    """,
                    (now, row["projection_id"]),
                )
            return [], "reconciliation_required"

        memory_ids = []
        try:
            with connect(self.db_path) as conn:
                for row in rows:
                    payload = json.loads(row["payload_json"])
                    scope = Scope.from_dict(payload["scope"])
                    memory, _ = self.memory.append(
                        conn,
                        scope=scope,
                        dedupe_key=payload["dedupe_key"],
                        kind=payload["kind"],
                        source=payload["source"],
                        content=payload["content"],
                        source_event_id=payload["source_event_id"],
                        importance=payload["importance"],
                        emotional_weight=payload["emotional_weight"],
                        confidence=payload["confidence"],
                        strength=payload["strength"],
                        scene_tags=payload["scene_tags"],
                        created_at=payload["created_at"],
                        metadata=payload["metadata"],
                    )
                    memory_ids.append(memory.memory_id)
                    conn.execute(
                        """
                        UPDATE memory_projection_outbox
                        SET status = 'projected', attempts = attempts + 1,
                            last_error = NULL, updated_at = ?
                        WHERE projection_id = ?
                        """,
                        (payload["created_at"], row["projection_id"]),
                    )
            return memory_ids, "projected"
        except Exception as error:
            for row in rows:
                self._execute(
                    """
                    UPDATE memory_projection_outbox
                    SET status = 'failed', attempts = attempts + 1,
                        last_error = ?, updated_at = datetime('now')
                    WHERE projection_id = ?
                    """,
                    (type(error).__name__, row["projection_id"]),
                )
            return [], "reconciliation_required"

    def _query(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[sqlite3.Row]:
        with connect(self.db_path) as conn:
            return list(conn.execute(sql, params).fetchall())

    def _execute(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> None:
        with connect(self.db_path) as conn:
            conn.execute(sql, params)
