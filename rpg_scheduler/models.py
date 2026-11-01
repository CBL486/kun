"""Immutable scheduler inputs and execution results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from rpg_sim.ids import canonical_json, stable_id


class TaskStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("调度时间必须包含时区")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class ScheduleSpec:
    kind: str
    operation_id: str
    payload: dict[str, Any]
    available_at: datetime = field(default_factory=utc_now)
    priority: int = 0
    max_attempts: int = 3
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("任务类型不能为空")
        if not self.operation_id.strip():
            raise ValueError("operation_id 不能为空")
        if self.max_attempts < 1:
            raise ValueError("max_attempts 必须大于 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds 必须大于 0")
        require_aware_utc(self.available_at)

    @property
    def task_id(self) -> str:
        return stable_id("task", [self.operation_id])

    @property
    def fingerprint(self) -> str:
        return canonical_json(
            {
                "kind": self.kind,
                "operation_id": self.operation_id,
                "payload": self.payload,
                "priority": self.priority,
                "max_attempts": self.max_attempts,
                "timeout_seconds": self.timeout_seconds,
            }
        )


@dataclass(frozen=True)
class TaskExecution:
    status: str
    task_id: str | None = None
    operation_id: str | None = None
    replayed: bool = False
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "task_id": self.task_id,
            "operation_id": self.operation_id,
            "replayed": self.replayed,
            "result": self.result,
            "error": self.error,
        }
