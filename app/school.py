"""Daily school session, low-token study and observable presence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from rpg_sim.ids import digest, stable_id
from rpg_storage.errors import StorageError


WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"
CLASSROOM_ID = "loc_classroom"
CLASSROOM_POSITION = (960.0, 338.0)
WORLD_TIMEZONE = ZoneInfo("Asia/Shanghai")
SCHOOL_START = time(9, 0)
CLASSROOM_WALK_MINUTES = 5
STUDY_MINUTES = 30
TOKEN_BUDGET = 1_200

CURRICULA = (
    {
        "id": "curriculum_empathy_public_domain",
        "theme": "共情与告别",
        "summary": "阅读一段公版文学的情感主题摘要，练习辨认人物的需要与边界。",
    },
    {
        "id": "curriculum_memory_ethics",
        "theme": "记忆与责任",
        "summary": "阅读关于记忆、遗忘与责任的文章摘要，思考哪些事情值得长期保留。",
    },
    {
        "id": "curriculum_relationship_boundaries",
        "theme": "关系与边界",
        "summary": "分析一段关系中倾听、信任和拒绝的不同层次。",
    },
)


@dataclass(frozen=True)
class StudyGeneration:
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


class StudyProvider(Protocol):
    def generate(
        self,
        *,
        curriculum: dict[str, str],
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> StudyGeneration: ...


class StaticStudyProvider:
    """Deterministic low-cost fallback used in local mode and on provider failure."""

    def generate(
        self,
        *,
        curriculum: dict[str, str],
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> StudyGeneration:
        text = (
            f"今天学习“{curriculum['theme']}”。"
            "我发现自己更需要先听清楚，再决定如何回应；"
            "有些理解不是立刻得到的，而是在安静里慢慢成形。"
        )
        return StudyGeneration(
            text=text,
            input_tokens=min(token_budget, 80),
            output_tokens=min(max(0, token_budget - 80), 80),
            provider="local-static",
            model="study-static-v1",
        )


class GatewayStudyProvider:
    """Adapter that routes the single daily study reflection through B9 gateway."""

    def __init__(self, gateway: Any):
        self.gateway = gateway

    def generate(
        self,
        *,
        curriculum: dict[str, str],
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> StudyGeneration:
        from rpg_llm.models import LlmRequest

        result = self.gateway.generate(
            LlmRequest(
                operation_id=operation_id,
                template_id="study_reflection",
                variables={
                    "theme": curriculum["theme"],
                    "summary": curriculum["summary"],
                },
                budget_date=budget_date,
                max_output_tokens=min(300, token_budget),
                interface="school",
            )
        )
        usage = result.get("usage") or {}
        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            raise StorageError(
                "study_generation_invalid",
                "学习生成结果不是有效文本",
            )
        return StudyGeneration(
            text=text.strip()[:1_200],
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            provider=str(result.get("provider") or "local-rule"),
            model=str(result.get("model") or "study-fallback-v1"),
        )


class SchoolAutonomyService:
    def __init__(
        self,
        repository: Any,
        *,
        provider: StudyProvider | None = None,
        world_id: str = WORLD_ID,
        character_id: str = CHARACTER_ID,
        token_budget: int = TOKEN_BUDGET,
    ):
        self.repository = repository
        self.provider = provider or StaticStudyProvider()
        self.world_id = world_id
        self.character_id = character_id
        self.token_budget = token_budget

    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        current = _local_time(now or datetime.now(WORLD_TIMEZONE))
        world_date = current.date().isoformat()
        missed = self.repository.mark_stale_study_sessions_missed(
            world_id=self.world_id,
            current_date=world_date,
            ended_at=current.isoformat(),
        )
        session = self.repository.get_study_session(
            world_id=self.world_id,
            world_date=world_date,
            character_id=self.character_id,
        )
        if session is None and current.time() >= SCHOOL_START:
            curriculum = CURRICULA[
                int(digest([world_date, self.character_id])[:2], 16)
                % len(CURRICULA)
            ]
            session = self.repository.create_study_session(
                study_session_id=stable_id(
                    "study",
                    [self.world_id, self.character_id, world_date],
                ),
                world_id=self.world_id,
                world_date=world_date,
                character_id=self.character_id,
                location_id=CLASSROOM_ID,
                started_at=current.isoformat(),
                curriculum_id=curriculum["id"],
                token_budget=self.token_budget,
            )
        if session is None:
            return {"status": "not_due", "missed": missed, "session": None}

        started = _parse_time(session["started_at"])
        if session["status"] == "scheduled":
            if current >= started + timedelta(
                minutes=CLASSROOM_WALK_MINUTES
            ):
                session = self.repository.update_study_session(
                    study_session_id=session["study_session_id"],
                    status="running",
                )
            else:
                return {
                    "status": "walking",
                    "missed": missed,
                    "session": session,
                }

        if session["status"] == "running":
            if session["reflection_memory_id"] is None:
                session = self._generate_reflection(session, current)
            if current >= started + timedelta(minutes=STUDY_MINUTES):
                session = self.repository.update_study_session(
                    study_session_id=session["study_session_id"],
                    status="completed",
                    ended_at=current.isoformat(),
                )
            return {
                "status": session["status"],
                "missed": missed,
                "session": session,
            }
        return {
            "status": session["status"],
            "missed": missed,
            "session": session,
        }

    def presence_for_tick(
        self,
        *,
        logical_time: str,
        revision: int,
    ) -> dict[str, Any] | None:
        current = _local_time(_parse_time(logical_time))
        session = self.repository.get_study_session(
            world_id=self.world_id,
            world_date=current.date().isoformat(),
            character_id=self.character_id,
        )
        if not session:
            return None
        if session["status"] == "scheduled":
            animation = "enter_place"
            moving = True
        elif session["status"] == "running":
            animation = "study"
            moving = False
        elif session["status"] == "completed":
            animation = "idle"
            moving = False
        else:
            return None
        return {
            "character_id": self.character_id,
            "x": CLASSROOM_POSITION[0],
            "y": CLASSROOM_POSITION[1],
            "location_id": CLASSROOM_ID,
            "facing": "down",
            "animation": animation,
            "speed": 60.0 if moving else 0.0,
            "moving": moving,
            "updated_at": logical_time,
            "revision": revision,
        }

    def _generate_reflection(
        self,
        session: dict[str, Any],
        current: datetime,
    ) -> dict[str, Any]:
        curriculum = next(
            item
            for item in CURRICULA
            if item["id"] == session["curriculum_id"]
        )
        try:
            generated = self.provider.generate(
                curriculum=curriculum,
                token_budget=session["token_budget"],
                operation_id=(
                    f"study:{session['study_session_id']}:reflection"
                ),
                budget_date=session["world_date"],
            )
        except Exception:
            generated = StaticStudyProvider().generate(
                curriculum=curriculum,
                token_budget=session["token_budget"],
                operation_id=(
                    f"study:{session['study_session_id']}:reflection"
                ),
                budget_date=session["world_date"],
            )
        if (
            generated.input_tokens + generated.output_tokens
            > session["token_budget"]
        ):
            generated = StaticStudyProvider().generate(
                curriculum=curriculum,
                token_budget=session["token_budget"],
                operation_id=(
                    f"study:{session['study_session_id']}:reflection"
                ),
                budget_date=session["world_date"],
            )
        event_id = stable_id(
            "evt",
            ["study_reflection", session["study_session_id"]],
        )
        self.repository.record_memory_event(
            {
                "event_id": event_id,
                "world_id": self.world_id,
                "actor_id": self.character_id,
                "participants": [self.character_id],
                "location_id": CLASSROOM_ID,
                "event_type": "school_reflection",
                "occurred_at": current.isoformat(),
                "summary": generated.text,
                "valence": 0.2,
                "intensity": 0.35,
                "importance": 0.55,
                "confidence": 1.0,
                "visibility": "private",
                "source": "school",
                "dedupe_key": f"school:{session['study_session_id']}:reflection",
                "metadata": {
                    "curriculum_id": curriculum["id"],
                    "provider": generated.provider,
                    "model": generated.model,
                },
            }
        )
        self.repository.update_emotion(
            event_id=event_id,
            world_id=self.world_id,
            character_id=self.character_id,
            values={"curiosity": 0.01, "stress": -0.005},
            updated_at=current.isoformat(),
        )
        return self.repository.update_study_session(
            study_session_id=session["study_session_id"],
            status="running",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
            reflection_memory_id=event_id,
        )


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _local_time(parsed)


def _local_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=WORLD_TIMEZONE)
    return value.astimezone(WORLD_TIMEZONE)
