from __future__ import annotations

from datetime import datetime, timedelta

from app.school import (
    CLASSROOM_ID,
    GatewayStudyProvider,
    SCHOOL_START,
    SchoolAutonomyService,
    StudyGeneration,
    WORLD_TIMEZONE,
)
from app.local_state import LocalWorldStore
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"
DAY = datetime(2026, 11, 7, 9, 1, tzinfo=WORLD_TIMEZONE)


class CountingProvider:
    def __init__(self, *, fail=False, over_budget=False):
        self.calls = 0
        self.fail = fail
        self.over_budget = over_budget

    def generate(
        self,
        *,
        curriculum,
        token_budget,
        operation_id,
        budget_date,
    ):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider unavailable")
        return StudyGeneration(
            text=f"今天学习了{curriculum['theme']}。",
            input_tokens=token_budget if self.over_budget else 80,
            output_tokens=40,
            provider="fake",
            model="fake-v1",
        )


class FakeGateway:
    def __init__(self):
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        return {
            "status": "succeeded",
            "text": "我今天更理解倾听和回应之间的区别。",
            "provider": "fake-llm",
            "model": "fake-study-v1",
            "usage": {"input_tokens": 90, "output_tokens": 36},
        }


def make_service(tmp_path, **kwargs):
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'school.db').as_posix()}"
    )
    repository = ProductRepository(engine)
    service = SchoolAutonomyService(repository, **kwargs)
    return engine, repository, service


def test_school_daily_flow_is_one_session_one_generation(tmp_path) -> None:
    provider = CountingProvider()
    engine, repository, service = make_service(tmp_path, provider=provider)
    try:
        scheduled = service.tick(DAY)
        assert scheduled["status"] == "walking"
        assert scheduled["session"]["status"] == "scheduled"

        started = service.tick(DAY + timedelta(minutes=6))
        assert started["status"] == "running"
        assert started["session"]["input_tokens"] + started[
            "session"
        ]["output_tokens"] <= started["session"]["token_budget"]
        assert started["session"]["reflection_memory_id"].startswith("evt_")
        event = repository.get_memory_event(
            started["session"]["reflection_memory_id"]
        )
        assert event["visibility"] == "private"
        assert event["source"] == "school"
        assert provider.calls == 1

        repeated = service.tick(DAY + timedelta(minutes=10))
        assert provider.calls == 1
        assert repeated["session"]["reflection_memory_id"] == event["event_id"]

        completed = service.tick(DAY + timedelta(minutes=31))
        assert completed["status"] == "completed"
        assert completed["session"]["ended_at"]

        restarted = SchoolAutonomyService(repository, provider=provider)
        recovered = restarted.tick(DAY + timedelta(minutes=32))
        assert recovered["status"] == "completed"
        assert provider.calls == 1
    finally:
        engine.dispose()


def test_school_presence_exposes_state_not_notes(tmp_path) -> None:
    engine, _repository, service = make_service(tmp_path)
    try:
        service.tick(DAY)
        walking = service.presence_for_tick(
            logical_time=(DAY + timedelta(minutes=1)).isoformat(),
            revision=51,
        )
        assert walking["location_id"] == CLASSROOM_ID
        assert walking["animation"] == "enter_place"
        assert walking["moving"] is True
        assert "summary" not in walking

        service.tick(DAY + timedelta(minutes=6))
        studying = service.presence_for_tick(
            logical_time=(DAY + timedelta(minutes=7)).isoformat(),
            revision=52,
        )
        assert studying["animation"] == "study"
        assert studying["moving"] is False
        assert set(studying) == {
            "character_id",
            "x",
            "y",
            "location_id",
            "facing",
            "animation",
            "speed",
            "moving",
            "updated_at",
            "revision",
        }
    finally:
        engine.dispose()


def test_world_projection_exposes_study_state_without_notes(tmp_path) -> None:
    engine, _repository, service = make_service(tmp_path)
    try:
        service.tick(DAY)
        service.tick(DAY + timedelta(minutes=6))
        world = LocalWorldStore(school_service=service)
        world.state["world_date"] = DAY.date().isoformat()
        world.state["logical_time"] = (
            DAY + timedelta(minutes=7)
        ).isoformat()
        response = world.world()
        assert response.agent_presence.location_id == CLASSROOM_ID
        assert response.agent_presence.animation == "study"
        serialized = response.model_dump_json()
        assert "今天学习了" not in serialized
        assert "reflection_memory_id" not in serialized
    finally:
        engine.dispose()


def test_provider_failure_and_budget_overflow_use_static_fallback(
    tmp_path,
) -> None:
    for index, provider in enumerate(
        (CountingProvider(fail=True), CountingProvider(over_budget=True))
    ):
        case_root = tmp_path / str(index)
        case_root.mkdir()
        engine, repository, service = make_service(
            case_root,
            provider=provider,
        )
        try:
            service.tick(DAY)
            result = service.tick(DAY + timedelta(minutes=6))
            session = result["session"]
            assert session["reflection_memory_id"]
            assert (
                session["input_tokens"] + session["output_tokens"]
                <= session["token_budget"]
            )
            event = repository.get_memory_event(
                session["reflection_memory_id"]
            )
            assert event["metadata"]["provider"] == "local-static"
        finally:
            engine.dispose()


def test_gateway_provider_is_called_once_per_daily_session(tmp_path) -> None:
    gateway = FakeGateway()
    engine, repository, service = make_service(
        tmp_path,
        provider=GatewayStudyProvider(gateway),
    )
    try:
        service.tick(DAY)
        first = service.tick(DAY + timedelta(minutes=6))
        second = service.tick(DAY + timedelta(minutes=7))
        assert first["session"]["input_tokens"] == 90
        assert first["session"]["output_tokens"] == 36
        assert len(gateway.calls) == 1
        assert second["session"]["reflection_memory_id"] == first[
            "session"
        ]["reflection_memory_id"]
        assert gateway.calls[0].template_id == "study_reflection"
        assert gateway.calls[0].interface == "school"
    finally:
        engine.dispose()


def test_previous_day_session_is_missed_not_replayed(tmp_path) -> None:
    engine, repository, service = make_service(tmp_path)
    try:
        service.tick(DAY)
        next_day = DAY + timedelta(days=1)
        result = service.tick(
            next_day.replace(hour=10, minute=0)
        )
        previous = repository.get_study_session(
            world_id=WORLD_ID,
            world_date=DAY.date().isoformat(),
            character_id=CHARACTER_ID,
        )
        assert previous["status"] == "missed"
        assert result["missed"] == 1
        assert result["session"]["world_date"] == next_day.date().isoformat()
    finally:
        engine.dispose()


def test_school_does_not_start_before_nine(tmp_path) -> None:
    engine, repository, service = make_service(tmp_path)
    try:
        before = DAY.replace(hour=8, minute=0)
        result = service.tick(before)
        assert result["status"] == "not_due"
        assert repository.get_study_session(
            world_id=WORLD_ID,
            world_date=before.date().isoformat(),
            character_id=CHARACTER_ID,
        ) is None
        assert SCHOOL_START.hour == 9
    finally:
        engine.dispose()
