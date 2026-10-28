"""B1 世界引擎：验证动作、事务式提交事件。"""

from __future__ import annotations

import copy
from typing import Any

from .ids import canonical_json, normalize_text, relationship_id, stable_id
from .mocks import MockReviewer
from .scenario import (
    ACTION_TEMPLATES,
    ACTIONS,
    CRITICAL_TEMPLATES,
    DIRECTOR_TEMPLATES,
    LOCATIONS,
    MAIN_ID,
    SLOT_WINDOWS,
    WORLD_ID,
    location_is_open,
    scheduled_npc,
)


class WorldError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


EVENT_SUMMARIES = {
    "dirtpl_campus_first_commute_v1": "林澄从宿舍前往教学楼，开始本周课程。",
    "dirtpl_library_notice_deadline_v1": "公告栏贴出校刊截稿提前的新通知，林澄记下新的时间要求。",
    "dirtpl_canteen_menu_change_v1": "食堂更新了今日菜单；高原只说明公开的售罄信息，没有谈论截稿变化。",
    "dirtpl_layout_disagreement_v1": "苏晚提出更醒目的版面，林澄担心文章重点被压过，两人明确保留了分歧。",
    "dirtpl_photo_permission_v1": "顾言提出拍摄活动现场，林澄只同意用于校刊内部评审，双方确认了使用范围。",
    "dirtpl_notice_misreading_v1": "林澄重新核对公告栏，发现截稿说明还包含楼层提交要求。",
    "dirtpl_reconciliation_v1": "林澄依据新公开的楼层要求向苏晚说明，双方确认了提交分工。",
    "dirtpl_river_cleanup_v1": "林澄参加河边公开清理活动，与苏晚、顾言协作。",
    "dirtpl_sunday_letter_v1": "林澄整理本周经历，选择在周分享中讲截稿、版面分歧与和解。",
}

TOPIC_FACTS = {
    "menu": "fact_canteen_public_menu",
    "layout": "fact_layout_brief",
    "photo_consent": "fact_photo_activity",
    "photo_scope": "fact_photo_activity",
    "submission_floor": "fact_submission_floor_public",
    "clarify": "fact_submission_floor_public",
    "cleanup": "fact_public_cleanup",
    "photos": "fact_photo_activity",
}

INTENT_FIELDS = {
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
}

PARAMETER_FIELDS = {
    "move": set(),
    "attend_class": set(),
    "study": {"focus_mode"},
    "talk": {"topic", "max_turns"},
    "rest": {"duration_slot_fraction"},
    "eat": {"meal_kind"},
    "explore": {"activity_id", "walk"},
    "observe": {"focus_kind"},
    "write_journal": {"trigger_id"},
}


