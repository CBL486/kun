"""主智能体结构化意图、候选和决策轨迹。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpg_sim.ids import canonical_json, stable_id


class IntentValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    action_type: str
    target_id: str
    parameters: dict[str, Any]
    score: float
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "score": round(self.score, 4),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class DecisionTrace:
    schema_version: str
    mode: str
    seed: int
    state_version: int
    tick_id: str
    candidates: list[Candidate]
    rejected_candidates: list[dict[str, Any]]
    selected_action: str | None
    selected_candidate_id: str | None
    model_used: bool
    degradation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "seed": self.seed,
            "state_version": self.state_version,
            "tick_id": self.tick_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "rejected_candidates": self.rejected_candidates,
            "selected_action": self.selected_action,
            "selected_candidate_id": self.selected_candidate_id,
            "model_used": self.model_used,
            "degradation_reason": self.degradation_reason,
        }


@dataclass(frozen=True)
class IntentProposal:
    schema_version: str
    operation_id: str
    tick_id: str
    character_id: str
    intent_id: str
    action_type: str
    target_id: str
    parameters: dict[str, Any]
    reason: str
    expected_outcome: str
    confidence: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IntentProposal":
        expected = {
            "schema_version",
            "operation_id",
            "tick_id",
            "character_id",
            "intent_id",
            "action_type",
            "target_id",
            "parameters",
            "reason",
            "expected_outcome",
            "confidence",
        }
        unknown = set(payload) - expected
        missing = expected - set(payload)
        if unknown:
            raise IntentValidationError(
                "invalid_schema",
                f"意图包含未声明字段：{sorted(unknown)}",
            )
        if missing:
            raise IntentValidationError(
                "invalid_schema",
                f"意图缺少字段：{sorted(missing)}",
            )
        proposal = cls(**payload)
        proposal.validate()
        return proposal

    @classmethod
    def from_candidate(
        cls,
        *,
        candidate: Candidate,
        operation_id: str,
        tick_id: str,
        character_id: str,
    ) -> "IntentProposal":
        intent_id = stable_id(
            "intent",
            [
                operation_id,
                tick_id,
                character_id,
                candidate.candidate_id,
            ],
        )
        return cls(
            schema_version="rpg-intent-v1",
            operation_id=operation_id,
            tick_id=tick_id,
            character_id=character_id,
            intent_id=intent_id,
            action_type=candidate.action_type,
            target_id=candidate.target_id,
            parameters=dict(candidate.parameters),
            reason="；".join(candidate.reason_codes),
            expected_outcome=EXPECTED_OUTCOMES.get(
                candidate.action_type, "完成一次受世界引擎约束的行动"
            ),
            confidence=round(max(0.0, min(1.0, candidate.score)), 4),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation_id": self.operation_id,
            "tick_id": self.tick_id,
            "character_id": self.character_id,
            "intent_id": self.intent_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "reason": self.reason,
            "expected_outcome": self.expected_outcome,
            "confidence": self.confidence,
        }

    def validate(self) -> None:
        expected = {
            "schema_version",
            "operation_id",
            "tick_id",
            "character_id",
            "intent_id",
            "action_type",
            "target_id",
            "parameters",
            "reason",
            "expected_outcome",
            "confidence",
        }
        if set(self.to_dict()) != expected:
            raise IntentValidationError("invalid_schema", "IntentProposal 字段不匹配")
        if self.schema_version != "rpg-intent-v1":
            raise IntentValidationError("invalid_schema", "Intent schema 版本无效")
        if not 0.0 <= self.confidence <= 1.0:
            raise IntentValidationError("invalid_schema", "confidence 越界")
        forbidden = {"event_id", "state_changes", "relationship_changes", "cost"}
        if forbidden & set(self.to_dict()):
            raise IntentValidationError("invalid_schema", "意图包含世界写入字段")


@dataclass(frozen=True)
class ActionIntent:
    schema_version: str
    action_id: str
    operation_id: str
    tick_id: str
    world_id: str
    character_id: str
    action_type: str
    target_id: str
    parameters: dict[str, Any]
    expected_state_version: int
    origin: str
    intent_nonce: str
    source_candidate_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "action_id": self.action_id,
            "operation_id": self.operation_id,
            "tick_id": self.tick_id,
            "world_id": self.world_id,
            "character_id": self.character_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "expected_state_version": self.expected_state_version,
            "origin": self.origin,
            "intent_nonce": self.intent_nonce,
        }
        if self.source_candidate_id:
            payload["source_candidate_id"] = self.source_candidate_id
        return payload

    def to_world_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("schema_version", None)
        return payload

    def fingerprint(self) -> str:
        return canonical_json(self.to_dict())


EXPECTED_OUTCOMES = {
    "move": "到达一个当前可达的公开地点。",
    "attend_class": "完成当前时段的课程安排。",
    "study": "推进校刊短文目标。",
    "talk": "在知识边界内完成一次公开交流。",
    "rest": "在安全地点恢复精力。",
    "eat": "完成一餐并降低饥饿。",
    "explore": "参加一个已注册公开活动。",
    "observe": "确认当前可见的公开细节。",
    "write_journal": "写下一篇只对自己可见的记录。",
}
