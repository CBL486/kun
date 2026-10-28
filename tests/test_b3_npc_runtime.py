from __future__ import annotations

import copy
import unittest

from rpg_npc.content import load_content_packs
from rpg_npc.models import ReactionTemplate, RelationshipProposal, RuntimeState
from rpg_npc.runtime import NPCMemoryFull, NPCRuntime, NPCScopeError
from rpg_npc.schedules import can_transition


def make_event(
    template_id: str,
    event_type: str,
    location_id: str,
    *,
    event_id: str = "evt_b3_test_001",
    occurred_at: str = "2026-11-04T14:40:00+08:00",
    visibility: str = "user_visible",
) -> dict:
    return {
        "event_id": event_id,
        "template_id": template_id,
        "event_type": event_type,
        "location_id": location_id,
        "participants": ["char_lin_cheng"],
        "summary": "一条公开测试事件。",
        "visibility": visibility,
        "occurred_at": occurred_at,
        "world_date": occurred_at[:10],
    }


class NPCRuntimeTests(unittest.TestCase):
    def test_runtime_state_machine_rejects_unlisted_transitions(self) -> None:
        self.assertTrue(
            can_transition(RuntimeState.SCHEDULED, RuntimeState.COMMUTING)
        )
        self.assertTrue(
            can_transition(RuntimeState.AVAILABLE, RuntimeState.INTERACTION_COOLDOWN)
        )
        self.assertFalse(
            can_transition(RuntimeState.ASLEEP, RuntimeState.AVAILABLE)
        )

    def test_all_four_npcs_complete_a_day_without_llm(self) -> None:
        runtime = NPCRuntime()
        schedule = runtime.run_day("2026-11-04")
        self.assertEqual(
            {"npc_chen", "npc_su", "npc_gao", "npc_gu"},
            set(schedule),
        )
        self.assertFalse(hasattr(runtime, "llm"))
        for npc_schedule in schedule.values():
            self.assertEqual(8, len(npc_schedule))
            self.assertEqual("ASLEEP", npc_schedule["night"]["runtime_state"])

    def test_schedule_locations_match_fixed_scene(self) -> None:
        schedule = NPCRuntime().run_day("2026-11-04")
        self.assertEqual(
            "loc_classroom",
            schedule["npc_su"]["afternoon_1"]["location_id"],
        )
        self.assertEqual(
            "loc_classroom",
            schedule["npc_gu"]["morning_2"]["location_id"],
        )
        self.assertEqual(
            "loc_canteen",
            schedule["npc_gao"]["noon"]["location_id"],
        )
        self.assertEqual(
            "loc_library",
            schedule["npc_chen"]["morning_1"]["location_id"],
        )

    def test_context_has_only_npc_visible_knowledge(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        context = runtime.context("npc_chen", event)
        self.assertEqual([event["event_id"]], [item["event_id"] for item in context["visible_events"]])
        self.assertNotIn("prompt", context)
        self.assertNotIn("character_private_memory", context)
        self.assertNotIn("npc_gao", context["known_fact_ids"])

    def test_internal_event_cannot_enter_npc_context(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-05", "21:30", "night")
        private_event = make_event(
            "dirtpl_sunday_letter_v1",
            "journal_written",
            "loc_dorm",
            visibility="internal",
            occurred_at="2026-11-05T21:30:00+08:00",
        )
        with self.assertRaises(NPCScopeError):
            runtime.context("npc_chen", private_event)

    def test_character_visible_event_is_limited_to_participants(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
            visibility="character_visible",
        )
        event["participants"] = ["char_lin_cheng", "npc_su"]
        context = runtime.context("npc_chen", event)
        self.assertEqual([], context["visible_events"])
        outcome = runtime.react("npc_chen", event)
        self.assertEqual("npc_scope_violation", outcome.code)

    def test_unknown_fact_returns_explicit_unknown_response(self) -> None:
        runtime = NPCRuntime()
        response = runtime.answer("npc_gao", "fact_notice_board_deadline")
        self.assertEqual("这个我没听说，不能替别人猜。", response)
        self.assertEqual(
            "这个我不聊，换个话题吧。",
            runtime.refuse("content_scope"),
        )

    def test_missing_template_returns_safe_fallback(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        event = make_event(
            "dirtpl_unregistered_public_event",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        outcome = runtime.react("npc_chen", event)
        self.assertEqual("npc_template_missing", outcome.code)
        self.assertEqual("我知道得不多，等有确切消息再说。", outcome.message)

    def test_forbidden_fact_id_prevents_template_selection(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-03", "12:15", "noon")
        runtime.npcs["npc_gao"]["knowledge_ids"].append(
            "fact_notice_board_deadline"
        )
        event = make_event(
            "dirtpl_canteen_menu_change_v1",
            "conversation_completed",
            "loc_canteen",
            occurred_at="2026-11-03T12:15:00+08:00",
        )
        outcome = runtime.react("npc_gao", event)
        self.assertIsNone(outcome.reaction)
        self.assertEqual("npc_template_missing", outcome.code)

    def test_same_npc_event_template_is_not_repeated(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        first = runtime.react("npc_chen", event)
        second = runtime.react("npc_chen", event)
        self.assertEqual("approved", first.status)
        self.assertEqual("npc_repeat_blocked", second.code)
        self.assertEqual(1, len(runtime.reaction_records))
        self.assertEqual(1, len(runtime.memory_slots("npc_chen")))

    def test_same_utterance_inside_48_hours_is_blocked(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        first_event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        first = runtime.react("npc_chen", first_event)
        self.assertEqual("approved", first.status)

        base = runtime.templates["say_chen_notice_reminder_01"]
        runtime.templates["say_chen_notice_reminder_02"] = ReactionTemplate(
            template_id="say_chen_notice_reminder_02",
            npc_id=base.npc_id,
            intent="notice_reminder_repeat",
            utterance=base.utterance,
            event_template_ids=("public_event_followup",),
            required_fact_ids=base.required_fact_ids,
            priority=10,
        )
        second_event = make_event(
            "public_event_followup",
            "detail_observed",
            "loc_library",
            event_id="evt_b3_test_002",
            occurred_at="2026-11-02T11:00:00+08:00",
        )
        second = runtime.react("npc_chen", second_event)
        self.assertEqual("fallback", second.status)
        self.assertEqual("npc_repeat_blocked", second.code)

    def test_ordinary_memory_is_deterministically_evicted_at_eight_slots(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        npc = runtime.npcs["npc_chen"]
        npc["memory_slots"] = [
            {
                "slot_id": f"old_{index}",
                "kind": "public_fact",
                "content_key": f"fact_{index}",
                "source_event_id": f"evt_old_{index}",
                "important": False,
                "expires_on": f"2026-11-{index + 1:02}",
                "last_used_at": "2026-11-01T00:00:00+08:00",
            }
            for index in range(8)
        ]
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            event_id="evt_b3_memory_eviction",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        outcome = runtime.react("npc_chen", event)
        self.assertEqual("approved", outcome.status)
        slots = runtime.memory_slots("npc_chen")
        self.assertEqual(8, len(slots))
        self.assertNotIn("old_0", {slot["slot_id"] for slot in slots})

    def test_important_memory_slots_are_never_silently_replaced(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        npc = runtime.npcs["npc_chen"]
        npc["memory_slots"] = [
            {
                "slot_id": f"important_{index}",
                "kind": "promise",
                "content_key": f"promise_{index}",
                "source_event_id": f"evt_promise_{index}",
                "important": True,
                "expires_on": "2026-11-09",
                "last_used_at": "2026-11-01T00:00:00+08:00",
            }
            for index in range(8)
        ]
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            event_id="evt_b3_memory_full",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        with self.assertRaises(NPCMemoryFull):
            runtime.react("npc_chen", event)

    def test_relationship_change_is_event_bound_and_replay_safe(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-04", "14:40", "afternoon_1")
        event = make_event(
            "dirtpl_layout_disagreement_v1",
            "conversation_completed",
            "loc_classroom",
        )
        outcome = runtime.react("npc_su", event)
        self.assertEqual("approved", outcome.status)
        proposal = outcome.reaction.relationship_proposals[0]
        self.assertEqual(event["event_id"], proposal.source_event_id)
        before = runtime._relationship_snapshot("npc_su")["tension"]
        applied = runtime.apply_relationship_proposal(proposal)
        self.assertEqual("applied", applied["status"])
        replayed = runtime.apply_relationship_proposal(proposal)
        self.assertEqual("replayed", replayed["status"])
        self.assertAlmostEqual(
            before + proposal.delta,
            runtime._relationship_snapshot("npc_su")["tension"],
        )

    def test_relationship_delta_over_limit_is_rejected(self) -> None:
        runtime = NPCRuntime()
        proposal = RelationshipProposal(
            relationship_id="rel_sha256_unused",
            npc_id="npc_su",
            source_event_id="evt_b3_invalid_delta",
            dimension="trust",
            delta=0.09,
            reason_code="invalid",
        )
        with self.assertRaisesRegex(ValueError, "relationship_delta_exceeds_limit"):
            proposal.validate()

    def test_unavailable_npc_does_not_speak(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "22:00", "night")
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T22:00:00+08:00",
        )
        outcome = runtime.react("npc_chen", event)
        self.assertEqual("npc_unavailable", outcome.code)
        self.assertIsNone(outcome.reaction)

    def test_content_packs_are_complete_and_approved(self) -> None:
        packs = load_content_packs()
        self.assertEqual(3, len(packs["courses"]["courses"]))
        self.assertEqual(12, len(packs["events"]["events"]))
        self.assertTrue(
            all(
                course["rights_status"] in {"original", "authorized"}
                for course in packs["courses"]["courses"]
            )
        )
        self.assertTrue(
            all(
                event["review_status"] == "approved"
                for event in packs["events"]["events"]
            )
        )

    def test_runtime_never_mutates_template_definitions(self) -> None:
        runtime = NPCRuntime()
        templates = copy.deepcopy(runtime.templates)
        runtime.set_time("2026-11-03", "12:15", "noon")
        runtime.react(
            "npc_gao",
            make_event(
                "dirtpl_canteen_menu_change_v1",
                "conversation_completed",
                "loc_canteen",
                occurred_at="2026-11-03T12:15:00+08:00",
            ),
        )
        self.assertEqual(templates, runtime.templates)

    def test_reaction_uses_no_model_and_all_acceptance_npcs_respond(self) -> None:
        fixtures = [
            (
                "npc_chen",
                "2026-11-02",
                "10:10",
                "morning_2",
                "dirtpl_library_notice_deadline_v1",
                "detail_observed",
                "loc_library",
            ),
            (
                "npc_su",
                "2026-11-04",
                "14:40",
                "afternoon_1",
                "dirtpl_layout_disagreement_v1",
                "conversation_completed",
                "loc_classroom",
            ),
            (
                "npc_gao",
                "2026-11-03",
                "12:15",
                "noon",
                "dirtpl_canteen_menu_change_v1",
                "conversation_completed",
                "loc_canteen",
            ),
            (
                "npc_gu",
                "2026-11-05",
                "10:00",
                "morning_2",
                "dirtpl_photo_permission_v1",
                "conversation_completed",
                "loc_classroom",
            ),
        ]
        for index, fixture in enumerate(fixtures):
            npc_id, date, time, slot, template, event_type, location = fixture
            runtime = NPCRuntime()
            runtime.set_time(date, time, slot)
            outcome = runtime.react(
                npc_id,
                make_event(
                    template,
                    event_type,
                    location,
                    event_id=f"evt_b3_acceptance_{index}",
                    occurred_at=f"{date}T{time}:00+08:00",
                ),
            )
            self.assertEqual("approved", outcome.status)
            self.assertFalse(outcome.reaction.model_used)

    def test_one_event_triggers_at_most_two_npc_reactions(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-07", "10:15", "morning_2")
        event = make_event(
            "dirtpl_river_cleanup_v1",
            "activity_participated",
            "loc_river",
            event_id="evt_b3_two_reactions",
            occurred_at="2026-11-07T10:15:00+08:00",
        )
        outcomes = runtime.react_to_event(event)
        self.assertEqual(2, len(outcomes))
        self.assertTrue(all(outcome.status == "approved" for outcome in outcomes))
        self.assertEqual(
            {"npc_su", "npc_gu"},
            {outcome.reaction.npc_id for outcome in outcomes},
        )
        for outcome in outcomes:
            for proposal in outcome.reaction.relationship_proposals:
                self.assertEqual(
                    "applied",
                    runtime.apply_relationship_proposal(proposal)["status"],
                )

    def test_npc_context_never_contains_another_npcs_memory(self) -> None:
        runtime = NPCRuntime()
        runtime.set_time("2026-11-02", "10:10", "morning_2")
        runtime.npcs["npc_su"]["memory_slots"].append(
            {
                "slot_id": "su_private_slot",
                "kind": "completed_exchange",
                "content_key": "su_only",
                "source_event_id": "evt_su_only",
                "important": True,
                "expires_on": "2026-11-09",
                "last_used_at": "2026-11-02T10:00:00+08:00",
            }
        )
        event = make_event(
            "dirtpl_library_notice_deadline_v1",
            "detail_observed",
            "loc_library",
            occurred_at="2026-11-02T10:10:00+08:00",
        )
        context = runtime.context("npc_chen", event)
        self.assertEqual([], context["memory_slots"])
        self.assertNotIn("su_private_slot", str(context))


if __name__ == "__main__":
    unittest.main()
