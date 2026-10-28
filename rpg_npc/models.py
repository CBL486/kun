"""NPC 运行时数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RuntimeState(StrEnum):
    SCHEDULED = "SCHEDULED"
    COMMUTING = "COMMUTING"
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    CLOSED = "CLOSED"
    ASLEEP = "ASLEEP"
    REACTION_PENDING = "REACTION_PENDING"
    INTERACTION_COOLDOWN = "INTERACTION_COOLDOWN"


@dataclass(frozen=True)
class ScheduleState:
    slot_key: str
    time: str
    location_id: str | None
    runtime_state: RuntimeState

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_key": self.slot_key,
            "time": self.time,
            "location_id": self.location_id,
            "runtime_state": self.runtime_state.value,
        }


@dataclass(frozen=True)
class ReactionTemplate:
    template_id: str
    npc_id: str
    intent: str
    utterance: str
    event_template_ids: tuple[str, ...] = ()
    event_types: tuple[str, ...] = ()
    required_fact_ids: tuple[str, ...] = ()
    forbidden_fact_ids: tuple[str, ...] = ()
    relationship_min: dict[str, float] = field(default_factory=dict)
    relationship_delta: dict[str, float] = field(default_factory=dict)
    priority: int = 0
    repeat_policy: str = "once_per_event"
    content_review_status: str = "approved"


@dataclass(frozen=True)
class RelationshipProposal:
    relationship_id: str
    npc_id: str
    source_event_id: str
    dimension: str
    delta: float
    reason_code: str

    def validate(self) -> None:
        if not self.source_event_id.startswith("evt_"):
            raise ValueError("relationship_event_required")
        if self.dimension not in {"familiarity", "trust", "tension"}:
            raise ValueError("invalid_relationship_dimension")
        if abs(self.delta) > 0.08:
            raise ValueError("relationship_delta_exceeds_limit")

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "npc_id": self.npc_id,
            "source_event_id": self.source_event_id,
            "dimension": self.dimension,
            "delta": self.delta,
            "reason_code": self.reason_code,
        }


@dataclass
class NPCReaction:
    npc_id: str
    source_event_id: str
    template_id: str
    utterance: str
    knowledge_basis: list[str]
    relationship_proposals: list[RelationshipProposal]
    memory_slot_written: str | None
    review_status: str = "approved"
    model_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "rpg-npc-reaction-v1",
            "npc_id": self.npc_id,
            "response_to_event_id": self.source_event_id,
            "template_id": self.template_id,
            "utterance": self.utterance,
            "knowledge_basis": self.knowledge_basis,
            "relationship_proposals": [
                proposal.to_dict() for proposal in self.relationship_proposals
            ],
            "memory_slot_written": self.memory_slot_written,
            "review_status": self.review_status,
            "model_used": self.model_used,
        }


@dataclass
class ReactionOutcome:
    status: str
    code: str | None
    reaction: NPCReaction | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "code": self.code,
            "reaction": self.reaction.to_dict() if self.reaction else None,
            "message": self.message,
        }
