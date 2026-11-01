"""Scheduler service that executes leased tasks with bounded time."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable

from .models import ScheduleSpec, TaskExecution, utc_now
from .repository import SchedulerRepository


TaskHandler = Callable[[dict[str, Any]], dict[str, Any] | None]


class SchedulerService:
    def __init__(self, repository: SchedulerRepository):
        self.repository = repository

    def schedule(self, spec: ScheduleSpec) -> TaskExecution:
        row = self.repository.enqueue(spec)
        return TaskExecution(
            status="scheduled",
            task_id=row["task_id"],
            operation_id=row["operation_id"],
            replayed=row["replayed"],
        )

    def run_next(
        self,
        *,
        worker_id: str,
        handlers: dict[str, TaskHandler],
        lease_seconds: float = 30.0,
        now: datetime | None = None,
    ) -> TaskExecution:
        current = now or utc_now()
        self.repository.recover_expired(now=current)
        task = self.repository.claim_next(
            worker_id=worker_id,
            now=current,
            lease_seconds=lease_seconds,
        )
        if task is None:
            return TaskExecution(status="idle")

        handler = handlers.get(task["kind"])
        if handler is None:
            row = self.repository.fail(
                task_id=task["task_id"],
                worker_id=worker_id,
                error="handler_missing",
                now=current,
            )
            return TaskExecution(
                status=row["status"],
                task_id=row["task_id"],
                operation_id=row["operation_id"],
                error=row["last_error"],
            )

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(handler, task)
        try:
            result = future.result(timeout=task["timeout_seconds"])
        except Exception as error:
            executor.shutdown(wait=False, cancel_futures=True)
            row = self.repository.fail(
                task_id=task["task_id"],
                worker_id=worker_id,
                error=type(error).__name__,
                now=current,
            )
            return TaskExecution(
                status=row["status"],
                task_id=row["task_id"],
                operation_id=row["operation_id"],
                error=row["last_error"],
            )
        executor.shutdown(wait=True)
        row = self.repository.succeed(
            task_id=task["task_id"],
            worker_id=worker_id,
            result=result,
            now=current,
        )
        return TaskExecution(
            status=row["status"],
            task_id=row["task_id"],
            operation_id=row["operation_id"],
            result=row["result"],
        )

    def run_due(
        self,
        *,
        worker_id: str,
        handlers: dict[str, TaskHandler],
        limit: int,
        lease_seconds: float = 30.0,
    ) -> list[TaskExecution]:
        outcomes = []
        for _ in range(limit):
            outcome = self.run_next(
                worker_id=worker_id,
                handlers=handlers,
                lease_seconds=lease_seconds,
            )
            if outcome.status == "idle":
                break
            outcomes.append(outcome)
        return outcomes
