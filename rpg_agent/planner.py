"""确定性候选生成与可解释行动选择。"""

from __future__ import annotations

from collections import deque
from typing import Any

from rpg_sim.engine import PARAMETER_FIELDS
from rpg_sim.ids import canonical_json, digest, stable_id
from rpg_sim.scenario import (
    ACTIONS,
    LOCATIONS,
    MAIN_ID,
    location_is_open,
)

from .models import Candidate, DecisionTrace
from .perception import Perception

BASE_SCORES = {
    "attend_class": 0.91,
    "observe": 0.74,
    "talk": 0.69,
    "study": 0.72,
    "rest": 0.35,
    "eat": 0.41,
    "explore": 0.76,
    "write_journal": 0.70,
    "move": 0.38,
}

TOPIC_BY_FACT = {
    "fact_canteen_public_menu": ("menu", ["npc_gao_public_menu"]),
    "fact_layout_brief": ("layout", ["goal_relevant_topic"]),
    "fact_photo_activity": ("photo_consent", ["consent_boundary"]),
    "fact_submission_floor_public": (
        "submission_floor",
        ["deadline_relevant", "public_fact"],
    ),
    "fact_public_cleanup": ("cleanup", ["public_activity"]),
}


class RulePlanner:
    schema_version = "rpg-decision-trace-v1"
    policy_id = "balanced_curiosity_v1"

    def __init__(self, seed: int):
        self.seed = seed

    def generate_candidates(
        self,
        state: dict[str, Any],
        perception: Perception,
    ) -> tuple[list[Candidate], list[dict[str, Any]]]:
        character = state["characters"][MAIN_ID]
        current_location = character["location_id"]
        time_text = perception.logical_time[11:16]
        accepted: list[Candidate] = []
        rejected: list[dict[str, Any]] = []

        if current_location in {"loc_dorm", "loc_canteen", "loc_river"}:
            meal_kind = self._meal_kind(perception.slot_key)
            accepted.append(
                self._candidate(
                    perception,
                    "eat",
                    current_location,
                    {"meal_kind": meal_kind},
                    extra_score=max(0.0, character["needs"]["hunger"] - 0.20),
                    reasons=["meal_location", "hunger_signal"],
                )
            )

        if current_location == "loc_dorm":
            accepted.append(
                self._candidate(
                    perception,
                    "rest",
                    current_location,
                    {"duration_slot_fraction": 0.5},
                    extra_score=max(0.0, 0.48 - character["needs"]["energy"]),
                    reasons=["safe_private_place", "energy_signal"],
                )
            )
            if (
                (perception.world_date == "2026-11-05" and perception.slot_key == "night")
                or (
                    perception.world_date == "2026-11-08"
                    and perception.slot_key == "night"
                )
            ):
                trigger = (
                    "photo_boundary"
                    if perception.world_date == "2026-11-05"
                    else "week_reflection"
                )
                accepted.append(
                    self._candidate(
                        perception,
                        "write_journal",
                        "personal_diary",
                        {"trigger_id": trigger},
                        extra_score=0.10,
                        reasons=["private_reflection", "journal_trigger"],
                    )
                )

        goal = character["goals"].get("goal_finish_feature")
        if (
            goal
            and goal["progress"] < 1.0
            and character["needs"]["focus"] >= 0.25
            and "writing_bench" in state["locations"][current_location]["facilities"]
        ):
            accepted.append(
                self._candidate(
                    perception,
                    "study",
                    "goal_finish_feature",
                    {"focus_mode": "drafting"},
                    extra_score=max(0.0, 0.85 - goal["progress"]) * 0.15,
                    reasons=["active_goal", "study_facility"],
                )
            )

        if (
            current_location == "loc_classroom"
            and perception.slot_key in {"morning_1", "morning_2", "afternoon_1"}
            and f"{perception.world_date}:{perception.slot_key}"
            not in state["settled_classes"]
        ):
            accepted.append(
                self._candidate(
                    perception,
                    "attend_class",
                    perception.slot_key,
                    {},
                    extra_score=0.08,
                    reasons=["scheduled_class", "classroom_present"],
                )
            )

        if (
            current_location in {"loc_library", "loc_classroom"}
            and "notice_board" in state["locations"][current_location]["facilities"]
        ):
            accepted.append(
                self._candidate(
                    perception,
                    "observe",
                    "notice_board",
                    {"focus_kind": "notice"},
                    extra_score=0.08,
                    reasons=["goal_relevant", "public_notice"],
                )
            )

        for npc in perception.nearby_characters:
            npc_id = npc["character_id"]
            source = state["npcs"][npc_id]
            if source["runtime_state"] != "available":
                continue
            for fact_id in source["knowledge_ids"]:
                mapping = TOPIC_BY_FACT.get(fact_id)
                if not mapping:
                    continue
                topic, reasons = mapping
                accepted.append(
                    self._candidate(
                        perception,
                        "talk",
                        npc_id,
                        {"topic": topic, "max_turns": 2},
                        extra_score=0.03,
                        reasons=["npc_present", *reasons],
                    )
                )
                break

        if (
            current_location == "loc_river"
            and perception.world_date >= "2026-11-07"
            and not state["activities"].get("river_cleanup")
        ):
            accepted.append(
                self._candidate(
                    perception,
                    "explore",
                    "river_cleanup",
                    {"activity_id": "river_cleanup"},
                    extra_score=0.13,
                    reasons=["registered_activity", "public_opportunity"],
                )
            )

        for target_location in LOCATIONS:
            if target_location == current_location:
                continue
            path = self._find_path(state, current_location, target_location)
            if not path:
                rejected.append(
                    self._rejected(
                        perception,
                        "move",
                        target_location,
                        "unreachable_target",
                    )
                )
                continue
            if any(
                not location_is_open(path_location, time_text)
                for path_location in path[1:]
            ):
                rejected.append(
                    self._rejected(
                        perception,
                        "move",
                        target_location,
                        "closed_location",
                    )
                )
                continue
            if (
                len(state["locations"][target_location]["occupants"])
                >= LOCATIONS[target_location]["capacity"]
            ):
                rejected.append(
                    self._rejected(
                        perception,
                        "move",
                        target_location,
                        "location_full",
                    )
                )
                continue
            accepted.append(
                self._candidate(
                    perception,
                    "move",
                    target_location,
                    {},
                    extra_score=0.02 if target_location == "loc_library" else 0.0,
                    reasons=["reachable_location", *(["goal_relevant"] if target_location == "loc_library" else [])],
                )
            )

        return accepted, rejected

    def plan(
        self,
        state: dict[str, Any],
        perception: Perception,
        *,
        degradation_reason: str | None = None,
    ) -> DecisionTrace:
        candidates, rejected = self.generate_candidates(state, perception)
        ranked = sorted(
            candidates,
            key=lambda candidate: (-candidate.score, candidate.candidate_id),
        )
        selected = ranked[0] if ranked else None
        return DecisionTrace(
            schema_version=self.schema_version,
            mode="rule_only",
            seed=self.seed,
            state_version=state["state_version"],
            tick_id=perception.tick_id,
            candidates=ranked,
            rejected_candidates=rejected,
            selected_action=selected.action_type if selected else None,
            selected_candidate_id=selected.candidate_id if selected else None,
            model_used=False,
            degradation_reason=degradation_reason,
        )

    def filter_candidates(
        self,
        state: dict[str, Any],
        perception: Perception,
        candidates: list[Candidate],
    ) -> tuple[list[Candidate], list[dict[str, Any]]]:
        accepted = []
        rejected = []
        current_location = state["characters"][MAIN_ID]["location_id"]
        time_text = perception.logical_time[11:16]
        for candidate in candidates:
            reason = None
            if candidate.action_type not in ACTIONS:
                reason = "unsupported_action"
            elif set(candidate.parameters) - PARAMETER_FIELDS[candidate.action_type]:
                reason = "invalid_parameters"
            elif candidate.action_type == "move":
                path = self._find_path(state, current_location, candidate.target_id)
                if not path:
                    reason = "unreachable_target"
                elif any(
                    not location_is_open(location_id, time_text)
                    for location_id in path[1:]
                ):
                    reason = "closed_location"
                elif (
                    len(state["locations"][candidate.target_id]["occupants"])
                    >= LOCATIONS[candidate.target_id]["capacity"]
                ):
                    reason = "location_full"
            elif candidate.action_type == "talk":
                npc = state["npcs"].get(candidate.target_id)
                if not npc or npc["location_id"] != current_location:
                    reason = "npc_not_present"
                elif npc["runtime_state"] != "available":
                    reason = "npc_unavailable"
            elif candidate.action_type == "observe":
                if "notice_board" not in state["locations"][current_location]["facilities"]:
                    reason = "target_not_visible"
            if reason:
                rejected.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "action_type": candidate.action_type,
                        "target_id": candidate.target_id,
                        "code": reason,
                    }
                )
            else:
                accepted.append(candidate)
        return accepted, rejected

    def _candidate(
        self,
        perception: Perception,
        action_type: str,
        target_id: str,
        parameters: dict[str, Any],
        *,
        extra_score: float,
        reasons: list[str],
    ) -> Candidate:
        candidate_id = stable_id(
            "cand",
            [
                perception.world_id,
                perception.world_date,
                perception.slot_key,
                action_type,
                target_id,
                canonical_json(parameters),
            ],
        )
        jitter = (
            int(digest({"seed": self.seed, "candidate_id": candidate_id})[:4], 16)
            % 31
        ) / 1000
        score = BASE_SCORES[action_type] + extra_score + jitter
        return Candidate(
            candidate_id=candidate_id,
            action_type=action_type,
            target_id=target_id,
            parameters=parameters,
            score=round(min(1.0, score), 4),
            reason_codes=reasons,
        )

    @staticmethod
    def _rejected(
        perception: Perception,
        action_type: str,
        target_id: str,
        code: str,
    ) -> dict[str, Any]:
        return {
            "candidate_id": stable_id(
                "cand",
                [
                    perception.world_id,
                    perception.world_date,
                    perception.slot_key,
                    action_type,
                    target_id,
                    "rejected",
                ],
            ),
            "action_type": action_type,
            "target_id": target_id,
            "code": code,
        }

    @staticmethod
    def _find_path(
        state: dict[str, Any],
        start: str,
        target: str,
    ) -> list[str]:
        if start == target:
            return [start]
        queue = deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            current = path[-1]
            neighbors = set(state["locations"][current]["connected_to"])
            for location in state["locations"].values():
                if current in location["connected_to"]:
                    neighbors.add(location["location_id"])
            for neighbor in sorted(neighbors):
                if neighbor in visited:
                    continue
                next_path = [*path, neighbor]
                if neighbor == target:
                    return next_path
                visited.add(neighbor)
                queue.append(next_path)
        return []

    @staticmethod
    def _meal_kind(slot_key: str) -> str:
        if slot_key == "dawn":
            return "breakfast"
        if slot_key in {"noon", "morning_2"}:
            return "lunch"
        if slot_key in {"evening", "night"}:
            return "dinner"
        return "snack"
