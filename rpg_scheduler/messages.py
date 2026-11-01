"""Persistent observer-message queue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rpg_orm.migrations import migrate
from rpg_orm.models import ObserverMessageRow

from .errors import SchedulerError
from .models import require_aware_utc


class PersistentMessageQueue:
    def __init__(self, engine: Engine, *, migrate_schema: bool = True):
        self.engine = engine
        if migrate_schema:
            migrate(engine)

    def enqueue(
        self,
        *,
        message_id: str,
        content: str,
        created_at: datetime,
    ) -> dict[str, Any]:
        created_at = require_aware_utc(created_at)
        try:
            with Session(self.engine) as session, session.begin():
                existing = session.get(ObserverMessageRow, message_id)
                if existing:
                    if existing.content != content:
                        raise SchedulerError(
                            "duplicate_message",
                            "同一 message_id 的内容不一致",
                        )
                    return {**self._row(existing), "replayed": True}
                row = ObserverMessageRow(
                    message_id=message_id,
                    content=content,
                    status="queued",
                    created_at=created_at,
                    updated_at=created_at,
                )
                session.add(row)
                session.flush()
                return {**self._row(row), "replayed": False}
        except IntegrityError as error:
            raise SchedulerError(
                "duplicate_message",
                "留言唯一约束冲突",
            ) from error

    def list_messages(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(ObserverMessageRow)
                .order_by(
                    ObserverMessageRow.created_at,
                    ObserverMessageRow.message_id,
                )
                .limit(limit)
            ).all()
            return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: ObserverMessageRow) -> dict[str, Any]:
        return {
            "message_id": row.message_id,
            "message": row.content,
            "status": row.status,
            "created_at": row.created_at.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
