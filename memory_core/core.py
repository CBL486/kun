"""SQLite 记忆读写、生命周期与召回。"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime
from typing import Any

from rpg_sim.ids import canonical_json, digest, stable_id

from .errors import ConflictError, NotFoundError, ScopeError, ValidationError
from .models import MemoryRecord, RecallResult, Scope

MEMORY_KINDS = {"event", "reflection", "summary", "relationship", "preference"}
STRENGTHEN_REASONS = {"share", "restatement", "scene_trigger", "flow", "manual"}
HALF_LIFE_DAYS = 14.0
ACTIVE_THRESHOLD = 0.3
FUZZY_THRESHOLD = 0.1


class MemoryCore:
    def append(
        self,
        conn: sqlite3.Connection,
        *,
        scope: Scope,
        dedupe_key: str,
        kind: str,
        source: str,
        content: str,
        source_event_id: str,
        importance: float,
        emotional_weight: float,
        confidence: float,
        strength: float,
        scene_tags: list[str],
        created_at: str,
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> tuple[MemoryRecord, bool]:
        scope.validate()
        if not dedupe_key or not source_event_id.startswith("evt_"):
            raise ValidationError("记忆必须包含去重键和正式来源事件 ID")
        if kind not in MEMORY_KINDS:
            raise ValidationError("记忆类型无效")
        if not source or not content:
            raise ValidationError("记忆来源和内容不能为空")
        for value, field in (
            (importance, "importance"),
            (emotional_weight, "emotional_weight"),
            (confidence, "confidence"),
            (strength, "strength"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValidationError(f"{field} 必须在 [0,1]")
        state = lifecycle_state(strength)
        stable_memory_id = memory_id or stable_id(
            "mem",
            [scope.scope_hash, dedupe_key],
        )
        existing = conn.execute(
            """
            SELECT * FROM memories
            WHERE scope_hash = ? AND dedupe_key = ?
            """,
            (scope.scope_hash, dedupe_key),
        ).fetchone()
        semantic = {
            "kind": kind,
            "source": source,
            "content": content,
            "source_event_id": source_event_id,
            "importance": round(importance, 6),
            "emotional_weight": round(emotional_weight, 6),
            "scene_tags": sorted(scene_tags),
        }
        if existing:
            existing_semantic = {
                "kind": existing["kind"],
                "source": existing["source"],
                "content": existing["content"],
                "source_event_id": existing["source_event_id"],
                "importance": round(existing["importance"], 6),
                "emotional_weight": round(existing["emotional_weight"], 6),
                "scene_tags": json.loads(existing["scene_tags_json"]),
            }
            if existing_semantic != semantic:
                raise ConflictError()
            return self._record_from_row(existing), True

        conn.execute(
            """
            INSERT INTO memories (
                memory_id, tenant_id, world_id, user_id, character_id,
                surface, conversation_id, conversation_key, scope_hash,
                kind, source, content, importance, emotional_weight,
                confidence, strength, scene_tags_json, created_at,
                last_accessed_at, last_strength_update, access_count,
                restated_count, locked, state, source_event_id,
                dedupe_key, metadata_json
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?,
                0, 0, 0, ?, ?, ?, ?
            )
            """,
            (
                stable_memory_id,
                scope.tenant_id,
                scope.world_id,
                scope.user_id,
                scope.character_id,
                scope.surface,
                scope.conversation_id,
                scope.conversation_key,
                scope.scope_hash,
                kind,
                source,
                content,
                importance,
                emotional_weight,
                confidence,
                strength,
                canonical_json(scene_tags),
                created_at,
                created_at,
                state,
                source_event_id,
                dedupe_key,
                canonical_json(metadata or {}),
            ),
        )
        row = conn.execute(
            "SELECT * FROM memories WHERE memory_id = ?",
            (stable_memory_id,),
        ).fetchone()
        return self._record_from_row(row), False

    def get(
        self,
        conn: sqlite3.Connection,
        memory_id: str,
        scope: Scope,
    ) -> MemoryRecord:
        row = conn.execute(
            """
            SELECT * FROM memories
            WHERE memory_id = ? AND scope_hash = ?
            """,
            (memory_id, scope.scope_hash),
        ).fetchone()
        if not row:
            raise NotFoundError()
        return self._record_from_row(row)

    def recall(
        self,
        conn: sqlite3.Connection,
        *,
        scope: Scope,
        current_time: str,
        query_tags: list[str] | None = None,
        max_items: int = 5,
        max_tokens: int = 1_000,
        include_fuzzy: bool = True,
    ) -> list[RecallResult]:
        if max_items < 0 or max_tokens < 1:
            raise ValidationError("召回预算无效")
        scope.validate()
        self.decay(conn, scope=scope, current_time=current_time)
        states = ["active", "fuzzy"] if include_fuzzy else ["active"]
        placeholders = ",".join("?" for _ in states)
        rows = conn.execute(
            f"""
            SELECT * FROM memories
            WHERE scope_hash = ? AND state IN ({placeholders})
            ORDER BY memory_id
            """,
            (scope.scope_hash, *states),
        ).fetchall()
        query = set(query_tags or [])
        now = datetime.fromisoformat(current_time)
        ranked: list[RecallResult] = []
        for row in rows:
            memory = self._record_from_row(row)
            tags = set(memory.scene_tags)
            relevance = (
                len(tags & query) / len(query)
                if query
                else 0.25
            )
            age_days = max(
                0.0,
                (now - datetime.fromisoformat(memory.created_at)).total_seconds()
                / 86400,
            )
            recency = 0.5 ** (age_days / HALF_LIFE_DAYS)
            access_bonus = min(memory.access_count / 5, 1.0)
            breakdown = {
                "relevance": round(relevance * 0.40, 6),
                "strength": round(memory.strength * 0.20, 6),
                "importance": round(memory.importance * 0.15, 6),
                "emotional_weight": round(memory.emotional_weight * 0.10, 6),
                "recency": round(recency * 0.10, 6),
                "access_bonus": round(access_bonus * 0.05, 6),
            }
            score = round(sum(breakdown.values()), 6)
            reasons = ["scope_exact", f"state_{memory.state}"]
            if tags & query:
                reasons.append("tag_match")
            if memory.access_count:
                reasons.append("previously_accessed")
            ranked.append(
                RecallResult(
                    memory=memory,
                    score=score,
                    score_breakdown=breakdown,
                    reason_codes=reasons,
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.memory.memory_id))
        selected = []
        used_tokens = 0
        for result in ranked:
            tokens = estimate_tokens(result.memory.content)
            if len(selected) >= max_items:
                break
            if used_tokens + tokens > max_tokens:
                continue
            selected.append(result)
            used_tokens += tokens
        for result in selected:
            conn.execute(
                """
                UPDATE memories
                SET last_accessed_at = ?, access_count = access_count + 1
                WHERE memory_id = ?
                """,
                (current_time, result.memory.memory_id),
            )
        return selected

    def decay(
        self,
        conn: sqlite3.Connection,
        *,
        scope: Scope,
        current_time: str,
    ) -> dict[str, int]:
        now = datetime.fromisoformat(current_time)
        rows = conn.execute(
            "SELECT * FROM memories WHERE scope_hash = ?",
            (scope.scope_hash,),
        ).fetchall()
        counts = {"active": 0, "fuzzy": 0, "archived": 0}
        for row in rows:
            if row["locked"]:
                state = "active"
                strength = row["strength"]
            else:
                last = datetime.fromisoformat(row["last_strength_update"])
                elapsed_days = max(0.0, (now - last).total_seconds() / 86400)
                strength = row["strength"] * (
                    0.5 ** (elapsed_days / HALF_LIFE_DAYS)
                )
                strength = round(strength, 6)
                state = lifecycle_state(strength)
            conn.execute(
                """
                UPDATE memories
                SET strength = ?, state = ?, last_strength_update = ?
                WHERE memory_id = ?
                """,
                (round(strength, 6), state, current_time, row["memory_id"]),
            )
            counts[state] += 1
        return counts

    def strengthen(
        self,
        conn: sqlite3.Connection,
        *,
        memory_id: str,
        scope: Scope,
        operation_id: str,
        amount: float,
        reason: str,
        source_event_id: str,
        current_time: str,
    ) -> tuple[MemoryRecord, bool]:
        if reason not in STRENGTHEN_REASONS:
            raise ValidationError("强化理由无效")
        if not 0.0 < amount <= 0.2:
            raise ValidationError("单次强化必须在 (0,0.2]")
        if not source_event_id.startswith("evt_"):
            raise ValidationError("强化必须引用正式事件")
        existing_op = conn.execute(
            "SELECT * FROM memory_mutations WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        memory = self.get(conn, memory_id, scope)
        if existing_op:
            if (
                existing_op["memory_id"] != memory_id
                or existing_op["reason"] != reason
                or existing_op["source_event_id"] != source_event_id
                or round(existing_op["amount"], 6) != round(amount, 6)
            ):
                raise ConflictError("强化 operation 内容冲突")
            return memory, True
        strength = min(1.0, memory.strength + amount)
        state = lifecycle_state(strength)
        conn.execute(
            """
            UPDATE memories
            SET strength = ?, state = ?, last_strength_update = ?,
                restated_count = restated_count + 1
            WHERE memory_id = ?
            """,
            (round(strength, 6), state, current_time, memory_id),
        )
        conn.execute(
            """
            INSERT INTO memory_mutations (
                operation_id, memory_id, source_event_id, reason,
                amount, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (operation_id, memory_id, source_event_id, reason, amount, current_time),
        )
        return self.get(conn, memory_id, scope), False

    def set_locked(
        self,
        conn: sqlite3.Connection,
        *,
        memory_id: str,
        scope: Scope,
        locked: bool,
        current_time: str,
    ) -> MemoryRecord:
        memory = self.get(conn, memory_id, scope)
        state = "active" if locked else lifecycle_state(memory.strength)
        conn.execute(
            """
            UPDATE memories
            SET locked = ?, state = ?, last_strength_update = ?
            WHERE memory_id = ?
            """,
            (int(locked), state, current_time, memory_id),
        )
        return self.get(conn, memory_id, scope)

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            scope=Scope(
                tenant_id=row["tenant_id"],
                world_id=row["world_id"],
                user_id=row["user_id"],
                character_id=row["character_id"],
                surface=row["surface"],
                conversation_id=row["conversation_id"],
            ),
            kind=row["kind"],
            source=row["source"],
            content=row["content"],
            importance=row["importance"],
            emotional_weight=row["emotional_weight"],
            confidence=row["confidence"],
            strength=row["strength"],
            scene_tags=json.loads(row["scene_tags_json"]),
            created_at=row["created_at"],
            last_accessed_at=row["last_accessed_at"],
            last_strength_update=row["last_strength_update"],
            access_count=row["access_count"],
            restated_count=row["restated_count"],
            locked=bool(row["locked"]),
            state=row["state"],
            source_event_id=row["source_event_id"],
            dedupe_key=row["dedupe_key"],
            metadata=json.loads(row["metadata_json"]),
        )


def lifecycle_state(strength: float) -> str:
    if strength >= ACTIVE_THRESHOLD:
        return "active"
    if strength >= FUZZY_THRESHOLD:
        return "fuzzy"
    return "archived"


def estimate_tokens(content: str) -> int:
    chinese = sum(1 for char in content if "\u4e00" <= char <= "\u9fff")
    remaining = len(content) - chinese
    return max(1, chinese + math.ceil(remaining / 4))
