"""记忆作用域、记录和召回结果。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpg_sim.ids import digest

from .errors import ValidationError


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    world_id: str
    user_id: str
    character_id: str
    surface: str
    conversation_id: str | None

    def validate(self) -> None:
        for name in (
            "tenant_id",
            "world_id",
            "user_id",
            "character_id",
            "surface",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{name} 不能为空")
        if self.conversation_id is not None and not self.conversation_id.strip():
            raise ValidationError("conversation_id 必须是有效字符串或 None")

    @property
    def key(self) -> tuple[Any, ...]:
        self.validate()
        return (
            self.tenant_id,
            self.world_id,
            self.user_id,
            self.character_id,
            self.surface,
            self.conversation_id,
        )

    @property
    def conversation_key(self) -> str:
        return self.conversation_id or "__null__"

    @property
    def scope_hash(self) -> str:
        return digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "world_id": self.world_id,
            "user_id": self.user_id,
            "character_id": self.character_id,
            "surface": self.surface,
            "conversation_id": self.conversation_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Scope":
        expected = {
            "tenant_id",
            "world_id",
            "user_id",
            "character_id",
            "surface",
            "conversation_id",
        }
        if set(payload) != expected:
            raise ValidationError("Scope 字段不完整或包含未知字段")
        scope = cls(**payload)
        scope.validate()
        return scope


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    scope: Scope
    kind: str
    source: str
    content: str
    importance: float
    emotional_weight: float
    confidence: float
    strength: float
    scene_tags: list[str]
    created_at: str
    last_accessed_at: str | None
    last_strength_update: str
    access_count: int
    restated_count: int
    locked: bool
    state: str
    source_event_id: str
    dedupe_key: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "scope": self.scope.to_dict(),
            "kind": self.kind,
            "source": self.source,
            "content": self.content,
            "importance": self.importance,
            "emotional_weight": self.emotional_weight,
            "confidence": self.confidence,
            "strength": self.strength,
            "scene_tags": self.scene_tags,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "last_strength_update": self.last_strength_update,
            "access_count": self.access_count,
            "restated_count": self.restated_count,
            "locked": self.locked,
            "state": self.state,
            "source_event_id": self.source_event_id,
            "dedupe_key": self.dedupe_key,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RecallResult:
    memory: MemoryRecord
    score: float
    score_breakdown: dict[str, float]
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory": self.memory.to_dict(),
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "reason_codes": self.reason_codes,
        }
