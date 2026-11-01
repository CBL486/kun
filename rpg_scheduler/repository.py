"""Persistent task queue with idempotency, leases and recovery."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Engine, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rpg_orm.migrations import migrate
from rpg_orm.models import ScheduledTaskRow

from .errors import SchedulerError
from .locks import advisory_lock
from .models import ScheduleSpec, TaskStatus, require_aware_utc


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return _aware(value).isoformat().replace("+00:00", "Z") if value else None


class SchedulerRepository:
    def __init__(self, engine: Engine, *, migrate_schema: bool = True):
        self.engine = engine
        if migrate_schema:
            migrate(engine)

    def enqueue(self, spec: ScheduleSpec) -> dict[str, Any]:
        with advisory_lock(
            self.engine,
            f"enqueue:{spec.operation_id}",
        ) as acquired:
            if not acquired:
                raise SchedulerError(
                    "scheduler_busy",
                    "当前 operation 正在被其他调度进程处理",
                )
            try:
                with Session(self.engine) as session, session.begin():
                    existing = session.get(ScheduledTaskRow, spec.task_id)
                    if existing:
                        if existing.fingerprint != spec.fingerprint:
                            raise SchedulerError(
                                "duplicate_operation",
                                "同一 operation_id 的任务内容不一致",
                            )
                        return {**self._row(existing), "replayed": True}
                    now = spec.available_at.astimezone(timezone.utc)
                    row = ScheduledTaskRow(
                        task_id=spec.task_id,
                        kind=spec.kind,
                        operation_id=spec.operation_id,
                        fingerprint=spec.fingerprint,
                        payload=spec.payload,
                        status=TaskStatus.PENDING.value,
                        priority=spec.priority,
                        available_at=now,
                        lease_owner=None,
                        lease_expires_at=None,
                        attempts=0,
                        max_attempts=spec.max_attempts,
                        timeout_seconds=spec.timeout_seconds,
                        last_error=None,
                        result=None,
                        created_at=now,
                        updated_at=now,
                        completed_at=None,
                    )
                    session.add(row)
                    session.flush()
                    return {**self._row(row), "replayed": False}
            except IntegrityError as error:
                raise SchedulerError(
                    "duplicate_operation",
                    "任务唯一约束冲突",
                ) from error

    def claim_next(
        self,
        *,
        worker_id: str,
        now: datetime,
        lease_seconds: float = 30.0,
        kind: str | None = None,
    ) -> dict[str, Any] | None:
        now = require_aware_utc(now)
        if lease_seconds <= 0:
            raise ValueError("lease_seconds 必须大于 0")
        with advisory_lock(self.engine, "claim-next") as acquired:
            if not acquired:
                return None
            with Session(self.engine) as session, session.begin():
                query = select(ScheduledTaskRow).where(
                    or_(
                        (
                            (ScheduledTaskRow.status == TaskStatus.PENDING.value)
                            & (ScheduledTaskRow.available_at <= now)
                        ),
                        (
                            (ScheduledTaskRow.status == TaskStatus.LEASED.value)
                            & (ScheduledTaskRow.lease_expires_at <= now)
                        ),
                    )
                )
                if kind:
                    query = query.where(ScheduledTaskRow.kind == kind)
                query = (
                    query.order_by(
                        ScheduledTaskRow.priority.desc(),
                        ScheduledTaskRow.available_at,
                        ScheduledTaskRow.created_at,
                        ScheduledTaskRow.task_id,
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                row = session.scalar(query)
                if row is None:
                    return None
                row.status = TaskStatus.LEASED.value
                row.lease_owner = worker_id
                row.lease_expires_at = now + timedelta(seconds=lease_seconds)
                row.attempts += 1
                row.updated_at = now
                session.flush()
                return self._row(row)

    def succeed(
        self,
        *,
        task_id: str,
        worker_id: str,
        result: dict[str, Any] | None,
        now: datetime,
    ) -> dict[str, Any]:
        now = require_aware_utc(now)
        with Session(self.engine) as session, session.begin():
            row = session.scalar(
                select(ScheduledTaskRow)
                .where(ScheduledTaskRow.task_id == task_id)
                .with_for_update()
            )
            self._assert_lease(row, worker_id, now)
            row.status = TaskStatus.SUCCEEDED.value
            row.result = result
            row.last_error = None
            row.lease_owner = None
            row.lease_expires_at = None
            row.updated_at = now
            row.completed_at = now
            session.flush()
            return self._row(row)

    def fail(
        self,
        *,
        task_id: str,
        worker_id: str,
        error: str,
        now: datetime,
        retry_after_seconds: float | None = None,
    ) -> dict[str, Any]:
        now = require_aware_utc(now)
        with Session(self.engine) as session, session.begin():
            row = session.scalar(
                select(ScheduledTaskRow)
                .where(ScheduledTaskRow.task_id == task_id)
                .with_for_update()
            )
            self._assert_lease(row, worker_id, now)
            row.last_error = error[:500]
            row.lease_owner = None
            row.lease_expires_at = None
            row.updated_at = now
            if row.attempts >= row.max_attempts:
                row.status = TaskStatus.DEAD_LETTER.value
                row.completed_at = now
            else:
                delay = (
                    retry_after_seconds
                    if retry_after_seconds is not None
                    else min(60.0, 2.0 ** (row.attempts - 1))
                )
                row.status = TaskStatus.PENDING.value
                row.available_at = now + timedelta(seconds=max(0.0, delay))
            session.flush()
            return self._row(row)

    def recover_expired(self, *, now: datetime) -> dict[str, int]:
        now = require_aware_utc(now)
        released = 0
        dead_lettered = 0
        with Session(self.engine) as session, session.begin():
            rows = session.scalars(
                select(ScheduledTaskRow)
                .where(
                    ScheduledTaskRow.status == TaskStatus.LEASED.value,
                    ScheduledTaskRow.lease_expires_at <= now,
                )
                .with_for_update(skip_locked=True)
            ).all()
            for row in rows:
                row.lease_owner = None
                row.lease_expires_at = None
                row.updated_at = now
                if row.attempts >= row.max_attempts:
                    row.status = TaskStatus.DEAD_LETTER.value
                    row.completed_at = now
                    dead_lettered += 1
                else:
                    row.status = TaskStatus.PENDING.value
                    released += 1
        return {"released": released, "dead_lettered": dead_lettered}

    def backlog(self, *, now: datetime) -> dict[str, Any]:
        now = require_aware_utc(now)
        with Session(self.engine) as session:
            pending_due = session.scalar(
                select(func.count())
                .select_from(ScheduledTaskRow)
                .where(
                    ScheduledTaskRow.status == TaskStatus.PENDING.value,
                    ScheduledTaskRow.available_at <= now,
                )
            )
            delayed = session.scalar(
                select(func.count())
                .select_from(ScheduledTaskRow)
                .where(
                    ScheduledTaskRow.status == TaskStatus.PENDING.value,
                    ScheduledTaskRow.available_at > now,
                )
            )
            leased = session.scalar(
                select(func.count())
                .select_from(ScheduledTaskRow)
                .where(ScheduledTaskRow.status == TaskStatus.LEASED.value)
            )
            expired = session.scalar(
                select(func.count())
                .select_from(ScheduledTaskRow)
                .where(
                    ScheduledTaskRow.status == TaskStatus.LEASED.value,
                    ScheduledTaskRow.lease_expires_at <= now,
                )
            )
            oldest = session.scalar(
                select(func.min(ScheduledTaskRow.available_at)).where(
                    ScheduledTaskRow.status == TaskStatus.PENDING.value
                )
            )
        oldest_delay = (
            max(0.0, (now - _aware(oldest)).total_seconds())
            if oldest
            else 0.0
        )
        return {
            "pending_due": int(pending_due or 0),
            "delayed": int(delayed or 0),
            "leased": int(leased or 0),
            "expired_leases": int(expired or 0),
            "oldest_pending_seconds": round(oldest_delay, 3),
        }

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(ScheduledTaskRow, task_id)
            return self._row(row) if row else None

    def get_by_operation(self, operation_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.scalar(
                select(ScheduledTaskRow).where(
                    ScheduledTaskRow.operation_id == operation_id
                )
            )
            return self._row(row) if row else None

    def list_tasks(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(ScheduledTaskRow)
            if status:
                query = query.where(ScheduledTaskRow.status == status)
            rows = session.scalars(
                query.order_by(
                    ScheduledTaskRow.available_at,
                    ScheduledTaskRow.task_id,
                ).limit(limit)
            ).all()
            return [self._row(row) for row in rows]

    @staticmethod
    def _assert_lease(
        row: ScheduledTaskRow | None,
        worker_id: str,
        now: datetime,
    ) -> None:
        if row is None:
            raise SchedulerError("task_unknown", "任务不存在")
        if (
            row.status != TaskStatus.LEASED.value
            or row.lease_owner != worker_id
            or row.lease_expires_at is None
            or _aware(row.lease_expires_at) <= now
        ):
            raise SchedulerError("lease_lost", "任务租约已失效")

    @staticmethod
    def _row(row: ScheduledTaskRow) -> dict[str, Any]:
        return {
            "task_id": row.task_id,
            "kind": row.kind,
            "operation_id": row.operation_id,
            "payload": row.payload,
            "status": row.status,
            "priority": row.priority,
            "available_at": _iso(row.available_at),
            "lease_owner": row.lease_owner,
            "lease_expires_at": _iso(row.lease_expires_at),
            "attempts": row.attempts,
            "max_attempts": row.max_attempts,
            "timeout_seconds": row.timeout_seconds,
            "last_error": row.last_error,
            "result": row.result,
            "created_at": _iso(row.created_at),
            "updated_at": _iso(row.updated_at),
            "completed_at": _iso(row.completed_at),
        }
