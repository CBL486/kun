from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from rpg_sim.engine import WorldEngine
from rpg_sim.ids import digest, stable_id
from rpg_sim.mocks import MockLLM, MockReviewer
from rpg_sim.scenario import (
    ACTIONS,
    CRITICAL_TEMPLATES,
    DAILY_ROUTES,
    DIRECTOR_TEMPLATES,
    initial_world,
)
from rpg_sim.simulator import SevenDaySimulator


class SevenDaySimulatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = SevenDaySimulator().run()
        cls.report = cls.result.report

    def test_required_report_fields_exist(self) -> None:
        required = {
            "scenario_id",
            "seed",
            "start_time",
            "end_time",
            "clock_mode",
            "code_version",
            "template_registry_version",
            "world_snapshot_before",
            "ordered_events",
            "action_attempts",
            "typed_rejections",
            "director_candidates",
            "director_rejected_candidates",
            "npc_reaction_records",
            "memory_read_explanations",
            "memory_write_records",
            "relationship_changes",
            "daily_shares",
            "diary_records",
            "observer_visible_projection",
            "budget_ledger",
            "degradation_events",
            "world_snapshot_after",
            "replay_hashes",
            "known_limitations",
        }
        self.assertEqual(required - set(self.report), set())

    def test_same_seed_produces_same_business_snapshot(self) -> None:
        second = SevenDaySimulator().run()
        self.assertEqual(
            self.report["replay_hashes"],
            second.report["replay_hashes"],
        )
        self.assertEqual(
            digest(self.result.snapshot_after),
            digest(second.snapshot_after),
        )

    def test_pause_restart_and_resume_preserve_business_result(self) -> None:
        with TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "checkpoint.json"
            paused = SevenDaySimulator(
                checkpoint_path=checkpoint,
                pause_after_steps=17,
            ).run()
            self.assertFalse(paused.complete)
            self.assertEqual("paused", paused.report["status"])
            self.assertTrue(checkpoint.is_file())

            paused_again = SevenDaySimulator.from_checkpoint(
                checkpoint,
                pause_after_steps=9,
            ).run()
            self.assertFalse(paused_again.complete)

            resumed = SevenDaySimulator.from_checkpoint(checkpoint).run()
            self.assertTrue(resumed.complete)
            self.assertEqual(
                self.report["replay_hashes"]["business_result"],
                resumed.report["replay_hashes"]["business_result"],
            )
            self.assertEqual(
                len(self.report["ordered_events"]),
                len(resumed.report["ordered_events"]),
            )
            self.assertEqual(
                len(self.report["action_attempts"]),
                len(resumed.report["action_attempts"]),
            )

    def test_mock_llm_and_reviewer_are_deterministic_and_offline(self) -> None:
        first = MockLLM(20261028).complete(
            "daily_share",
            {"summaries": ["公开事件一", "公开事件二", "公开事件三"]},
        )
        second = MockLLM(20261028).complete(
            "daily_share",
            {"summaries": ["公开事件一", "公开事件二", "公开事件三"]},
        )
        self.assertEqual(first, second)
        self.assertEqual("mock", first.provider)
        self.assertEqual("approved", MockReviewer().review(first.text))

    def test_all_critical_templates_appear(self) -> None:
        seen = {event["template_id"] for event in self.report["ordered_events"]}
        self.assertEqual(CRITICAL_TEMPLATES, seen & CRITICAL_TEMPLATES)
        self.assertEqual(9, len(CRITICAL_TEMPLATES))

    def test_nine_actions_are_used_and_registered(self) -> None:
        used = {item["action_type"] for item in self.report["action_attempts"]}
        self.assertEqual(set(ACTIONS), used)
        self.assertEqual(9, len(ACTIONS))

    def test_daily_budgets_and_fixed_counts(self) -> None:
        daily = self.report["budget_ledger"]["daily"]
        self.assertEqual(set(DAILY_ROUTES), set(daily))
        for world_date, ledger in daily.items():
            self.assertLessEqual(ledger["world_events"], 6, world_date)
            self.assertLessEqual(ledger["shares"], 1, world_date)
            self.assertLessEqual(ledger["journals"], 1, world_date)
            self.assertLessEqual(ledger["model_calls"], 8, world_date)
            self.assertLessEqual(ledger["input_tokens"], 24_000, world_date)
            self.assertLessEqual(ledger["output_tokens"], 6_000, world_date)
            self.assertLessEqual(float(ledger["cost_cny"]), 0.10, world_date)
        self.assertEqual(12, len(DIRECTOR_TEMPLATES))
        self.assertEqual(41, self.report["budget_ledger"]["totals"]["world_events"])

    def test_every_event_and_state_change_is_traceable(self) -> None:
        dates = set(DAILY_ROUTES)
        by_day = Counter(event["world_date"] for event in self.report["ordered_events"])
        self.assertTrue(by_day.keys() <= dates)
        previous = 0
        for event in self.report["ordered_events"]:
            self.assertTrue(event["event_id"].startswith("evt_"))
            self.assertTrue(event["action_id"].startswith("act_"))
            self.assertEqual(
                event["state_version_before"] + 1,
                event["state_version_after"],
            )
            self.assertGreater(event["state_version_after"], previous)
            previous = event["state_version_after"]
            for change in event["state_changes"]:
                self.assertIn("path", change)
                self.assertIn("before", change)
                self.assertIn("after", change)
            for change in event["relationship_changes"]:
                self.assertEqual(event["event_id"], change["event_id"])
                self.assertLessEqual(abs(change["delta"]), 0.08)

    def test_every_daily_share_has_three_layers_and_sources(self) -> None:
        event_ids = {event["event_id"] for event in self.report["ordered_events"]}
        self.assertEqual(7, len(self.report["daily_shares"]))
        for share in self.report["daily_shares"]:
            self.assertEqual({"event", "feeling", "reflection"}, set(share["layers"]))
            self.assertGreaterEqual(len(share["source_event_ids"]), 3)
            self.assertLessEqual(len(share["source_event_ids"]), 5)
            self.assertTrue(set(share["source_event_ids"]) <= event_ids)

    def test_private_journal_is_not_in_observer_projection(self) -> None:
        observer_text = str(self.report["observer_visible_projection"])
        self.assertEqual(2, len(self.report["diary_records"]))
        self.assertTrue(self.report["observer_visible_projection"]["diary_available"])
        for diary in self.report["diary_records"]:
            self.assertEqual("internal", diary["visibility"])
            self.assertNotIn(diary["summary"], observer_text)

    def test_npc_boundary_and_reaction_dedupe(self) -> None:
        menu_events = [
            event
            for event in self.report["ordered_events"]
            if event["template_id"] == "dirtpl_canteen_menu_change_v1"
        ]
        self.assertEqual(1, len(menu_events))
        self.assertEqual(["fact_canteen_public_menu"], menu_events[0]["knowledge_basis"])
        pairs = [
            (record["npc_id"], record["response_to_event_id"])
            for record in self.report["npc_reaction_records"]
        ]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertLessEqual(
            max(Counter(event_id for _, event_id in pairs).values()),
            2,
        )

    def test_director_candidates_are_registered_and_cannot_write_state(self) -> None:
        candidates = self.report["director_candidates"]
        self.assertEqual(12, len(candidates))
        for candidate in candidates:
            self.assertIn(candidate["template_id"], DIRECTOR_TEMPLATES)
            self.assertIsNone(candidate["state_write"])
            self.assertEqual("approved", candidate["review_status"])

    def test_sunday_recalls_earlier_week_events(self) -> None:
        recalls = self.report["memory_read_explanations"]
        self.assertGreaterEqual(len(recalls), 3)
        self.assertEqual(3, len(recalls))
        event_dates = {
            event["event_id"]: event["world_date"]
            for event in self.report["ordered_events"]
        }
        self.assertEqual(
            {"2026-11-02", "2026-11-04", "2026-11-06"},
            {event_dates[item["source_event_id"]] for item in recalls},
        )


class WorldEngineRejectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = WorldEngine(initial_world())
        self.engine.prepare_time("2026-11-02", "08:00", "morning_1")

    def _intent(self, **overrides):
        tick_id = stable_id("tick", ["world", "char", "date", "slot", "epoch"])
        action_id = stable_id("act", [tick_id, 0, "nonce"])
        intent = {
            "action_id": action_id,
            "operation_id": "op_test_001",
            "tick_id": tick_id,
            "world_id": "world_qinghe_v1",
            "character_id": "char_lin_cheng",
            "action_type": "move",
            "target_id": "loc_classroom",
            "parameters": {},
            "expected_state_version": self.engine.state["state_version"],
            "origin": "test",
            "intent_nonce": "nonce",
        }
        intent.update(overrides)
        return intent

    def test_unknown_action_is_rejected_without_state_change(self) -> None:
        before = digest(self.engine.snapshot())
        result = self.engine.apply(self._intent(action_type="teleport"))
        self.assertFalse(result["ok"])
        self.assertEqual("unsupported_action", result["code"])
        self.assertEqual(before, digest(self.engine.snapshot()))

    def test_stale_state_is_rejected(self) -> None:
        result = self.engine.apply(self._intent(expected_state_version=99))
        self.assertFalse(result["ok"])
        self.assertEqual("stale_state", result["code"])
        self.assertEqual(0, self.engine.state["state_version"])

    def test_replay_returns_original_event_without_duplicate(self) -> None:
        intent = self._intent()
        first = self.engine.apply(intent)
        second = self.engine.apply(intent)
        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertTrue(second["replayed"])
        self.assertEqual(first["event"]["event_id"], second["event"]["event_id"])
        self.assertEqual(1, len(self.engine.state["events"]))
        self.assertEqual(1, self.engine.state["state_version"])

    def test_operation_reuse_with_different_content_conflicts(self) -> None:
        first = self.engine.apply(self._intent())
        self.assertTrue(first["ok"])
        second = self.engine.apply(
            self._intent(target_id="loc_library", intent_nonce="different")
        )
        self.assertFalse(second["ok"])
        self.assertEqual("duplicate_operation", second["code"])


if __name__ == "__main__":
    unittest.main()
