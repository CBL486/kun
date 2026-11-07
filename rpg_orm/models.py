"""B5 SQLAlchemy 表模型。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
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


class WorldClockRow(Base):
    __tablename__ = "world_clock_states"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    logical_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    state_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    last_tick_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    catch_up_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="live",
    )
    compressed_ticks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "state_revision >= 0",
            name="ck_world_clock_revision",
        ),
        CheckConstraint(
            "compressed_ticks >= 0",
            name="ck_world_clock_compressed_ticks",
        ),
    )


class MemoryEventRow(Base):
    __tablename__ = "memory_events"

    event_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(96), nullable=False)
    participants: Mapped[list[str]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    location_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    intensity: Mapped[float] = mapped_column(Float, nullable=False)
    importance: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    metadata_document: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONDocument,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "dedupe_key",
            name="uq_memory_events_world_dedupe",
        ),
        CheckConstraint(
            "valence >= -1 AND valence <= 1",
            name="ck_memory_event_valence",
        ),
        CheckConstraint(
            "intensity >= 0 AND intensity <= 1",
            name="ck_memory_event_intensity",
        ),
        CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_memory_event_importance",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_memory_event_confidence",
        ),
        CheckConstraint(
            "visibility IN ('private', 'user_visible', 'public')",
            name="ck_memory_event_visibility",
        ),
        CheckConstraint(
            "source IN ('agent', 'world', 'player', 'school', 'media')",
            name="ck_memory_event_source",
        ),
        Index(
            "idx_memory_events_world_time",
            "world_id",
            "occurred_at",
        ),
    )


class RelationshipStateRow(Base):
    __tablename__ = "relationship_states"

    relationship_id: Mapped[str] = mapped_column(
        String(160),
        primary_key=True,
    )
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    from_character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    to_character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    affection: Mapped[float] = mapped_column(Float, nullable=False)
    trust: Mapped[float] = mapped_column(Float, nullable=False)
    familiarity: Mapped[float] = mapped_column(Float, nullable=False)
    warmth: Mapped[float] = mapped_column(Float, nullable=False)
    tension: Mapped[float] = mapped_column(Float, nullable=False)
    last_event_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "from_character_id",
            "to_character_id",
            name="uq_relationship_direction",
        ),
        CheckConstraint(
            "affection >= 0 AND affection <= 1",
            name="ck_relationship_affection",
        ),
        CheckConstraint(
            "trust >= 0 AND trust <= 1",
            name="ck_relationship_trust",
        ),
        CheckConstraint(
            "familiarity >= 0 AND familiarity <= 1",
            name="ck_relationship_familiarity",
        ),
        CheckConstraint(
            "warmth >= 0 AND warmth <= 1",
            name="ck_relationship_warmth",
        ),
        CheckConstraint(
            "tension >= 0 AND tension <= 1",
            name="ck_relationship_tension",
        ),
    )


class EmotionStateRow(Base):
    __tablename__ = "emotion_states"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    arousal: Mapped[float] = mapped_column(Float, nullable=False)
    energy: Mapped[float] = mapped_column(Float, nullable=False)
    stress: Mapped[float] = mapped_column(Float, nullable=False)
    curiosity: Mapped[float] = mapped_column(Float, nullable=False)
    decay_rate: Mapped[float] = mapped_column(Float, nullable=False)
    last_event_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "valence >= -1 AND valence <= 1",
            name="ck_emotion_valence",
        ),
        CheckConstraint(
            "arousal >= 0 AND arousal <= 1",
            name="ck_emotion_arousal",
        ),
        CheckConstraint(
            "energy >= 0 AND energy <= 1",
            name="ck_emotion_energy",
        ),
        CheckConstraint(
            "stress >= 0 AND stress <= 1",
            name="ck_emotion_stress",
        ),
        CheckConstraint(
            "curiosity >= 0 AND curiosity <= 1",
            name="ck_emotion_curiosity",
        ),
        CheckConstraint(
            "decay_rate >= 0 AND decay_rate <= 1",
            name="ck_emotion_decay_rate",
        ),
    )


class PersonaBaselineRow(Base):
    __tablename__ = "persona_baselines"

    persona_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "character_id",
            "revision",
            name="uq_persona_baseline_character_revision",
        ),
        CheckConstraint("revision > 0", name="ck_persona_revision"),
        Index(
            "idx_persona_baselines_active",
            "character_id",
            "is_active",
        ),
    )


class PersonaStateRow(Base):
    __tablename__ = "persona_states"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    baseline_persona_id: Mapped[str] = mapped_column(
        String(96),
        nullable=False,
    )
    baseline_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    self_narrative: Mapped[str] = mapped_column(Text, nullable=False)
    behavior_habits: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    value_weights: Mapped[dict[str, float]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    interests: Mapped[list[str]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    active_goals: Mapped[list[str]] = mapped_column(
        JSONDocument,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "baseline_revision > 0",
            name="ck_persona_state_revision",
        ),
    )


class PersonaChangeLogRow(Base):
    __tablename__ = "persona_change_log"

    change_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    baseline_persona_id: Mapped[str] = mapped_column(
        String(96),
        nullable=False,
    )
    baseline_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    dimension: Mapped[str] = mapped_column(String(64), nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        Index(
            "idx_persona_change_character_time",
            "character_id",
            "changed_at",
        ),
        CheckConstraint(
            "source IN ("
            "'world_event', 'memory_recall', 'player_baseline_edit', "
            "'player_custom_persona', 'default_persona'"
            ")",
            name="ck_persona_change_source",
        ),
    )


class StudySessionRow(Base):
    __tablename__ = "study_sessions"

    study_session_id: Mapped[str] = mapped_column(
        String(96),
        primary_key=True,
    )
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    world_date: Mapped[str] = mapped_column(String(10), nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    location_id: Mapped[str] = mapped_column(String(96), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    curriculum_id: Mapped[str] = mapped_column(String(96), nullable=False)
    token_budget: Mapped[int] = mapped_column(Integer, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    reflection_memory_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "world_date",
            "character_id",
            name="uq_study_session_daily",
        ),
        CheckConstraint(
            "status IN ('scheduled', 'running', 'completed', 'failed', 'missed')",
            name="ck_study_session_status",
        ),
    )


class MediaObservationRow(Base):
    __tablename__ = "media_observations"

    observation_id: Mapped[str] = mapped_column(
        String(96),
        primary_key=True,
    )
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_valence: Mapped[float] = mapped_column(Float, nullable=False)
    memory_event_id: Mapped[str | None] = mapped_column(
        String(96),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "url_hash",
            name="uq_media_observation_url",
        ),
        CheckConstraint(
            "provider IN ('bilibili', 'douyin')",
            name="ck_media_provider",
        ),
        CheckConstraint(
            "status IN ('pending', 'reviewing', 'reviewed', 'blocked', 'failed')",
            name="ck_media_status",
        ),
        CheckConstraint(
            "emotional_valence >= -1 AND emotional_valence <= 1",
            name="ck_media_valence",
        ),
    )


class SetupStateRow(Base):
    __tablename__ = "setup_state"

    world_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    configured: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    key_hint: Mapped[str | None] = mapped_column(String(32), nullable=True)
    persona_configured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    world_ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class DeepSeekCredentialRow(Base):
    __tablename__ = "deepseek_credentials"

    credential_id: Mapped[str] = mapped_column(
        String(96),
        primary_key=True,
    )
    world_id: Mapped[str] = mapped_column(String(96), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    key_ref: Mapped[str] = mapped_column(Text, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "idx_deepseek_credentials_world_active",
            "world_id",
            "active",
        ),
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


class ScheduledTaskRow(Base):
    __tablename__ = "scheduled_tasks"

    task_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    operation_id: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False
    )
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONDocument, nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSONDocument, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'leased', 'succeeded', 'dead_letter')",
            name="ck_scheduled_task_status",
        ),
        CheckConstraint("attempts >= 0", name="ck_scheduled_task_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_scheduled_task_max_attempts"),
        Index(
            "idx_scheduled_tasks_ready",
            "status",
            "priority",
            "available_at",
        ),
        Index(
            "idx_scheduled_tasks_lease",
            "status",
            "lease_expires_at",
        ),
    )


class ObserverMessageRow(Base):
    __tablename__ = "observer_messages"

    message_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'claimed', 'responded', 'rejected')",
            name="ck_observer_message_status",
        ),
        Index("idx_observer_messages_status", "status", "created_at"),
    )


class LlmOperationRow(Base):
    __tablename__ = "llm_operations"

    operation_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    request_hash: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[str] = mapped_column(String(96), nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), nullable=False)
    run_mode: Mapped[str] = mapped_column(String(24), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    degradation_reason: Mapped[str | None] = mapped_column(
        String(96), nullable=True
    )
    prompt_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    redacted_prompt_preview: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('succeeded', 'fallback', 'blocked')",
            name="ck_llm_operation_status",
        ),
        CheckConstraint(
            "review_status IN ('approved', 'blocked', 'unavailable')",
            name="ck_llm_review_status",
        ),
        CheckConstraint(
            "run_mode IN ('model', 'rule')",
            name="ck_llm_run_mode",
        ),
    )


class LlmUsageRow(Base):
    __tablename__ = "llm_usage"

    usage_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    operation_id: Mapped[str] = mapped_column(
        String(160), nullable=False
    )
    attempt_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_request_id: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    review_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_cny: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0 AND review_calls >= 0",
            name="ck_llm_usage_nonnegative",
        ),
        Index("idx_llm_usage_operation", "operation_id"),
        Index("idx_llm_usage_created", "created_at"),
    )


class LlmCostAttributionRow(Base):
    __tablename__ = "llm_cost_attributions"

    usage_id: Mapped[str] = mapped_column(
        String(128), primary_key=True
    )
    budget_date: Mapped[str] = mapped_column(String(10), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    character_id: Mapped[str] = mapped_column(String(96), nullable=False)
    interface: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index(
            "idx_llm_cost_attribution_dimensions",
            "budget_date",
            "event_id",
            "character_id",
            "interface",
        ),
    )
