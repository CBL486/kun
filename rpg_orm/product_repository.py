"""Schema-5 event, relationship, emotion and Persona persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from rpg_sim.ids import stable_id
from rpg_storage.errors import StorageError

from .migrations import migrate
from .models import (
    EmotionStateRow,
    MemoryEventRow,
    PersonaBaselineRow,
    PersonaChangeLogRow,
    PersonaStateRow,
    RelationshipStateRow,
    SetupStateRow,
    DeepSeekCredentialRow,
    WorldClockRow,
)


class ProductRepository:
    def __init__(self, engine: Engine, *, migrate_schema: bool = True):
        self.engine = engine
        if migrate_schema:
            migrate(engine)

    def record_memory_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        event_id = str(payload["event_id"])
        world_id = str(payload["world_id"])
        dedupe_key = str(payload["dedupe_key"])
        self._validate_event(payload)
        with Session(self.engine) as session, session.begin():
            existing = session.scalar(
                select(MemoryEventRow).where(
                    MemoryEventRow.world_id == world_id,
                    MemoryEventRow.dedupe_key == dedupe_key,
                )
            )
            if existing:
                if existing.event_id != event_id:
                    raise StorageError(
                        "duplicate_event",
                        "同一去重键对应不同事件",
                    )
                return self._event_dict(existing)
            row = MemoryEventRow(
                event_id=event_id,
                world_id=world_id,
                actor_id=payload["actor_id"],
                participants=list(payload.get("participants", [])),
                location_id=payload.get("location_id"),
                event_type=payload["event_type"],
                occurred_at=_datetime(payload["occurred_at"]),
                summary=payload["summary"],
                valence=float(payload["valence"]),
                intensity=float(payload["intensity"]),
                importance=float(payload["importance"]),
                confidence=float(payload["confidence"]),
                visibility=payload["visibility"],
                source=payload["source"],
                dedupe_key=dedupe_key,
                metadata_document=dict(payload.get("metadata", {})),
                created_at=_datetime(payload.get("created_at", payload["occurred_at"])),
            )
            session.add(row)
            session.flush()
            return self._event_dict(row)

    def apply_relationship(
        self,
        *,
        event_id: str,
        relationship_id: str,
        world_id: str,
        from_character_id: str,
        to_character_id: str,
        deltas: dict[str, float],
        updated_at: str,
    ) -> dict[str, Any]:
        self._require_event(world_id, event_id)
        allowed = {"affection", "trust", "familiarity", "warmth", "tension"}
        if set(deltas) - allowed:
            raise StorageError("invalid_change", "关系变化字段无效")
        now = _datetime(updated_at)
        with Session(self.engine) as session, session.begin():
            row = session.get(RelationshipStateRow, relationship_id)
            if row and row.last_event_id == event_id:
                return self._relationship_dict(row)
            if row is None:
                row = RelationshipStateRow(
                    relationship_id=relationship_id,
                    world_id=world_id,
                    from_character_id=from_character_id,
                    to_character_id=to_character_id,
                    affection=0.5,
                    trust=0.3,
                    familiarity=0.1,
                    warmth=0.3,
                    tension=0.0,
                    last_event_id=None,
                    updated_at=now,
                )
                session.add(row)
            for field, delta in deltas.items():
                current = float(getattr(row, field))
                setattr(row, field, round(_clamp(current + float(delta)), 6))
            row.last_event_id = event_id
            row.updated_at = now
            session.flush()
            return self._relationship_dict(row)

    def update_emotion(
        self,
        *,
        event_id: str,
        world_id: str,
        character_id: str,
        values: dict[str, float],
        updated_at: str,
        decay_rate: float = 0.1,
    ) -> dict[str, Any]:
        self._require_event(world_id, event_id)
        allowed = {
            "valence",
            "arousal",
            "energy",
            "stress",
            "curiosity",
            "decay_rate",
        }
        if set(values) - allowed:
            raise StorageError("invalid_change", "情绪变化字段无效")
        now = _datetime(updated_at)
        with Session(self.engine) as session, session.begin():
            row = session.get(EmotionStateRow, (world_id, character_id))
            if row and row.last_event_id == event_id:
                return self._emotion_dict(row)
            if row is None:
                row = EmotionStateRow(
                    world_id=world_id,
                    character_id=character_id,
                    valence=0.0,
                    arousal=0.4,
                    energy=0.7,
                    stress=0.2,
                    curiosity=0.6,
                    decay_rate=decay_rate,
                    last_event_id=None,
                    updated_at=now,
                )
                session.add(row)
            for field, value in values.items():
                current = float(getattr(row, field))
                next_value = _clamp(current + float(value))
                if field == "valence":
                    next_value = _clamp(float(value), -1.0, 1.0)
                setattr(row, field, round(next_value, 6))
            row.last_event_id = event_id
            row.updated_at = now
            session.flush()
            return self._emotion_dict(row)

    def save_persona_bundle(
        self,
        *,
        world_id: str,
        character_id: str,
        bundle: dict[str, Any],
    ) -> dict[str, Any]:
        baseline = bundle["baseline"]
        state = bundle["state"]
        revision = int(bundle["baseline_revision"])
        if revision < 1:
            raise StorageError("invalid_persona", "Persona revision 必须大于 0")
        baseline_id = baseline["persona_id"]
        now = _datetime(baseline.get("updated_at", state["updated_at"]))
        with Session(self.engine) as session, session.begin():
            for active in session.scalars(
                select(PersonaBaselineRow).where(
                    PersonaBaselineRow.character_id == character_id,
                    PersonaBaselineRow.is_active.is_(True),
                )
            ).all():
                active.is_active = False
            baseline_row = session.get(
                PersonaBaselineRow,
                (baseline_id, revision),
            )
            if baseline_row is None:
                baseline_row = PersonaBaselineRow(
                    persona_id=baseline_id,
                    revision=revision,
                    character_id=character_id,
                    payload=dict(baseline),
                    is_default=bool(baseline.get("is_default")),
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                session.add(baseline_row)
            else:
                baseline_row.payload = dict(baseline)
                baseline_row.is_active = True
                baseline_row.updated_at = now
            state_row = session.get(
                PersonaStateRow,
                (world_id, character_id),
            )
            if state_row is None:
                state_row = PersonaStateRow(
                    world_id=world_id,
                    character_id=character_id,
                    baseline_persona_id=baseline_id,
                    baseline_revision=revision,
                    self_narrative=state["self_narrative"],
                    behavior_habits=list(state.get("behavior_habits", [])),
                    value_weights=dict(state.get("value_weights", {})),
                    interests=list(state.get("interests", [])),
                    active_goals=list(state.get("active_goals", [])),
                    updated_at=now,
                )
                session.add(state_row)
            else:
                state_row.baseline_persona_id = baseline_id
                state_row.baseline_revision = revision
                state_row.self_narrative = state["self_narrative"]
                state_row.behavior_habits = list(
                    state.get("behavior_habits", [])
                )
                state_row.value_weights = dict(state.get("value_weights", {}))
                state_row.interests = list(state.get("interests", []))
                state_row.active_goals = list(state.get("active_goals", []))
                state_row.updated_at = now
            for change in state.get("change_log", []):
                change_id = stable_id(
                    "pchg",
                    [
                        world_id,
                        character_id,
                        baseline_id,
                        revision,
                        change.get("changed_at"),
                        change.get("dimension"),
                        change.get("evidence"),
                    ],
                )
                if session.get(PersonaChangeLogRow, change_id):
                    continue
                session.add(
                    PersonaChangeLogRow(
                        change_id=change_id,
                        world_id=world_id,
                        character_id=character_id,
                        baseline_persona_id=baseline_id,
                        baseline_revision=revision,
                        dimension=change["dimension"],
                        delta=float(change.get("delta", 0.0)),
                        source_event_id=change.get("source_event_id"),
                        source=change.get("source", "player_baseline_edit"),
                        evidence=change.get("evidence", ""),
                        changed_at=_datetime(change["changed_at"]),
                    )
                )
            session.flush()
            self._assert_persona_consistency(
                session,
                world_id=world_id,
                character_id=character_id,
            )
            return {
                "persona_id": baseline_id,
                "revision": revision,
                "character_id": character_id,
                "changed_rows": len(state.get("change_log", [])),
            }

    def migrate_persona_json(
        self,
        path: Path | str,
        *,
        world_id: str = "world_qinghe_v1",
        character_id: str = "char_lin_cheng",
    ) -> dict[str, Any]:
        source = Path(path)
        if not source.is_file():
            raise StorageError("persona_json_missing", "Persona JSON 不存在")
        try:
            bundle = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise StorageError("persona_json_invalid", "Persona JSON 无效") from error
        if not isinstance(bundle, dict) or not isinstance(
            bundle.get("baseline"),
            dict,
        ):
            raise StorageError("persona_json_invalid", "Persona JSON 结构无效")
        return self.save_persona_bundle(
            world_id=world_id,
            character_id=character_id,
            bundle=bundle,
        )

    def get_persona_bundle(
        self,
        *,
        world_id: str,
        character_id: str,
    ) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            state = session.get(PersonaStateRow, (world_id, character_id))
            if not state:
                return None
            baseline = session.get(
                PersonaBaselineRow,
                (state.baseline_persona_id, state.baseline_revision),
            )
            if not baseline:
                raise StorageError(
                    "persona_inconsistent",
                    "Persona State 指向不存在的 Baseline",
                )
            changes = session.scalars(
                select(PersonaChangeLogRow)
                .where(
                    PersonaChangeLogRow.world_id == world_id,
                    PersonaChangeLogRow.character_id == character_id,
                )
                .order_by(PersonaChangeLogRow.changed_at)
            ).all()
            return {
                "baseline_revision": baseline.revision,
                "baseline": dict(baseline.payload),
                "state": {
                    "baseline_persona_id": state.baseline_persona_id,
                    "self_narrative": state.self_narrative,
                    "behavior_habits": list(state.behavior_habits),
                    "value_weights": dict(state.value_weights),
                    "interests": list(state.interests),
                    "active_goals": list(state.active_goals),
                    "change_log": [
                        {
                            "changed_at": _iso(change.changed_at),
                            "dimension": change.dimension,
                            "delta": change.delta,
                            "source_event_id": change.source_event_id,
                            "source": change.source,
                            "evidence": change.evidence,
                        }
                        for change in changes
                    ],
                    "updated_at": _iso(state.updated_at),
                },
            }

    def migrate_setup_json(
        self,
        root: Path | str,
        *,
        world_id: str = "world_qinghe_v1",
    ) -> dict[str, Any]:
        setup_root = Path(root)
        state_path = setup_root / "setup_state.json"
        key_path = setup_root / "deepseek_api_key.txt"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        configured = key_path.is_file() and bool(
            key_path.read_text(encoding="utf-8").strip()
        )
        now = _utc_now()
        with Session(self.engine) as session, session.begin():
            setup = session.get(SetupStateRow, world_id)
            if setup is None:
                setup = SetupStateRow(
                    world_id=world_id,
                    configured=configured,
                    provider="deepseek",
                    key_hint=state.get("key_hint"),
                    persona_configured=bool(state.get("persona_configured")),
                    world_ready=bool(
                        configured
                        and state.get("world_ready")
                        and state.get("persona_configured")
                    ),
                    completed_at=(
                        _datetime(state["completed_at"])
                        if state.get("completed_at")
                        else None
                    ),
                    updated_at=_datetime(now),
                )
                session.add(setup)
            else:
                setup.configured = configured
                setup.key_hint = state.get("key_hint")
                setup.persona_configured = bool(
                    state.get("persona_configured")
                )
                setup.world_ready = bool(
                    configured
                    and state.get("world_ready")
                    and state.get("persona_configured")
                )
                setup.completed_at = (
                    _datetime(state["completed_at"])
                    if state.get("completed_at")
                    else None
                )
                setup.updated_at = _datetime(now)
            for credential in session.scalars(
                select(DeepSeekCredentialRow).where(
                    DeepSeekCredentialRow.world_id == world_id,
                    DeepSeekCredentialRow.active.is_(True),
                )
            ).all():
                credential.active = False
                credential.rotated_at = _datetime(now)
            credential_id = None
            if configured:
                credential_id = stable_id(
                    "cred",
                    [world_id, state.get("key_hint"), "deepseek"],
                )
                existing = session.get(DeepSeekCredentialRow, credential_id)
                if existing:
                    existing.active = True
                    existing.rotated_at = _datetime(now)
                else:
                    session.add(
                        DeepSeekCredentialRow(
                            credential_id=credential_id,
                            world_id=world_id,
                            provider="deepseek",
                            key_ref=key_path.name,
                            key_hint=state.get("key_hint") or "sk-...",
                            active=True,
                            created_at=_datetime(now),
                            rotated_at=None,
                        )
                    )
            session.flush()
            return {
                "world_id": world_id,
                "configured": configured,
                "world_ready": setup.world_ready,
                "credential_id": credential_id,
            }

    def put_world_clock(
        self,
        *,
        world_id: str,
        logical_time: str,
        state_revision: int,
        last_tick_at: str,
        catch_up_mode: str,
        compressed_ticks: int,
        last_summary: str | None,
        updated_at: str,
    ) -> dict[str, Any]:
        with Session(self.engine) as session, session.begin():
            row = session.get(WorldClockRow, world_id)
            if row is None:
                row = WorldClockRow(
                    world_id=world_id,
                    logical_time=_datetime(logical_time),
                    state_revision=state_revision,
                    last_tick_at=_datetime(last_tick_at),
                    catch_up_mode=catch_up_mode,
                    compressed_ticks=compressed_ticks,
                    last_summary=last_summary,
                    updated_at=_datetime(updated_at),
                )
                session.add(row)
            else:
                row.logical_time = _datetime(logical_time)
                row.state_revision = state_revision
                row.last_tick_at = _datetime(last_tick_at)
                row.catch_up_mode = catch_up_mode
                row.compressed_ticks = compressed_ticks
                row.last_summary = last_summary
                row.updated_at = _datetime(updated_at)
            session.flush()
            return self._clock_dict(row)

    def get_world_clock(self, world_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(WorldClockRow, world_id)
            return self._clock_dict(row) if row else None

    def _assert_persona_consistency(
        self,
        session: Session,
        *,
        world_id: str,
        character_id: str,
    ) -> None:
        state = session.get(PersonaStateRow, (world_id, character_id))
        if not state:
            raise StorageError("persona_inconsistent", "Persona State 缺失")
        baseline = session.get(
            PersonaBaselineRow,
            (state.baseline_persona_id, state.baseline_revision),
        )
        if not baseline or not baseline.is_active:
            raise StorageError(
                "persona_inconsistent",
                "Persona State 未指向活动 Baseline",
            )
        mismatched = session.scalar(
            select(PersonaChangeLogRow).where(
                PersonaChangeLogRow.world_id == world_id,
                PersonaChangeLogRow.character_id == character_id,
                PersonaChangeLogRow.baseline_persona_id
                == state.baseline_persona_id,
                PersonaChangeLogRow.baseline_revision
                > state.baseline_revision,
            )
        )
        if mismatched:
            raise StorageError(
                "persona_inconsistent",
                "change log revision 超过当前 Persona State",
            )

    def _require_event(self, world_id: str, event_id: str) -> None:
        with Session(self.engine) as session:
            event = session.get(MemoryEventRow, event_id)
            if not event or event.world_id != world_id:
                raise StorageError(
                    "unknown_event",
                    "状态变化必须引用同一世界的正式事件",
                )

    @staticmethod
    def _validate_event(payload: dict[str, Any]) -> None:
        for field, minimum, maximum in (
            ("valence", -1.0, 1.0),
            ("intensity", 0.0, 1.0),
            ("importance", 0.0, 1.0),
            ("confidence", 0.0, 1.0),
        ):
            value = float(payload[field])
            if not minimum <= value <= maximum:
                raise StorageError(
                    "invalid_event",
                    f"{field} 超出允许范围",
                )

    @staticmethod
    def _event_dict(row: MemoryEventRow) -> dict[str, Any]:
        return {
            "event_id": row.event_id,
            "world_id": row.world_id,
            "actor_id": row.actor_id,
            "participants": list(row.participants),
            "location_id": row.location_id,
            "event_type": row.event_type,
            "occurred_at": _iso(row.occurred_at),
            "summary": row.summary,
            "valence": row.valence,
            "intensity": row.intensity,
            "importance": row.importance,
            "confidence": row.confidence,
            "visibility": row.visibility,
            "source": row.source,
            "dedupe_key": row.dedupe_key,
            "metadata": dict(row.metadata_document),
        }

    @staticmethod
    def _relationship_dict(row: RelationshipStateRow) -> dict[str, Any]:
        return {
            "relationship_id": row.relationship_id,
            "world_id": row.world_id,
            "from_character_id": row.from_character_id,
            "to_character_id": row.to_character_id,
            "affection": row.affection,
            "trust": row.trust,
            "familiarity": row.familiarity,
            "warmth": row.warmth,
            "tension": row.tension,
            "last_event_id": row.last_event_id,
            "updated_at": _iso(row.updated_at),
        }

    @staticmethod
    def _emotion_dict(row: EmotionStateRow) -> dict[str, Any]:
        return {
            "world_id": row.world_id,
            "character_id": row.character_id,
            "valence": row.valence,
            "arousal": row.arousal,
            "energy": row.energy,
            "stress": row.stress,
            "curiosity": row.curiosity,
            "decay_rate": row.decay_rate,
            "last_event_id": row.last_event_id,
            "updated_at": _iso(row.updated_at),
        }

    @staticmethod
    def _clock_dict(row: WorldClockRow) -> dict[str, Any]:
        return {
            "world_id": row.world_id,
            "logical_time": _iso(row.logical_time),
            "state_revision": row.state_revision,
            "last_tick_at": _iso(row.last_tick_at),
            "catch_up_mode": row.catch_up_mode,
            "compressed_ticks": row.compressed_ticks,
            "last_summary": row.last_summary,
            "updated_at": _iso(row.updated_at),
        }


def _datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _datetime(value).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))
