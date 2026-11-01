"""Persistent operation cache and deduplicated usage ledger."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from rpg_orm.migrations import migrate
from rpg_orm.models import LlmOperationRow, LlmUsageRow
from rpg_sim.ids import stable_id

from .models import BudgetSnapshot


CHINA_TIMEZONE = timezone(timedelta(hours=8))


class LlmRepository:
    def __init__(self, engine: Engine, *, migrate_schema: bool = True):
        self.engine = engine
        if migrate_schema:
            migrate(engine)

    def get_operation(self, operation_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(LlmOperationRow, operation_id)
            if not row:
                return None
            return {
                "operation_id": row.operation_id,
                "request_hash": row.request_hash,
                "template_id": row.template_id,
                "template_version": row.template_version,
                "status": row.status,
                "result": row.result,
                "review_status": row.review_status,
                "run_mode": row.run_mode,
                "provider": row.provider,
                "model": row.model,
                "attempts": row.attempts,
                "degradation_reason": row.degradation_reason,
                "prompt_sha256": row.prompt_sha256,
                "redacted_prompt_preview": row.redacted_prompt_preview,
                "latency_ms": row.latency_ms,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

    def save_operation(
        self,
        *,
        operation_id: str,
        request_hash: str,
        template_id: str,
        template_version: str,
        status: str,
        result: dict[str, Any],
        review_status: str,
        run_mode: str,
        provider: str | None,
        model: str | None,
        attempts: int,
        degradation_reason: str | None,
        prompt_sha256: str,
        redacted_prompt_preview: str,
        latency_ms: float,
        now: datetime,
    ) -> None:
        with Session(self.engine) as session, session.begin():
            row = LlmOperationRow(
                operation_id=operation_id,
                request_hash=request_hash,
                template_id=template_id,
                template_version=template_version,
                status=status,
                result=result,
                review_status=review_status,
                run_mode=run_mode,
                provider=provider,
                model=model,
                attempts=attempts,
                degradation_reason=degradation_reason,
                prompt_sha256=prompt_sha256,
                redacted_prompt_preview=redacted_prompt_preview,
                latency_ms=latency_ms,
                created_at=now,
                updated_at=now,
            )
            session.add(row)

    def record_usage(
        self,
        *,
        operation_id: str,
        attempt_id: str,
        provider_request_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        review_calls: int,
        cost_cny: Decimal,
        price_version: str,
        now: datetime,
    ) -> bool:
        usage_id = stable_id(
            "usage",
            [operation_id, provider_request_id],
        )
        with Session(self.engine) as session, session.begin():
            existing = session.get(LlmUsageRow, usage_id)
            if existing:
                return False
            session.add(
                LlmUsageRow(
                    usage_id=usage_id,
                    operation_id=operation_id,
                    attempt_id=attempt_id,
                    provider_request_id=provider_request_id,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    review_calls=review_calls,
                    cost_cny=cost_cny,
                    price_version=price_version,
                    created_at=now,
                )
            )
            return True

    def usage_snapshot(self, budget_date: str) -> BudgetSnapshot:
        day = date.fromisoformat(budget_date)
        start = datetime.combine(day, time.min, tzinfo=CHINA_TIMEZONE).astimezone(
            timezone.utc
        )
        end = start + timedelta(days=1)
        with Session(self.engine) as session:
            calls = session.scalar(
                select(func.count())
                .select_from(LlmUsageRow)
                .where(
                    LlmUsageRow.created_at >= start,
                    LlmUsageRow.created_at < end,
                )
            )
            review_calls = session.scalar(
                select(func.coalesce(func.sum(LlmUsageRow.review_calls), 0)).where(
                    LlmUsageRow.created_at >= start,
                    LlmUsageRow.created_at < end,
                )
            )
            input_tokens = session.scalar(
                select(func.coalesce(func.sum(LlmUsageRow.input_tokens), 0)).where(
                    LlmUsageRow.created_at >= start,
                    LlmUsageRow.created_at < end,
                )
            )
            output_tokens = session.scalar(
                select(func.coalesce(func.sum(LlmUsageRow.output_tokens), 0)).where(
                    LlmUsageRow.created_at >= start,
                    LlmUsageRow.created_at < end,
                )
            )
            cost_cny = session.scalar(
                select(func.coalesce(func.sum(LlmUsageRow.cost_cny), 0)).where(
                    LlmUsageRow.created_at >= start,
                    LlmUsageRow.created_at < end,
                )
            )
        return BudgetSnapshot(
            calls=int(calls or 0),
            review_calls=int(review_calls or 0),
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            cost_cny=Decimal(str(cost_cny or 0)),
        )

    def list_usage(self) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(LlmUsageRow).order_by(
                    LlmUsageRow.created_at,
                    LlmUsageRow.usage_id,
                )
            ).all()
            return [
                {
                    "usage_id": row.usage_id,
                    "operation_id": row.operation_id,
                    "attempt_id": row.attempt_id,
                    "provider_request_id": row.provider_request_id,
                    "provider": row.provider,
                    "model": row.model,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "review_calls": row.review_calls,
                    "cost_cny": str(row.cost_cny),
                    "price_version": row.price_version,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
