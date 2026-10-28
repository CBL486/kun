"""B5 SQLAlchemy 表模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .types import UTCDateTime

JSONDocument = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class SchemaVersionRow(Base):
    __tablename__ = "schema_versions"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class WorldHeadRow(Base):
    __tablename__ = "world_heads"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    logical_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("state_version >= 0", name="ck_world_head_version"),
    )


class WorldVersionRow(Base):
    __tablename__ = "world_versions"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    state_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    logical_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class ActionLogRow(Base):
    __tablename__ = "actions"

    operation_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    action_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    tick_id: Mapped[str] = mapped_column(String(96), nullable=False)
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        Index("idx_actions_world_time", "world_id", "committed_at"),
    )


class EventLogRow(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    world_date: Mapped[str] = mapped_column(String(10), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_key: Mapped[str] = mapped_column(String(24), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False)
    tick_id: Mapped[str] = mapped_column(String(96), nullable=False)
    action_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    event: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "world_date",
            "sequence",
            name="uq_events_world_date_sequence",
        ),
        Index("idx_events_world_time", "world_id", "world_date", "sequence"),
    )


class ProjectionOutboxRow(Base):
    __tablename__ = "memory_projection_outbox"

    projection_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("events.event_id", ondelete="RESTRICT"),
        nullable=False,
    )
    candidate_index: Mapped[int] = mapped_column(Integer, nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "candidate_index",
            name="uq_outbox_event_candidate",
        ),
        CheckConstraint(
            "status IN ('pending', 'projected', 'failed')",
            name="ck_outbox_status",
        ),
        Index("idx_outbox_status", "status"),
    )


class MemoryRow(Base):
    __tablename__ = "memories"

    memory_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    user_id: Mapped[str] = mapped_column(String(96), nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    surface: Mapped[str] = mapped_column(String(32), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    conversation_key: Mapped[str] = mapped_column(String(96), nullable=False)
    scope_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(48), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float] = mapped_column(Float, nullable=False)
    emotional_weight: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    scene_tags: Mapped[list[str]] = mapped_column(JSONDocument, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, nullable=True
    )
    last_strength_update: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False
    )
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    restated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    source_event_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("events.event_id", ondelete="RESTRICT"),
        nullable=False,
    )
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    metadata_document: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONDocument, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "scope_hash",
            "dedupe_key",
            name="uq_memories_scope_dedupe",
        ),
        CheckConstraint(
            "state IN ('active', 'fuzzy', 'archived')",
            name="ck_memory_state",
        ),
        CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_memory_importance",
        ),
        CheckConstraint(
            "strength >= 0 AND strength <= 1",
            name="ck_memory_strength",
        ),
        Index("idx_memories_scope_state", "scope_hash", "state"),
        Index("idx_memories_source_event", "source_event_id"),
    )


class MemoryMutationRow(Base):
    __tablename__ = "memory_mutations"

    operation_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    memory_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("memories.memory_id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_event_id: Mapped[str] = mapped_column(String(96), nullable=False)
    reason: Mapped[str] = mapped_column(String(24), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class NPCMemorySlotRow(Base):
    __tablename__ = "npc_memory_slots"

    npc_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    slot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    content_key: Mapped[str] = mapped_column(String(160), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    important: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expires_on: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
