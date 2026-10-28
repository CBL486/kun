"""跨 SQLite/PostgreSQL 的世界、事件和记忆仓库。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from memory_core import Scope
from memory_core.core import (
    ACTIVE_THRESHOLD,
    FUZZY_THRESHOLD,
    HALF_LIFE_DAYS,
    estimate_tokens,
)
from rpg_sim.ids import canonical_json, digest, stable_id
from rpg_storage.errors import StorageError

from .migrations import migrate
from .models import (
    ActionLogRow,
    EventLogRow,
    MemoryRow,
    NPCMemorySlotRow,
    ProjectionOutboxRow,
    WorldHeadRow,
    WorldVersionRow,
)


@dataclass
class OrmCommitResult:
    event_id: str
    operation_id: str
    replayed: bool
    memory_ids: list[str]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "operation_id": self.operation_id,
            "replayed": self.replayed,
            "memory_ids": self.memory_ids,
            "status": self.status,
        }


class OrmRepository:
    def __init__(
        self,
        engine: Engine,
        *,
        user_id: str = "observer_demo_001",
        migrate_schema: bool = True,
    ):
        self.engine = engine
        self.user_id = user_id
        if migrate_schema:
            migrate(self.engine)
        self.Session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def initialize_world(self, state: dict[str, Any]) -> None:
        with Session(self.engine) as session, session.begin():
            existing = session.get(WorldHeadRow, state["world_id"])
            if existing:
                if existing.state != state:
                    raise StorageError(
                        "world_conflict",
                        "初始世界状态与已有状态不一致",
                    )
                return
            session.add(
                WorldHeadRow(
                    world_id=state["world_id"],
                    state_version=state["state_version"],
                    logical_time=state["logical_time"],
                    state=state,
                    updated_at=state["logical_time"],
                )
            )
            session.add(
                WorldVersionRow(
                    world_id=state["world_id"],
                    state_version=state["state_version"],
                    logical_time=state["logical_time"],
                    state=state,
                    event_id=None,
                    created_at=state["logical_time"],
                )
            )

    def commit_step(
        self,
        *,
        state_before: dict[str, Any],
        state_after: dict[str, Any],
        event: dict[str, Any],
        action: dict[str, Any],
        simulate_projection_failure: bool = False,
    ) -> OrmCommitResult:
        self._validate_step(state_before, state_after, event, action)
        fingerprint = canonical_json(action)
        with Session(self.engine) as session:
            existing = session.get(ActionLogRow, action["operation_id"])
            if existing:
                if existing.fingerprint != fingerprint:
                    raise StorageError(
                        "duplicate_operation",
                        "operation 内容不一致",
                    )
                memory_ids, status = self._project_event(
                    existing.event_id,
                    simulate_failure=False,
                )
                return OrmCommitResult(
                    event_id=existing.event_id,
                    operation_id=action["operation_id"],
                    replayed=True,
                    memory_ids=memory_ids,
                    status=status,
                )

        projections = self._build_projections(event=event, action=action)
        try:
            with Session(self.engine) as session, session.begin():
                head = session.scalar(
                    select(WorldHeadRow)
                    .where(WorldHeadRow.world_id == state_after["world_id"])
                    .with_for_update()
                )
                if not head:
                    raise StorageError("unknown_reference", "世界尚未初始化")
                if (
                    head.state_version != state_before["state_version"]
                    or head.state != state_before
                ):
                    raise StorageError("stale_state", "数据库世界版本已过期")
                session.add(
                    ActionLogRow(
                        operation_id=action["operation_id"],
                        action_id=action["action_id"],
                        world_id=action["world_id"],
                        character_id=action["character_id"],
                        action_type=action["action_type"],
                        tick_id=action["tick_id"],
                        fingerprint=fingerprint,
                        status="committed",
                        event_id=event["event_id"],
                        payload=action,
                        committed_at=event["committed_at"],
                    )
                )
                session.add(
                    EventLogRow(
                        event_id=event["event_id"],
                        world_id=event["world_id"],
                        world_date=event["world_date"],
                        sequence=event["sequence"],
                        slot_key=event["slot_key"],
                        occurred_at=event["occurred_at"],
                        event_type=event["event_type"],
                        summary=event["summary"],
                        visibility=event["visibility"],
                        tick_id=event["tick_id"],
                        action_id=event["action_id"],
                        event=event,
                        committed_at=event["committed_at"],
                    )
                )
                session.add(
                    WorldVersionRow(
                        world_id=state_after["world_id"],
                        state_version=state_after["state_version"],
                        logical_time=state_after["logical_time"],
                        state=state_after,
                        event_id=event["event_id"],
                        created_at=event["committed_at"],
                    )
                )
                head.state_version = state_after["state_version"]
                head.logical_time = state_after["logical_time"]
                head.state = state_after
                head.updated_at = event["committed_at"]
                for projection in projections:
                    session.add(
                        ProjectionOutboxRow(
                            projection_id=projection["projection_id"],
                            event_id=event["event_id"],
                            candidate_index=projection["candidate_index"],
                            character_id=projection["character_id"],
                            dedupe_key=projection["dedupe_key"],
                            payload=projection,
                            status="pending",
                            attempts=0,
                            last_error=None,
                            created_at=event["committed_at"],
                            updated_at=event["committed_at"],
                        )
                    )
        except IntegrityError as error:
            raise StorageError(
                "event_conflict",
                "数据库唯一约束失败，事务已回滚",
            ) from error

        memory_ids, status = self._project_event(
            event["event_id"],
            simulate_failure=simulate_projection_failure,
        )
        return OrmCommitResult(
            event_id=event["event_id"],
            operation_id=action["operation_id"],
            replayed=False,
            memory_ids=memory_ids,
            status=status,
        )

    def reconcile(self, event_id: str | None = None) -> dict[str, int]:
        with Session(self.engine) as session:
            query = select(ProjectionOutboxRow.event_id).where(
                ProjectionOutboxRow.status != "projected"
            )
            if event_id:
                query = query.where(ProjectionOutboxRow.event_id == event_id)
            event_ids = sorted(set(session.scalars(query).all()))
        projected = 0
        failed = 0
        for current_event_id in event_ids:
            memory_ids, status = self._project_event(current_event_id)
            if status == "projected":
                projected += len(memory_ids)
            else:
                failed += 1
        return {"projected": projected, "failed_events": failed}

    def recall(
        self,
        *,
        scope: Scope,
        current_time: str,
        query_tags: list[str] | None = None,
        max_items: int = 5,
        max_tokens: int = 1_000,
        include_fuzzy: bool = True,
    ) -> list[dict[str, Any]]:
        now = datetime.fromisoformat(current_time)
        query = set(query_tags or [])
        with Session(self.engine) as session, session.begin():
            rows = session.scalars(
                select(MemoryRow)
                .where(MemoryRow.scope_hash == scope.scope_hash)
                .order_by(MemoryRow.memory_id)
            ).all()
            for row in rows:
                if row.locked:
                    row.strength = row.strength
                    row.state = "active"
                else:
                    elapsed_days = max(
                        0.0,
                        (
                            now - _aware(row.last_strength_update)
                        ).total_seconds()
                        / 86400,
                    )
                    row.strength = round(
                        row.strength * (0.5 ** (elapsed_days / HALF_LIFE_DAYS)),
                        6,
                    )
                    row.state = _lifecycle(row.strength)
                row.last_strength_update = now
            allowed_states = {"active", "fuzzy"} if include_fuzzy else {"active"}
            ranked = []
            for row in rows:
                if row.state not in allowed_states:
                    continue
                tags = set(row.scene_tags)
                relevance = len(tags & query) / len(query) if query else 0.25
                age_days = max(
                    0.0,
                    (now - _aware(row.created_at)).total_seconds() / 86400,
                )
                recency = 0.5 ** (age_days / HALF_LIFE_DAYS)
                access_bonus = min(row.access_count / 5, 1.0)
                breakdown = {
                    "relevance": round(relevance * 0.40, 6),
                    "strength": round(row.strength * 0.20, 6),
                    "importance": round(row.importance * 0.15, 6),
                    "emotional_weight": round(row.emotional_weight * 0.10, 6),
                    "recency": round(recency * 0.10, 6),
                    "access_bonus": round(access_bonus * 0.05, 6),
                }
                ranked.append(
                    {
                        "memory": self._memory_dict(row),
                        "score": round(sum(breakdown.values()), 6),
                        "score_breakdown": breakdown,
                        "reason_codes": ["scope_exact", f"state_{row.state}"],
                    }
                )
            ranked.sort(
                key=lambda item: (
                    -item["score"],
                    item["memory"]["memory_id"],
                )
            )
            selected = []
            used_tokens = 0
            selected_rows = []
            for result in ranked:
                tokens = estimate_tokens(result["memory"]["content"])
                if len(selected) >= max_items:
                    break
                if used_tokens + tokens > max_tokens:
                    continue
                selected.append(result)
                used_tokens += tokens
                selected_rows.append(result["memory"]["memory_id"])
            for row in rows:
                if row.memory_id in selected_rows:
                    row.last_accessed_at = now
                    row.access_count += 1
        return selected

    def get_world_state(self) -> dict[str, Any]:
        with Session(self.engine) as session:
            head = session.scalar(select(WorldHeadRow).limit(1))
            if not head:
                raise StorageError("unknown_reference", "世界尚未初始化")
            return head.state

    def get_action(self, operation_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(ActionLogRow, operation_id)
            return self._action_dict(row) if row else None

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(EventLogRow, event_id)
            return self._event_dict(row) if row else None

    def list_actions(self) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(ActionLogRow).order_by(
                    ActionLogRow.committed_at,
                    ActionLogRow.operation_id,
                )
            ).all()
            return [self._action_dict(row) for row in rows]

    def list_events(self) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(EventLogRow).order_by(
                    EventLogRow.world_date,
                    EventLogRow.sequence,
                    EventLogRow.event_id,
                )
            ).all()
            return [self._event_dict(row) for row in rows]

    def list_projections(self, status: str | None = None) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(ProjectionOutboxRow)
            if status:
                query = query.where(ProjectionOutboxRow.status == status)
            rows = session.scalars(
                query.order_by(
                    ProjectionOutboxRow.event_id,
                    ProjectionOutboxRow.candidate_index,
                )
            ).all()
            return [
                {
                    "projection_id": row.projection_id,
                    "event_id": row.event_id,
                    "candidate_index": row.candidate_index,
                    "character_id": row.character_id,
                    "dedupe_key": row.dedupe_key,
                    "payload": row.payload,
                    "status": row.status,
                    "attempts": row.attempts,
                    "last_error": row.last_error,
                    "created_at": _utc_iso(row.created_at),
                    "updated_at": _utc_iso(row.updated_at),
                }
                for row in rows
            ]

    def save_npc_slots(
        self,
        npc_id: str,
        slots: list[dict[str, Any]],
        *,
        updated_at: str,
    ) -> None:
        if len(slots) > 8:
            raise StorageError("npc_memory_full", "NPC 记忆槽不能超过 8 条")
        with Session(self.engine) as session, session.begin():
            existing = session.scalars(
                select(NPCMemorySlotRow).where(NPCMemorySlotRow.npc_id == npc_id)
            ).all()
            for row in existing:
                session.delete(row)
            for slot in slots:
                session.add(
                    NPCMemorySlotRow(
                        npc_id=npc_id,
                        slot_id=slot["slot_id"],
                        kind=slot["kind"],
                        content_key=slot["content_key"],
                        source_event_id=slot.get("source_event_id"),
                        important=bool(slot.get("important", False)),
                        expires_on=slot.get("expires_on"),
                        last_used_at=slot.get("last_used_at"),
                        updated_at=updated_at,
                    )
                )

    def load_npc_slots(self, npc_id: str) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(NPCMemorySlotRow)
                .where(NPCMemorySlotRow.npc_id == npc_id)
                .order_by(
                    NPCMemorySlotRow.important.desc(),
                    NPCMemorySlotRow.slot_id,
                )
            ).all()
            return [
                {
                    "npc_id": row.npc_id,
                    "slot_id": row.slot_id,
                    "kind": row.kind,
                    "content_key": row.content_key,
                    "source_event_id": row.source_event_id,
                    "important": row.important,
                    "expires_on": row.expires_on,
                    "last_used_at": (
                        _utc_iso(row.last_used_at)
                        if row.last_used_at
                        else None
                    ),
                    "updated_at": _utc_iso(row.updated_at),
                }
                for row in rows
            ]

    def semantic_export(self) -> dict[str, Any]:
        with Session(self.engine) as session:
            memories = session.scalars(
                select(MemoryRow).order_by(MemoryRow.memory_id)
            ).all()
            memory_records = [self._memory_dict(row) for row in memories]
        payload = {
            "world": self.get_world_state(),
            "actions": self.list_actions(),
            "events": self.list_events(),
            "projections": self.list_projections(),
            "memories": memory_records,
        }
        payload["digest"] = digest(payload)
        return payload

    def _project_event(
        self,
        event_id: str,
        *,
        simulate_failure: bool = False,
    ) -> tuple[list[str], str]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(ProjectionOutboxRow)
                .where(
                    ProjectionOutboxRow.event_id == event_id,
                    ProjectionOutboxRow.status != "projected",
                )
                .order_by(ProjectionOutboxRow.candidate_index)
            ).all()
            if not rows:
                projected = session.scalars(
                    select(MemoryRow.memory_id).where(
                        MemoryRow.source_event_id == event_id
                    )
                ).all()
                return list(projected), "projected"
        if simulate_failure:
            with Session(self.engine) as session, session.begin():
                for row in session.scalars(
                    select(ProjectionOutboxRow).where(
                        ProjectionOutboxRow.event_id == event_id,
                        ProjectionOutboxRow.status != "projected",
                    )
                ).all():
                    row.attempts += 1
                    row.last_error = "simulated_projection_failure"
            return [], "reconciliation_required"

        memory_ids = []
        try:
            with Session(self.engine) as session, session.begin():
                rows = session.scalars(
                    select(ProjectionOutboxRow)
                    .where(
                        ProjectionOutboxRow.event_id == event_id,
                        ProjectionOutboxRow.status != "projected",
                    )
                    .order_by(ProjectionOutboxRow.candidate_index)
                ).all()
                for outbox in rows:
                    payload = outbox.payload
                    scope = Scope.from_dict(payload["scope"])
                    existing = session.scalar(
                        select(MemoryRow).where(
                            MemoryRow.scope_hash == scope.scope_hash,
                            MemoryRow.dedupe_key == payload["dedupe_key"],
                        )
                    )
                    if existing:
                        memory_id = existing.memory_id
                    else:
                        memory_id = stable_id(
                            "mem",
                            [scope.scope_hash, payload["dedupe_key"]],
                        )
                        session.add(
                            MemoryRow(
                                memory_id=memory_id,
                                tenant_id=scope.tenant_id,
                                world_id=scope.world_id,
                                user_id=scope.user_id,
                                character_id=scope.character_id,
                                surface=scope.surface,
                                conversation_id=scope.conversation_id,
                                conversation_key=scope.conversation_key,
                                scope_hash=scope.scope_hash,
                                kind=payload["kind"],
                                source=payload["source"],
                                content=payload["content"],
                                importance=payload["importance"],
                                emotional_weight=payload["emotional_weight"],
                                confidence=payload["confidence"],
                                strength=payload["strength"],
                                scene_tags=payload["scene_tags"],
                                created_at=payload["created_at"],
                                last_accessed_at=None,
                                last_strength_update=payload["created_at"],
                                access_count=0,
                                restated_count=0,
                                locked=False,
                                state=_lifecycle(payload["strength"]),
                                source_event_id=payload["source_event_id"],
                                dedupe_key=payload["dedupe_key"],
                                metadata_document=payload["metadata"],
                            )
                        )
                    memory_ids.append(memory_id)
                    outbox.status = "projected"
                    outbox.attempts += 1
                    outbox.last_error = None
            return memory_ids, "projected"
        except Exception as error:
            with Session(self.engine) as session, session.begin():
                for row in session.scalars(
                    select(ProjectionOutboxRow).where(
                        ProjectionOutboxRow.event_id == event_id,
                        ProjectionOutboxRow.status != "projected",
                    )
                ).all():
                    row.status = "failed"
                    row.attempts += 1
                    row.last_error = type(error).__name__
            return [], "reconciliation_required"

    def _build_projections(
        self,
        *,
        event: dict[str, Any],
        action: dict[str, Any],
    ) -> list[dict[str, Any]]:
        projections = []
        for index, candidate in enumerate(event.get("memory_candidates", [])):
            conversation_id = (
                None
                if event["event_type"] == "journal_written"
                else f"day-{event['world_date']}"
            )
            scope = Scope(
                tenant_id="rpg-world",
                world_id=event["world_id"],
                user_id=self.user_id,
                character_id=action["character_id"],
                surface="school",
                conversation_id=conversation_id,
            )
            dedupe_key = (
                f"rpg:{event['event_id']}:{action['character_id']}:{index}"
            )
            projections.append(
                {
                    "projection_id": stable_id(
                        "proj",
                        [event["event_id"], index, action["character_id"]],
                    ),
                    "candidate_index": index,
                    "character_id": action["character_id"],
                    "dedupe_key": dedupe_key,
                    "scope": scope.to_dict(),
                    "kind": candidate["kind"],
                    "source": candidate["source"],
                    "content": candidate["summary"],
                    "source_event_id": event["event_id"],
                    "importance": candidate["importance"],
                    "emotional_weight": candidate["emotional_weight"],
                    "confidence": 0.98,
                    "strength": round(
                        0.45 + candidate["importance"] * 0.35,
                        4,
                    ),
                    "scene_tags": candidate["scene_tags"],
                    "created_at": event["committed_at"],
                    "metadata": {
                        "visibility": event["visibility"],
                        "template_id": event["template_id"],
                    },
                }
            )
        return projections

    @staticmethod
    def _validate_step(
        state_before: dict[str, Any],
        state_after: dict[str, Any],
        event: dict[str, Any],
        action: dict[str, Any],
    ) -> None:
        if event["world_id"] != action["world_id"]:
            raise StorageError("scope_mismatch", "事件和动作 world_id 不一致")
        if event["action_id"] != action["action_id"]:
            raise StorageError("event_conflict", "事件 action_id 不一致")
        if state_before["state_version"] + 1 != state_after["state_version"]:
            raise StorageError("stale_state", "状态版本不是单步递增")
        if (
            event["state_version_before"] != state_before["state_version"]
            or event["state_version_after"] != state_after["state_version"]
        ):
            raise StorageError("stale_state", "事件状态版本不一致")

    @staticmethod
    def _action_dict(row: ActionLogRow) -> dict[str, Any]:
        return {
            "operation_id": row.operation_id,
            "action_id": row.action_id,
            "world_id": row.world_id,
            "character_id": row.character_id,
            "action_type": row.action_type,
            "tick_id": row.tick_id,
            "fingerprint": row.fingerprint,
            "status": row.status,
            "event_id": row.event_id,
            "payload": row.payload,
            "committed_at": _utc_iso(row.committed_at),
        }

    @staticmethod
    def _event_dict(row: EventLogRow) -> dict[str, Any]:
        return {
            "event_id": row.event_id,
            "world_id": row.world_id,
            "world_date": row.world_date,
            "sequence": row.sequence,
            "slot_key": row.slot_key,
            "occurred_at": _utc_iso(row.occurred_at),
            "event_type": row.event_type,
            "summary": row.summary,
            "visibility": row.visibility,
            "tick_id": row.tick_id,
            "action_id": row.action_id,
            "event": row.event,
            "committed_at": _utc_iso(row.committed_at),
        }

    @staticmethod
    def _memory_dict(row: MemoryRow) -> dict[str, Any]:
        return {
            "memory_id": row.memory_id,
            "scope": {
                "tenant_id": row.tenant_id,
                "world_id": row.world_id,
                "user_id": row.user_id,
                "character_id": row.character_id,
                "surface": row.surface,
                "conversation_id": row.conversation_id,
            },
            "kind": row.kind,
            "source": row.source,
            "content": row.content,
            "importance": row.importance,
            "emotional_weight": row.emotional_weight,
            "confidence": row.confidence,
            "strength": row.strength,
            "scene_tags": row.scene_tags,
            "created_at": _utc_iso(row.created_at),
            "last_accessed_at": (
                _utc_iso(row.last_accessed_at) if row.last_accessed_at else None
            ),
            "last_strength_update": _utc_iso(row.last_strength_update),
            "access_count": row.access_count,
            "restated_count": row.restated_count,
            "locked": row.locked,
            "state": row.state,
            "source_event_id": row.source_event_id,
            "dedupe_key": row.dedupe_key,
            "metadata": row.metadata_document,
        }


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return _aware(value).isoformat().replace("+00:00", "Z")


def _lifecycle(strength: float) -> str:
    if strength >= ACTIVE_THRESHOLD:
        return "active"
    if strength >= FUZZY_THRESHOLD:
        return "fuzzy"
    return "archived"
