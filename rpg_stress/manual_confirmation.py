"""Explicit manual confirmation for high-risk operations."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from rpg_sim.ids import stable_id


class ConfirmationRequired(RuntimeError):
    def __init__(self, operation_id: str, status: str):
        super().__init__(f"{operation_id} 需要人工确认，当前状态：{status}")
        self.code = "manual_confirmation_required"
        self.operation_id = operation_id
        self.status = status


@dataclass(frozen=True)
class ConfirmationRequest:
    operation_id: str
    reason_code: str
    status: str = "pending"
    reviewer: str | None = None


class ManualConfirmationGate:
    def __init__(self):
        self._lock = threading.RLock()
        self._requests: dict[str, ConfirmationRequest] = {}

    def request(self, *, operation_id: str, reason_code: str) -> ConfirmationRequest:
        with self._lock:
            existing = self._requests.get(operation_id)
            if existing:
                if existing.reason_code != reason_code:
                    raise ValueError("同一 operation 的确认理由不一致")
                return existing
            item = ConfirmationRequest(
                operation_id=stable_id("confirm", [operation_id]),
                reason_code=reason_code,
            )
            self._requests[operation_id] = item
            return item

    def decide(
        self,
        *,
        operation_id: str,
        approved: bool,
        reviewer: str,
    ) -> ConfirmationRequest:
        with self._lock:
            existing = self._requests.get(operation_id)
            if existing is None:
                raise KeyError(operation_id)
            if existing.status != "pending":
                raise ValueError("人工确认已经有结论")
            item = ConfirmationRequest(
                operation_id=stable_id("confirm", [operation_id]),
                reason_code=existing.reason_code,
                status="approved" if approved else "rejected",
                reviewer=reviewer,
            )
            self._requests[operation_id] = item
            return item

    def execute(
        self,
        *,
        operation_id: str,
        action: Callable[[], object],
    ) -> object:
        with self._lock:
            existing = self._requests.get(operation_id)
            status = existing.status if existing else "missing"
        if existing is None or status != "approved":
            raise ConfirmationRequired(operation_id, status)
        return action()
