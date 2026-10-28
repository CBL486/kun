"""NPC 日程、知识、反应和有限记忆运行时。"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

from rpg_sim.ids import relationship_id, stable_id
from rpg_sim.scenario import initial_world

from .content import load_content_packs
from .models import (
    NPCReaction,
    ReactionOutcome,
    RelationshipProposal,
    RuntimeState,
)
from .schedules import SLOT_TIMES, can_transition, day_schedule, schedule_state
from .templates import REACTION_TEMPLATES, UNKNOWN_RESPONSES


class NPCScopeError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class NPCMemoryFull(RuntimeError):
    code = "npc_memory_full"


class NPCRuntime:
    max_memory_slots = 8

    def __init__(self):
        world = initial_world()
        self.npcs = copy.deepcopy(world["npcs"])
        self.relationships = copy.deepcopy(world["relationships"])
        self.templates = {template.template_id: template for template in REACTION_TEMPLATES}
        self.content_packs = load_content_packs()
        self.reaction_records: list[NPCReaction] = []
        self.used_reactions: set[tuple[str, str, str]] = set()
        self.relationship_applied: set[tuple[str, str]] = set()
        self.utterance_history: list[dict[str, str]] = []
        self.current_date: str | None = None
        self.current_time: str | None = None
        self.current_slot: str | None = None

    def set_time(self, world_date: str, time_text: str, slot_key: str) -> None:
        self.current_date = world_date
        self.current_time = time_text
        self.current_slot = slot_key
        for npc_id, npc in self.npcs.items():
            schedule = schedule_state(npc_id, world_date, time_text, slot_key)
            self._apply_schedule(npc, schedule)

    def run_day(self, world_date: str) -> dict[str, dict[str, dict[str, Any]]]:
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for npc_id in sorted(self.npcs):
            schedule = day_schedule(npc_id, world_date)
            result[npc_id] = {
                slot_key: state.to_dict()
                for slot_key, state in schedule.items()
            }
        return result

    def context(self, npc_id: str, event: dict[str, Any]) -> dict[str, Any]:
        npc = self._npc(npc_id)
        if event.get("visibility") == "internal":
            raise NPCScopeError(
                "npc_scope_violation",
                "NPC 不能读取 internal 事件",
            )
        visible = (
            npc["location_id"] == event.get("location_id")
            and (
                event.get("visibility") == "user_visible"
                or npc_id in event.get("participants", [])
            )
        )
        return {
            "npc_id": npc_id,
            "world_date": self.current_date or event.get("world_date"),
            "slot_key": self.current_slot,
            "location_id": npc["location_id"],
            "runtime_state": npc["runtime_state"].value,
            "visible_character_ids": (
                list(event.get("participants", [])) if visible else []
            ),
            "visible_events": (
                [
                    {
                        "event_id": event.get("event_id"),
                        "summary": event.get("summary", ""),
                    }
                ]
                if visible
                else []
            ),
            "known_fact_ids": list(npc["knowledge_ids"]),
            "memory_slots": copy.deepcopy(npc["memory_slots"]),
            "relationship": self._relationship_snapshot(npc_id),
        }

    def answer(self, npc_id: str, fact_id: str) -> str:
        npc = self._npc(npc_id)
        if fact_id not in npc["knowledge_ids"]:
            return UNKNOWN_RESPONSES["unknown_event"]
        answers = {
            "fact_canteen_public_menu": "今天菜单换了，售罄情况以窗口为准。",
            "fact_layout_brief": "版面要求以公开简报为准，重点和标题都要保留。",
            "fact_submission_floor_public": "提交楼层以公开通知为准。",
            "fact_photo_activity": "拍摄用途和范围需要先得到明确同意。",
            "fact_public_cleanup": "河边清理活动在公开集合点集合。",
        }
        return answers.get(
            fact_id,
            UNKNOWN_RESPONSES["missing_template"],
        )

    def refuse(self, reason: str = "content_scope") -> str:
        return UNKNOWN_RESPONSES.get(
            reason,
            UNKNOWN_RESPONSES["missing_template"],
        )

    def react_to_event(self, event: dict[str, Any]) -> list[ReactionOutcome]:
        """按固定优先级让至多两名在场 NPC 对同一正式事件反应。"""
        if event.get("visibility") == "internal":
            raise NPCScopeError(
                "npc_scope_violation",
                "NPC 不能对 internal 事件作出反应",
            )
        ranked = []
        for npc_id, npc in self.npcs.items():
            if npc["runtime_state"] != RuntimeState.AVAILABLE:
                continue
            if npc["location_id"] != event.get("location_id"):
                continue
            matching = self._matching_templates(npc_id, event)
            if not matching:
                continue
            best = sorted(
                matching,
                key=lambda item: (-item.priority, item.template_id),
            )[0]
            ranked.append((best.priority, best.template_id, npc_id))
        selected = [
            npc_id
            for _, _, npc_id in sorted(ranked, key=lambda item: (-item[0], item[1], item[2]))[:2]
        ]
        return [self.react(npc_id, event) for npc_id in selected]

    def react(self, npc_id: str, event: dict[str, Any]) -> ReactionOutcome:
        npc = self._npc(npc_id)
        if event.get("visibility") == "internal":
            raise NPCScopeError(
                "npc_scope_violation",
                "NPC 不能对 internal 事件作出反应",
            )
        if npc["runtime_state"] != RuntimeState.AVAILABLE:
            return ReactionOutcome(
                status="unavailable",
                code="npc_unavailable",
                reaction=None,
                message="NPC 当前不可互动",
            )
        if npc["location_id"] != event.get("location_id"):
            return ReactionOutcome(
                status="not_present",
                code="npc_not_present",
                reaction=None,
                message="NPC 不在事件地点",
            )
        if (
            event.get("visibility") == "character_visible"
            and npc_id not in event.get("participants", [])
        ):
            return ReactionOutcome(
                status="not_visible",
                code="npc_scope_violation",
                reaction=None,
                message="NPC 不是该事件的直接参与者",
            )

        candidates = self._matching_templates(npc_id, event)
        if not candidates:
            return ReactionOutcome(
                status="fallback",
                code="npc_template_missing",
                reaction=None,
                message=UNKNOWN_RESPONSES["missing_template"],
            )
        template = sorted(
            candidates,
            key=lambda item: (-item.priority, item.template_id),
        )[0]
        dedupe_key = (event["event_id"], npc_id, template.template_id)
        if dedupe_key in self.used_reactions:
            return ReactionOutcome(
                status="repeat_blocked",
                code="npc_repeat_blocked",
                reaction=None,
                message="同一事件和模板已经反应过",
            )
        if self._utterance_in_cooldown(npc_id, template.utterance, event):
            return ReactionOutcome(
                status="fallback",
                code="npc_repeat_blocked",
                reaction=None,
                message=UNKNOWN_RESPONSES["missing_template"],
            )

        proposals = [
            RelationshipProposal(
                relationship_id=relationship_id("char_lin_cheng", npc_id),
                npc_id=npc_id,
                source_event_id=event["event_id"],
                dimension=dimension,
                delta=delta,
                reason_code=template.intent,
            )
            for dimension, delta in template.relationship_delta.items()
        ]
        for proposal in proposals:
            proposal.validate()
        memory_slot_id = self._write_memory_slot(
            npc_id=npc_id,
            event=event,
            template=template,
        )
        reaction = NPCReaction(
            npc_id=npc_id,
            source_event_id=event["event_id"],
            template_id=template.template_id,
            utterance=template.utterance,
            knowledge_basis=list(template.required_fact_ids),
            relationship_proposals=proposals,
            memory_slot_written=memory_slot_id,
            review_status=template.content_review_status,
        )
        self.used_reactions.add(dedupe_key)
        self.reaction_records.append(reaction)
        self.utterance_history.append(
            {
                "npc_id": npc_id,
                "utterance": template.utterance,
                "occurred_at": event.get(
                    "occurred_at",
                    f"{self.current_date}T{self.current_time}:00+08:00",
                ),
            }
        )
        return ReactionOutcome(
            status="approved",
            code=None,
            reaction=reaction,
            message="NPC 反应候选已通过模板校验",
        )

    def apply_relationship_proposal(
        self,
        proposal: RelationshipProposal,
    ) -> dict[str, Any]:
        proposal.validate()
        key = (
            proposal.relationship_id,
            proposal.source_event_id,
            proposal.dimension,
        )
        if key in self.relationship_applied:
            return {
                "status": "replayed",
                "event_id": proposal.source_event_id,
                "relationship": self._relationship_snapshot(proposal.npc_id),
            }
        relationship = self.relationships.get(proposal.relationship_id)
        if not relationship:
            raise KeyError("unknown_relationship")
        before = float(relationship[proposal.dimension])
        after = max(0.0, min(1.0, before + proposal.delta))
        relationship[proposal.dimension] = round(after, 4)
        relationship["last_event_id"] = proposal.source_event_id
        change = {
            "relationship_id": proposal.relationship_id,
            "dimension": proposal.dimension,
            "before": round(before, 4),
            "delta": round(relationship[proposal.dimension] - before, 4),
            "after": round(relationship[proposal.dimension], 4),
            "event_id": proposal.source_event_id,
        }
        relationship["change_log"].append(change)
        self.relationship_applied.add(key)
        return {
            "status": "applied",
            "event_id": proposal.source_event_id,
            "change": change,
            "relationship": self._relationship_snapshot(proposal.npc_id),
        }

    def memory_slots(self, npc_id: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._npc(npc_id)["memory_slots"])

    def _matching_templates(self, npc_id: str, event: dict[str, Any]) -> list[Any]:
        npc = self._npc(npc_id)
        relationship = self._relationship_snapshot(npc_id)
        result = []
        for template in self.templates.values():
            if template.npc_id != npc_id or template.content_review_status != "approved":
                continue
            if (
                template.event_template_ids
                and event.get("template_id") not in template.event_template_ids
            ):
                continue
            if template.event_types and event.get("event_type") not in template.event_types:
                continue
            if not set(template.required_fact_ids) <= set(npc["knowledge_ids"]):
                continue
            if set(template.forbidden_fact_ids) & set(npc["knowledge_ids"]):
                continue
            if any(
                relationship.get(dimension, 0.0) < minimum
                for dimension, minimum in template.relationship_min.items()
            ):
                continue
            result.append(template)
        return result

    def _write_memory_slot(
        self,
        *,
        npc_id: str,
        event: dict[str, Any],
        template: Any,
    ) -> str:
        npc = self._npc(npc_id)
        for slot in npc["memory_slots"]:
            if (
                slot["source_event_id"] == event["event_id"]
                and slot["content_key"] == template.template_id
            ):
                return slot["slot_id"]
        if len(npc["memory_slots"]) >= self.max_memory_slots:
            evictable = [
                slot for slot in npc["memory_slots"] if not slot["important"]
            ]
            if not evictable:
                raise NPCMemoryFull("NPC 重要记忆槽已满")
            victim = min(
                evictable,
                key=lambda slot: (
                    slot["expires_on"],
                    slot["last_used_at"],
                    slot["slot_id"],
                ),
            )
            npc["memory_slots"].remove(victim)
        slot_id = stable_id("slot", [npc_id, event["event_id"], template.template_id])
        npc["memory_slots"].append(
            {
                "slot_id": slot_id,
                "kind": "completed_exchange",
                "content_key": template.template_id,
                "source_event_id": event["event_id"],
                "important": bool(event.get("important")) or template.priority >= 80,
                "expires_on": self.current_date or event.get("world_date"),
                "last_used_at": event.get("occurred_at"),
            }
        )
        return slot_id

    def _utterance_in_cooldown(
        self,
        npc_id: str,
        utterance: str,
        event: dict[str, Any],
    ) -> bool:
        occurred_at = datetime.fromisoformat(
            event.get(
                "occurred_at",
                f"{self.current_date}T{self.current_time}:00+08:00",
            )
        )
        for history in self.utterance_history:
            if history["npc_id"] != npc_id or history["utterance"] != utterance:
                continue
            previous = datetime.fromisoformat(history["occurred_at"])
            if abs((occurred_at - previous).total_seconds()) < 48 * 3600:
                return True
        return False

    def _apply_schedule(self, npc: dict[str, Any], schedule: Any) -> None:
        current = npc["runtime_state"]
        if isinstance(current, str):
            try:
                current = RuntimeState(current.upper())
            except ValueError:
                current = RuntimeState.SCHEDULED
        target = schedule.runtime_state
        if can_transition(current, target):
            npc["runtime_state"] = target
        else:
            npc["runtime_state"] = (
                RuntimeState.SCHEDULED
                if target != RuntimeState.ASLEEP
                else RuntimeState.CLOSED
            )
        npc["location_id"] = schedule.location_id

    def _relationship_snapshot(self, npc_id: str) -> dict[str, float]:
        rid = relationship_id("char_lin_cheng", npc_id)
        relationship = self.relationships[rid]
        return {
            "familiarity": relationship["familiarity"],
            "trust": relationship["trust"],
            "tension": relationship["tension"],
        }

    def _npc(self, npc_id: str) -> dict[str, Any]:
        try:
            return self.npcs[npc_id]
        except KeyError as error:
            raise KeyError("npc_unknown") from error