class WorldEngine:
    def __init__(
        self,
        state: dict[str, Any],
        reviewer: MockReviewer | None = None,
    ):
        self.state = state
        self.reviewer = reviewer or MockReviewer()
        self.operations: dict[str, dict[str, Any]] = {}

    def prepare_time(self, world_date: str, time_text: str, slot_key: str) -> None:
        if world_date not in DATED_SLOTS:
            raise WorldError("precondition_failed", f"未知场景日期：{world_date}")
        if slot_key not in SLOT_WINDOWS:
            raise WorldError("invalid_schema", f"未知 slot：{slot_key}")
        if time_text < SLOT_WINDOWS[slot_key][0] or time_text > SLOT_WINDOWS[slot_key][1]:
            raise WorldError(
                "precondition_failed",
                f"{time_text} 不在 {slot_key} 时段内",
            )
        self.state["world_date"] = world_date
        self.state["logical_time"] = f"{world_date}T{time_text}:00+08:00"
        self.state["open_slot"] = slot_key
        for npc_id, npc in self.state["npcs"].items():
            location, runtime_state = scheduled_npc(npc_id, world_date, time_text)
            npc["location_id"] = location
            npc["runtime_state"] = runtime_state
        self._refresh_occupants()

    def apply(
        self,
        intent: dict[str, Any],
        *,
        event_template_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            self._validate_envelope(intent)
        except WorldError as error:
            return self._error(error.code, str(error))
        operation_id = intent["operation_id"]
        payload_hash = canonical_json(
            {key: value for key, value in intent.items() if key != "action_id"}
        )
        existing = self.operations.get(operation_id)
        if existing:
            if existing["payload_hash"] != payload_hash:
                return self._error("duplicate_operation", "同一 operation_id 的内容不一致")
            event = copy.deepcopy(existing["event"])
            return {
                "ok": True,
                "code": None,
                "message": "返回已提交结果",
                "event": event,
                "state_version_after": self.state["state_version"],
                "replayed": True,
            }

        if intent["expected_state_version"] != self.state["state_version"]:
            return self._error(
                "stale_state",
                "状态版本已过期",
                details={
                    "expected": intent["expected_state_version"],
                    "actual": self.state["state_version"],
                },
            )

        trial = copy.deepcopy(self.state)
        try:
            event = self._commit_to_trial(
                trial,
                intent,
                event_template_id=event_template_id,
            )
        except WorldError as error:
            return self._error(error.code, str(error))

        self.state = trial
        self._refresh_occupants()
        self.operations[operation_id] = {
            "payload_hash": payload_hash,
            "event": copy.deepcopy(event),
        }
        return {
            "ok": True,
            "code": None,
            "message": "事件已提交",
            "event": event,
            "state_version_after": self.state["state_version"],
            "replayed": False,
        }

    def snapshot(self) -> dict[str, Any]:
        self._refresh_occupants()
        return copy.deepcopy(self.state)

    def settle_evening(
        self,
        world_date: str,
        time_text: str = "18:45",
    ) -> dict[str, Any] | None:
        """日终系统事件：确保主角色回到宿舍，并以内部事件留下追溯链。"""
        self.prepare_time(world_date, time_text, "evening")
        character = self.state["characters"][MAIN_ID]
        before_location = character["location_id"]
        if before_location == "loc_dorm":
            return None

        sequence = self.state["sequence"] + 1
        template_id = "system_daily_return_v1"
        action_id = stable_id(
            "act", [WORLD_ID, world_date, sequence, template_id, "system"]
        )
        event_id = stable_id(
            "evt",
            [WORLD_ID, world_date, sequence, template_id, action_id],
        )
        event_summary = "日终时，林澄回到宿舍整理当天物品。"
        review_status = self.reviewer.review(event_summary)
        if review_status != "approved":
            raise WorldError("content_policy_blocked", "内容审核未通过")
        state_version_before = self.state["state_version"]
        character["location_id"] = "loc_dorm"
        self.state["sequence"] = sequence
        self.state["state_version"] += 1
        self._refresh_occupants()

        event = {
            "schema_version": "rpg-event-v1",
            "event_id": event_id,
            "world_id": WORLD_ID,
            "tick_id": stable_id(
                "tick", [WORLD_ID, MAIN_ID, world_date, "evening", "system_return"]
            ),
            "action_id": action_id,
            "source_candidate_id": None,
            "template_id": template_id,
            "world_date": world_date,
            "slot_key": "evening",
            "sequence": sequence,
            "occurred_at": self.state["logical_time"],
            "event_type": "day_settled",
            "participants": [MAIN_ID],
            "location_id": "loc_dorm",
            "causality": {
                "kind": "system_schedule",
                "reason_code": "end_of_day_return",
            },
            "summary": event_summary,
            "knowledge_basis": [],
            "state_changes": [
                {
                    "path": f"characters.{MAIN_ID}.location_id",
                    "operation": "value",
                    "before": before_location,
                    "value": "loc_dorm",
                    "after": "loc_dorm",
                }
            ],
            "relationship_changes": [],
            "memory_candidates": [],
            "visibility": "internal",
            "review": {
                "status": review_status,
                "policy_version": self.reviewer.policy_version,
            },
            "state_version_before": state_version_before,
            "state_version_after": state_version_before + 1,
            "committed_at": self.state["logical_time"],
        }
        self.state["events"].append(event)
        return event

    def _validate_envelope(self, intent: dict[str, Any]) -> None:
        unknown = set(intent) - INTENT_FIELDS
        if unknown:
            raise WorldError("invalid_action_schema", f"未知意图字段：{sorted(unknown)}")
        required = INTENT_FIELDS - {"source_candidate_id"}
        missing = required - set(intent)
        if missing:
            raise WorldError("invalid_action_schema", f"缺少意图字段：{sorted(missing)}")
        if intent["world_id"] != WORLD_ID:
            raise WorldError("unknown_reference", "世界不存在")
        if intent["character_id"] != MAIN_ID:
            raise WorldError("unknown_reference", "主角色不存在")
        if intent["action_type"] not in ACTIONS:
            raise WorldError("unsupported_action", "动作不在九个注册动作内")
        parameters = intent["parameters"]
        if not isinstance(parameters, dict):
            raise WorldError("invalid_action_schema", "parameters 必须是对象")
        unknown_parameters = set(parameters) - PARAMETER_FIELDS[intent["action_type"]]
        if unknown_parameters:
            raise WorldError(
                "invalid_action_schema",
                f"动作参数不允许：{sorted(unknown_parameters)}",
            )
        forbidden = {"event_id", "state_changes", "relationship_changes", "cost"}
        if forbidden & set(intent):
            raise WorldError("invalid_action_schema", "意图包含世界写入字段")

    def _commit_to_trial(
        self,
        trial: dict[str, Any],
        intent: dict[str, Any],
        *,
        event_template_id: str | None,
    ) -> dict[str, Any]:
        action_type = intent["action_type"]
        target_id = normalize_text(intent["target_id"])
        parameters = intent["parameters"]
        character = trial["characters"][MAIN_ID]
        state_changes: list[dict[str, Any]] = []
        relationship_changes: list[dict[str, Any]] = []
        knowledge_basis: list[str] = []
        participants = [MAIN_ID]
        template_id = event_template_id or ACTION_TEMPLATES[action_type]
        visibility = "user_visible"
        reason_code = "rule_selected_action"
        movement_path: list[str] = []

        current_location = character["location_id"]
        time_text = trial["logical_time"][11:16]

        if action_type == "move":
            self._require_location(target_id)
            movement_path = self._find_path(trial, current_location, target_id)
            if not movement_path:
                raise WorldError("precondition_failed", "目标地点不可达")
            for path_location_id in movement_path[1:]:
                if not location_is_open(path_location_id, time_text):
                    raise WorldError("precondition_failed", "路径上有地点当前未开放")
            if len(trial["locations"][target_id]["occupants"]) >= LOCATIONS[target_id]["capacity"]:
                raise WorldError("precondition_failed", "目标地点已满")
            self._set_character_location(trial, target_id, state_changes)
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", -0.03, state_changes
            )
            reason_code = "reachable_open_location"

        elif action_type == "attend_class":
            if current_location != "loc_classroom":
                raise WorldError("precondition_failed", "角色不在教学楼")
            if target_id != trial["open_slot"]:
                raise WorldError("precondition_failed", "课程与当前时段不匹配")
            if not target_id.startswith(("morning", "afternoon")):
                raise WorldError("precondition_failed", "当前时段没有课程")
            class_key = f"{trial['world_date']}:{target_id}"
            if class_key in trial["settled_classes"]:
                raise WorldError("precondition_failed", "本节课程已经结算")
            trial["settled_classes"].append(class_key)
            state_changes.append(
                {
                    "path": "course_progress.attendance",
                    "operation": "value",
                    "before": None,
                    "value": class_key,
                    "after": class_key,
                }
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "focus", 0.10, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", -0.10, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "stress", 0.02, state_changes
            )
            self._add_number_change(
                trial,
                MAIN_ID,
                "goals",
                "goal_finish_feature",
                0.05,
                state_changes,
                nested="progress",
            )
            reason_code = "scheduled_class"

        elif action_type == "study":
            if target_id != "goal_finish_feature":
                raise WorldError("unknown_reference", "目标不存在")
            needs = character["needs"]
            if needs["focus"] < 0.25:
                raise WorldError("precondition_failed", "专注度不足")
            goal = character["goals"]["goal_finish_feature"]
            if goal["progress"] >= 1.0:
                raise WorldError("precondition_failed", "目标已完成")
            mode = parameters.get("focus_mode")
            if mode not in {None, "reading", "drafting"}:
                raise WorldError("invalid_action_schema", "学习模式无效")
            delta = 0.10 if mode == "drafting" else 0.08
            self._add_number_change(
                trial,
                MAIN_ID,
                "goals",
                "goal_finish_feature",
                delta,
                state_changes,
                nested="progress",
            )
            trial["course_progress"]["goal_finish_feature"] = character["goals"][
                "goal_finish_feature"
            ]["progress"]
            self._add_number_change(
                trial, MAIN_ID, "needs", "focus", -0.05, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", -0.05, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "stress", 0.01, state_changes
            )
            reason_code = "goal_relevant_study"

        elif action_type == "talk":
            npc = trial["npcs"].get(target_id)
            if not npc:
                raise WorldError("unknown_reference", "NPC 不存在")
            if npc["location_id"] != current_location:
                raise WorldError("precondition_failed", "NPC 不在场")
            if npc["runtime_state"] not in {"available", "AVAILABLE"}:
                raise WorldError("precondition_failed", "NPC 当前不可互动")
            topic = normalize_text(parameters.get("topic", ""))
            if not topic or len(topic) > 40:
                raise WorldError("invalid_action_schema", "话题长度无效")
            max_turns = parameters.get("max_turns", 1)
            if max_turns not in {1, 2}:
                raise WorldError("invalid_action_schema", "max_turns 只能为 1 或 2")
            fact_id = TOPIC_FACTS.get(topic)
            if not fact_id:
                raise WorldError("npc_knowledge_blocked", "NPC 缺少该话题的知识依据")
            if fact_id not in npc["knowledge_ids"]:
                raise WorldError("npc_knowledge_blocked", "NPC 没有该公开事实")
            knowledge_basis = [fact_id]
            participants.append(target_id)
            self._add_number_change(
                trial, MAIN_ID, "needs", "social", 0.06, state_changes
            )
            rid = relationship_id(MAIN_ID, target_id)
            if template_id == "dirtpl_layout_disagreement_v1":
                self._add_relationship_change(
                    trial, rid, "tension", 0.04, relationship_changes, "event_placeholder"
                )
            elif template_id == "dirtpl_reconciliation_v1":
                self._add_relationship_change(
                    trial, rid, "tension", -0.03, relationship_changes, "event_placeholder"
                )
                self._add_relationship_change(
                    trial, rid, "trust", 0.04, relationship_changes, "event_placeholder"
                )
            else:
                self._add_relationship_change(
                    trial, rid, "familiarity", 0.02, relationship_changes, "event_placeholder"
                )
            reason_code = "public_topic_exchange"

        elif action_type == "rest":
            if target_id != current_location or current_location != "loc_dorm":
                raise WorldError("precondition_failed", "只能在宿舍休息")
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", 0.15, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "stress", -0.08, state_changes
            )
            reason_code = "safe_rest"

        elif action_type == "eat":
            if target_id != current_location:
                raise WorldError("precondition_failed", "只能在当前地点用餐")
            if current_location not in {"loc_dorm", "loc_canteen", "loc_river"}:
                raise WorldError("precondition_failed", "当前地点没有餐食")
            meal_kind = parameters.get("meal_kind")
            if meal_kind not in {"breakfast", "lunch", "dinner", "snack"}:
                raise WorldError("invalid_action_schema", "餐别无效")
            if current_location == "loc_river" and meal_kind != "lunch":
                raise WorldError("precondition_failed", "河边仅提供活动自带午餐")
            self._add_number_change(
                trial, MAIN_ID, "needs", "hunger", -0.32, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", 0.09, state_changes
            )
            reason_code = "meal_supported"

        elif action_type == "explore":
            activity_id = parameters.get("activity_id")
            if target_id != "river_cleanup" or activity_id != "river_cleanup":
                raise WorldError("unknown_reference", "活动未注册")
            if current_location != "loc_river":
                raise WorldError("precondition_failed", "活动地点不匹配")
            trial["activities"]["river_cleanup"] = True
            state_changes.append(
                {
                    "path": "activities.river_cleanup",
                    "operation": "value",
                    "before": None,
                    "value": True,
                    "after": True,
                }
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "energy", -0.05, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "social", 0.05, state_changes
            )
            self._add_number_change(
                trial, MAIN_ID, "needs", "stress", -0.04, state_changes
            )
            reason_code = "registered_public_activity"

        elif action_type == "observe":
            if target_id != "notice_board":
                raise WorldError("unknown_reference", "观察目标不可见")
            if current_location not in {"loc_library", "loc_classroom"}:
                raise WorldError("precondition_failed", "公告栏不在当前地点")
            self._add_number_change(
                trial, MAIN_ID, "needs", "focus", 0.02, state_changes
            )
            reason_code = "goal_relevant_observation"

        elif action_type == "write_journal":
            if target_id != "personal_diary":
                raise WorldError("unknown_reference", "日记目标不存在")
            if current_location not in {"loc_dorm", "loc_river"}:
                raise WorldError("precondition_failed", "当前地点不适合写日记")
            trigger_id = parameters.get("trigger_id")
            if trigger_id not in {"photo_boundary", "week_reflection"}:
                raise WorldError("precondition_failed", "日记触发条件不满足")
            visibility = "internal"
            self._add_number_change(
                trial, MAIN_ID, "needs", "stress", -0.04, state_changes
            )
            reason_code = "private_reflection"

        event_id = stable_id(
            "evt",
            [
                trial["world_id"],
                trial["world_date"],
                trial["sequence"] + 1,
                template_id,
                intent["action_id"],
            ],
        )

        for change in relationship_changes:
            change["event_id"] = event_id

        if action_type == "talk":
            npc = trial["npcs"][target_id]
            if not any(slot.get("source_event_id") == event_id for slot in npc["memory_slots"]):
                if len(npc["memory_slots"]) >= 8:
                    raise WorldError("npc_memory_full", "NPC 有限记忆槽已满")
                npc["memory_slots"].append(
                    {
                        "slot_id": f"{target_id}_slot_{len(npc['memory_slots']) + 1:02}",
                        "kind": "completed_exchange",
                        "content_key": knowledge_basis[0],
                        "source_event_id": event_id,
                        "important": template_id in CRITICAL_TEMPLATES,
                        "expires_on": trial["world_date"],
                    }
                )
                state_changes.append(
                    {
                        "path": f"npc.{target_id}.memory_slots",
                        "operation": "append",
                        "before": None,
                        "value": npc["memory_slots"][-1]["slot_id"],
                        "after": npc["memory_slots"][-1]["slot_id"],
                    }
                )

        visibility = "internal" if action_type == "write_journal" else visibility
        event_summary = EVENT_SUMMARIES.get(
            template_id,
            self._default_summary(action_type, target_id),
        )
        review_status = self.reviewer.review(event_summary)
        if review_status != "approved":
            raise WorldError("content_policy_blocked", "内容审核未通过")

        event = {
            "schema_version": "rpg-event-v1",
            "event_id": event_id,
            "world_id": trial["world_id"],
            "tick_id": intent["tick_id"],
            "action_id": intent["action_id"],
            "source_candidate_id": intent.get("source_candidate_id"),
            "template_id": template_id,
            "world_date": trial["world_date"],
            "slot_key": trial["open_slot"],
            "sequence": trial["sequence"] + 1,
            "occurred_at": trial["logical_time"],
            "event_type": self._event_type(action_type, template_id),
            "participants": participants,
            "location_id": current_location,
            "causality": {
                "kind": "character_action" if action_type != "write_journal" else "reflection",
                "reason_code": reason_code,
            },
            "summary": event_summary,
            "knowledge_basis": knowledge_basis,
            "state_changes": state_changes,
            "relationship_changes": relationship_changes,
            "memory_candidates": [
                {
                    "candidate_index": 0,
                    "kind": "reflection" if action_type == "write_journal" else "event",
                    "source": "school_event",
                    "summary": event_summary,
                    "importance": 0.72 if template_id in CRITICAL_TEMPLATES else 0.35,
                    "emotional_weight": 0.42 if template_id in CRITICAL_TEMPLATES else 0.16,
                    "scene_tags": [LOCATIONS[current_location]["kind"]]
                    + (["critical"] if template_id in CRITICAL_TEMPLATES else []),
                }
            ],
            "visibility": visibility,
            "review": {
                "status": review_status,
                "policy_version": self.reviewer.policy_version,
            },
            "state_version_before": trial["state_version"],
            "state_version_after": trial["state_version"] + 1,
            "committed_at": trial["logical_time"],
        }
        if movement_path:
            event["movement_path"] = movement_path

        trial["sequence"] += 1
        trial["state_version"] += 1
        trial["events"].append(event)
        character["state"] = self._derive_state(character["needs"])
        return event

    def _event_type(self, action_type: str, template_id: str) -> str:
        return {
            "move": "character_moved",
            "attend_class": "class_attended",
            "study": "study_progressed",
            "talk": "conversation_completed",
            "rest": "character_rested",
            "eat": "meal_completed",
            "explore": "activity_participated",
            "observe": "detail_observed",
            "write_journal": "journal_written",
        }[action_type]

    def _default_summary(self, action_type: str, target_id: str) -> str:
        summaries = {
            "move": f"林澄移动到 {target_id}。",
            "attend_class": f"林澄完成当前时段课程。",
            "study": "林澄推进校刊短文任务。",
            "talk": f"林澄与 {target_id} 完成一次公开交流。",
            "rest": "林澄在宿舍安静休息。",
            "eat": "林澄完成一餐并恢复精力。",
            "explore": "林澄参加已注册公开活动。",
            "observe": "林澄观察了当前可见的公开细节。",
            "write_journal": "林澄写下只对自己可见的本周记录。",
        }
        return summaries[action_type]

    def _derive_state(self, needs: dict[str, float]) -> str:
        if needs["energy"] < 0.25:
            return "tired"
        if needs["stress"] > 0.65:
            return "low"
        if needs["focus"] > 0.72:
            return "flow"
        if needs["social"] > 0.70:
            return "excited"
        return "calm"

    def _require_location(self, location_id: str) -> None:
        if location_id not in self.state["locations"]:
            raise WorldError("unknown_reference", "地点不存在")

    def _find_path(
        self,
        trial: dict[str, Any],
        start: str,
        target: str,
    ) -> list[str]:
        if start == target:
            return [start]
        queue: list[list[str]] = [[start]]
        visited = {start}
        while queue:
            path = queue.pop(0)
            current = path[-1]
            neighbors = set(trial["locations"][current]["connected_to"])
            for location in trial["locations"].values():
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

    def _set_character_location(
        self,
        trial: dict[str, Any],
        target_id: str,
        changes: list[dict[str, Any]],
    ) -> None:
        character = trial["characters"][MAIN_ID]
        before = character["location_id"]
        character["location_id"] = target_id
        changes.append(
            {
                "path": f"characters.{MAIN_ID}.location_id",
                "operation": "value",
                "before": before,
                "value": target_id,
                "after": target_id,
            }
        )

    def _add_number_change(
        self,
        trial: dict[str, Any],
        character_id: str,
        group: str,
        key: str,
        delta: float,
        changes: list[dict[str, Any]],
        *,
        nested: str | None = None,
    ) -> None:
        character = trial["characters"][character_id]
        container = character[group]
        if nested:
            container = container[key]
            key = nested
        before = float(container[key])
        after = max(0.0, min(1.0, before + delta))
        container[key] = round(after, 4)
        path = (
            f"characters.{character_id}.{group}.{key}"
            if not nested
            else f"characters.{character_id}.{group}.{key}"
        )
        if group == "goals":
            path = f"characters.{character_id}.goal_progress.goal_finish_feature"
            actual = trial["characters"][character_id]["goals"]["goal_finish_feature"][
                "progress"
            ]
            trial["course_progress"]["goal_finish_feature"] = actual
        changes.append(
            {
                "path": path,
                "operation": "delta",
                "before": round(before, 4),
                "value": round(container[key] - before, 4),
                "after": round(container[key], 4),
            }
        )

    def _add_relationship_change(
        self,
        trial: dict[str, Any],
        rid: str,
        dimension: str,
        delta: float,
        changes: list[dict[str, Any]],
        event_id: str,
    ) -> None:
        if abs(delta) > 0.08:
            raise WorldError("invalid_schema", "单次关系变化超过上限")
        relationship = trial["relationships"][rid]
        before = float(relationship[dimension])
        after = max(0.0, min(1.0, before + delta))
        relationship[dimension] = round(after, 4)
        change = {
            "relationship_id": rid,
            "dimension": dimension,
            "before": round(before, 4),
            "delta": round(relationship[dimension] - before, 4),
            "after": round(relationship[dimension], 4),
            "event_id": event_id,
        }
        relationship["last_event_id"] = event_id
        relationship["change_log"].append(change)
        changes.append(change)

    def _refresh_occupants(self) -> None:
        for location in self.state["locations"].values():
            location["occupants"] = []
        character = self.state["characters"][MAIN_ID]
        character_location = character["location_id"]
        self.state["locations"][character_location]["occupants"].append(MAIN_ID)
        for npc_id, npc in self.state["npcs"].items():
            location_id = npc["location_id"]
            if location_id:
                self.state["locations"][location_id]["occupants"].append(npc_id)

    def _error(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "code": code,
            "message": message,
            "details": details or {},
            "event": None,
            "replayed": False,
        }


DATED_SLOTS = {
    "2026-11-02",
    "2026-11-03",
    "2026-11-04",
    "2026-11-05",
    "2026-11-06",
    "2026-11-07",
    "2026-11-08",
}
