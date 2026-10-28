from __future__ import annotations

import json
import unittest

from rpg_agent.loop import AgentLoop
from rpg_agent.models import Candidate, IntentValidationError
from rpg_agent.perception import Perception
from rpg_agent.planner import RulePlanner
from rpg_sim.engine import WorldEngine
from rpg_sim.ids import digest
from rpg_sim.scenario import initial_world


def new_loop() -> AgentLoop:
    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare("2026-11-02", "08:00", "morning_1")
    return loop


class AgentCoreTests(unittest.TestCase):
    def test_intent_does_not_mutate_world(self) -> None:
        loop = new_loop()
        before = digest(loop.engine.snapshot())
        perception = loop.perceive()
        trace = loop.plan(perception)
        proposal = loop.propose("op_no_mutation", trace)
        intent = loop.materialize(proposal)
        self.assertEqual(before, digest(loop.engine.snapshot()))
        self.assertEqual("rpg-action-intent-v1", intent.schema_version)
        self.assertEqual(loop.engine.state["state_version"], intent.expected_state_version)

    def test_same_state_and_seed_produce_same_decision(self) -> None:
        first = new_loop()
        second = new_loop()
        first_result = first.run_once("op_deterministic")
        second_result = second.run_once("op_deterministic")
        self.assertEqual(
            first_result.trace.to_dict(),
            second_result.trace.to_dict(),
        )
        self.assertEqual(
            first_result.intent.to_dict(),
            second_result.intent.to_dict(),
        )
        self.assertEqual(
            first_result.world_result["event"]["event_id"],
            second_result.world_result["event"]["event_id"],
        )

    def test_perception_contains_only_safe_projection(self) -> None:
        loop = new_loop()
        perception = loop.perceive().to_dict()
        forbidden = {"state_changes", "prompt", "action_score", "memory_slots"}
        self.assertFalse(forbidden & set(perception))
        self.assertEqual("loc_dorm", perception["location"]["location_id"])
        self.assertIn("constraints", perception)

    def test_candidate_filter_rejects_illegal_actions(self) -> None:
        loop = new_loop()
        perception = loop.perceive()
        unsupported = Candidate(
            candidate_id="cand_bad_action",
            action_type="teleport",
            target_id="loc_river",
            parameters={},
            score=2.0,
            reason_codes=["invalid"],
        )
        remote_npc = Candidate(
            candidate_id="cand_remote_npc",
            action_type="talk",
            target_id="npc_gao",
            parameters={"topic": "menu", "max_turns": 2},
            score=0.9,
            reason_codes=["invalid"],
        )
        accepted, rejected = loop.planner.filter_candidates(
            loop.engine.state,
            perception,
            [unsupported, remote_npc],
        )
        self.assertEqual([], accepted)
        self.assertEqual(
            {"unsupported_action", "npc_not_present"},
            {item["code"] for item in rejected},
        )

    def test_decision_trace_has_scores_and_reasons(self) -> None:
        loop = new_loop()
        result = loop.run_once("op_trace")
        trace = result.trace.to_dict()
        self.assertTrue(trace["candidates"])
        self.assertEqual(
            result.proposal.target_id,
            next(
                item["target_id"]
                for item in trace["candidates"]
                if item["candidate_id"] == trace["selected_candidate_id"]
            ),
        )
        self.assertTrue(trace["candidates"][0]["reason_codes"])
        self.assertFalse(trace["model_used"])

    def test_relationship_changes_are_event_bound(self) -> None:
        loop = AgentLoop(WorldEngine(initial_world()))
        loop.prepare("2026-11-03", "12:15", "noon")
        state = loop.engine.state
        state["characters"]["char_lin_cheng"]["location_id"] = "loc_canteen"
        state["npcs"]["npc_gao"]["location_id"] = "loc_canteen"
        state["npcs"]["npc_gao"]["runtime_state"] = "available"
        perception = loop.perceive()
        candidates = [
            Candidate(
                candidate_id="cand_talk_gao",
                action_type="talk",
                target_id="npc_gao",
                parameters={"topic": "menu", "max_turns": 2},
                score=0.95,
                reason_codes=["public_menu"],
            )
        ]
        selected = candidates[0]
        proposal = loop.propose(
            "op_relationship",
            loop.planner.plan(state, perception),
        )
        # 强制选择测试候选，验证关系变化仍由世界引擎绑定事件 ID。
        intent = loop.materialize(
            type(proposal).from_candidate(
                candidate=selected,
                operation_id="op_relationship_targeted",
                tick_id=perception.tick_id,
                character_id="char_lin_cheng",
            )
        )
        result = loop.execute(intent)
        self.assertTrue(result["ok"])
        event = result["event"]
        self.assertEqual("conversation_completed", event["event_type"])
        self.assertTrue(event["relationship_changes"])
        for change in event["relationship_changes"]:
            self.assertEqual(event["event_id"], change["event_id"])
        relationship_id = event["relationship_changes"][0]["relationship_id"]
        familiarity = loop.engine.state["relationships"][relationship_id][
            "familiarity"
        ]
        replay = loop.execute(intent)
        self.assertTrue(replay["replayed"])
        self.assertEqual(event["event_id"], replay["event"]["event_id"])
        self.assertEqual(
            familiarity,
            loop.engine.state["relationships"][relationship_id]["familiarity"],
        )
        self.assertEqual(1, len(loop.engine.state["events"]))

    def test_intent_fields_cannot_write_world(self) -> None:
        proposal = new_loop().propose(
            "op_invalid_fields",
            new_loop().plan(),
        )
        payload = proposal.to_dict()
        payload["state_changes"] = [{"path": "world.sequence", "value": 99}]
        from rpg_agent.models import IntentProposal

        with self.assertRaises(IntentValidationError):
            IntentProposal.from_dict(payload)

    def test_replay_returns_same_event_without_relationship_duplicate(self) -> None:
        loop = new_loop()
        first = loop.run_once("op_replay")
        second = loop.run_once("op_replay")
        self.assertTrue(first.world_result["ok"])
        self.assertTrue(second.world_result["replayed"])
        self.assertEqual(
            first.world_result["event"]["event_id"],
            second.world_result["event"]["event_id"],
        )
        self.assertEqual(1, len(loop.engine.state["events"]))
        self.assertEqual(1, loop.engine.state["state_version"])

    def test_model_format_error_degrades_to_rule_mode(self) -> None:
        loop = new_loop()
        result = loop.run_once("op_degraded", simulate_model_error=True)
        self.assertEqual("DEGRADED", result.status)
        self.assertTrue(result.world_result["ok"])
        self.assertIn("model_format_error", result.trace.degradation_reason)
        self.assertFalse(result.trace.model_used)

    def test_stale_state_can_be_recovered_with_same_operation(self) -> None:
        loop = new_loop()
        trace = loop.plan()
        proposal = loop.propose("op_stale_recovery", trace)
        stale_intent = loop.materialize(proposal)

        # 模拟另一个协作者先提交状态变化。
        other = loop.run_once("op_other_commit")
        self.assertTrue(other.world_result["ok"])
        stale_result = loop.execute(stale_intent)
        self.assertEqual("stale_state", stale_result["code"])

        recovered = loop.recover_after_stale("op_stale_recovery")
        self.assertEqual("COMMITTED", recovered.status)
        self.assertTrue(recovered.world_result["ok"])
        self.assertEqual(
            2,
            loop.engine.state["state_version"],
        )

    def test_no_action_intent_has_only_registered_fields(self) -> None:
        loop = new_loop()
        result = loop.run_once("op_structured")
        intent = result.intent.to_dict()
        self.assertEqual(
            {
                "schema_version",
                "action_id",
                "operation_id",
                "tick_id",
                "world_id",
                "character_id",
                "action_type",
                "target_id",
                "parameters",
                "expected_state_version",
                "origin",
                "intent_nonce",
                "source_candidate_id",
            },
            set(intent),
        )
        json.dumps(intent, ensure_ascii=False)

    def test_candidate_ids_are_stable_across_instances(self) -> None:
        first = new_loop().plan().candidates
        second = new_loop().plan().candidates
        self.assertEqual(
            [item.candidate_id for item in first],
            [item.candidate_id for item in second],
        )


if __name__ == "__main__":
    unittest.main()
