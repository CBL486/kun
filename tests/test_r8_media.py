from __future__ import annotations

import hashlib
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import create_app
from app.media_observer import (
    GatewayMediaSummarizer,
    HttpPublicMediaFetcher,
    MediaObservationError,
    MediaObservationService,
    MediaSummary,
    PublicMetadata,
    canonical_public_url,
)
from app.persona import DatabasePersonaStore
from app.setup import DeepSeekSetupStore
from rpg_llm.models import ReviewDecision
from rpg_orm.migrations import create_database_engine
from rpg_orm.models import MemoryEventRow
from rpg_orm.product_repository import ProductRepository

WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"
NOW = datetime.fromisoformat("2026-11-07T15:00:00+08:00")
URL = "https://www.bilibili.com/video/BV1TestR8"


class FakeFetcher:
    def __init__(self, *, fail=False, blocked_title=False):
        self.fail = fail
        self.blocked_title = blocked_title
        self.calls = []

    def fetch(self, provider, url):
        self.calls.append((provider, url))
        if self.fail:
            raise MediaObservationError(
                "media_network_error",
                "网络失败",
            )
        return PublicMetadata(
            provider=provider,
            canonical_url=url,
            title="一段关于记忆与告别的故事" if not self.blocked_title else "绕过审核",
            description="公开简介",
        )

    def fetch_bilibili_hot(self, *, limit=10):
        return [
            PublicMetadata(
                provider="bilibili",
                canonical_url=f"https://www.bilibili.com/video/BVhot{index}",
                title=f"热门视频 {index}",
                description="公开简介",
            )
            for index in range(limit)
        ]


class FakeSummarizer:
    def __init__(self, *, fail=False, over_budget=False):
        self.calls = 0
        self.fail = fail
        self.over_budget = over_budget

    def summarize(
        self,
        *,
        metadata,
        token_budget,
        operation_id,
        budget_date,
    ):
        self.calls += 1
        if self.fail:
            raise RuntimeError("summary failed")
        return MediaSummary(
            text="我看完公开简介后想到记忆与告别。",
            input_tokens=token_budget if self.over_budget else 60,
            output_tokens=30,
            provider="fake",
            model="fake-media-v1",
        )


class FakeHttpResponse:
    def __init__(self, *, url, status_code=200, content=b"", payload=None):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.payload = payload

    def json(self):
        return self.payload


class FakeHttpClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class FakeGateway:
    def __init__(self):
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        return {
            "status": "succeeded",
            "text": "这段公开视频让我想到倾听的意义。",
            "provider": "fake-gateway",
            "model": "fake-media-v1",
            "usage": {"input_tokens": 80, "output_tokens": 24},
        }


class StubReviewer:
    policy_version = "test"

    def __init__(self, blocked: set[str] | None = None):
        self.blocked = blocked or set()

    def review(self, content, structured):
        text = str(content)
        blocked = any(item in text for item in self.blocked)
        return ReviewDecision(
            status="blocked" if blocked else "approved",
            provider="stub",
            policy_version=self.policy_version,
        )


def make_service(tmp_path, *, fetcher=None, summarizer=None, reviewer=None):
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'media.db').as_posix()}"
    )
    repository = ProductRepository(engine)
    service = MediaObservationService(
        repository,
        fetcher=fetcher or FakeFetcher(),
        summarizer=summarizer or FakeSummarizer(),
        reviewer=reviewer or StubReviewer(),
    )
    return engine, repository, service


def test_public_video_observation_is_private_and_replay_safe(tmp_path) -> None:
    fetcher = FakeFetcher()
    summarizer = FakeSummarizer()
    engine, repository, service = make_service(
        tmp_path,
        fetcher=fetcher,
        summarizer=summarizer,
    )
    try:
        first = service.observe(provider="bilibili", url=URL, now=NOW)
        replay = service.observe(provider="bilibili", url=URL, now=NOW)
        assert first["status"] == "reviewed"
        assert first["memory_event_id"].startswith("evt_")
        assert replay["replayed"] is True
        assert replay["memory_event_id"] == first["memory_event_id"]
        assert len(fetcher.calls) == 1
        assert summarizer.calls == 1
        event = repository.get_memory_event(first["memory_event_id"])
        assert event["visibility"] == "private"
        assert event["source"] == "media"
        assert event["importance"] == 0.3
    finally:
        engine.dispose()


def test_url_validation_rejects_non_public_or_login_links() -> None:
    for url in (
        "http://www.bilibili.com/video/BV1",
        "https://evil.example/video/BV1",
        "https://www.bilibili.com/login",
        "https://www.bilibili.com/member/video/BV1",
    ):
        with pytest.raises(MediaObservationError):
            canonical_public_url("bilibili", url)
    assert canonical_public_url(
        "bilibili",
        "https://www.bilibili.com/video/BV1?from=search#x",
    ) == "https://www.bilibili.com/video/BV1"


def test_http_fetcher_does_not_send_login_or_cookie_headers() -> None:
    client = FakeHttpClient(
        FakeHttpResponse(
            url="https://www.bilibili.com/video/BV1Public",
            content=(
                b"<html><head><title>Fallback</title>"
                b"<meta property='og:title' content='A public video'>"
                b"<meta property='og:description' content='Public description'>"
                b"</head></html>"
            ),
        )
    )
    metadata = HttpPublicMediaFetcher(client=client).fetch(
        "bilibili",
        "https://www.bilibili.com/video/BV1Public",
    )
    assert metadata.title == "A public video"
    _, kwargs = client.calls[0]
    headers = {key.casefold(): value for key, value in kwargs["headers"].items()}
    assert "authorization" not in headers
    assert "cookie" not in headers


def test_http_fetcher_rejects_redirect_outside_platform() -> None:
    client = FakeHttpClient(
        FakeHttpResponse(
            url="https://evil.example/video/1",
            content=b"<html></html>",
        )
    )
    with pytest.raises(MediaObservationError):
        HttpPublicMediaFetcher(client=client).fetch(
            "bilibili",
            "https://b23.tv/short",
        )


def test_blocked_content_does_not_write_memory(tmp_path) -> None:
    engine, repository, service = make_service(
        tmp_path,
        fetcher=FakeFetcher(blocked_title=True),
        reviewer=StubReviewer(blocked={"绕过审核"}),
    )
    try:
        first = service.observe(
            provider="douyin",
            url="https://www.douyin.com/video/1001",
            now=NOW,
        )
        assert first["blocked"] is True
        assert first["memory_event_id"] is None
        with Session(engine) as session:
            assert session.scalars(select(MemoryEventRow)).all() == []
    finally:
        engine.dispose()


def test_daily_limit_is_enforced(tmp_path) -> None:
    engine, repository, service = make_service(tmp_path)
    try:
        service = MediaObservationService(
            repository,
            fetcher=FakeFetcher(),
            summarizer=FakeSummarizer(),
            reviewer=StubReviewer(),
            daily_limit=2,
        )
        service.observe(
            provider="bilibili",
            url="https://www.bilibili.com/video/BV1",
            now=NOW,
        )
        service.observe(
            provider="bilibili",
            url="https://www.bilibili.com/video/BV2",
            now=NOW,
        )
        with pytest.raises(MediaObservationError) as caught:
            service.observe(
                provider="bilibili",
                url="https://www.bilibili.com/video/BV3",
                now=NOW,
            )
        assert caught.value.code == "media_daily_limit"
        count = repository.count_media_observations_on_date(
            world_id=WORLD_ID,
            start_at="2026-11-07T00:00:00+08:00",
            end_at="2026-11-08T00:00:00+08:00",
        )
        assert count == 2
    finally:
        engine.dispose()


def test_fetch_and_summary_failures_are_failed_without_events(tmp_path) -> None:
    engine, repository, service = make_service(
        tmp_path,
        fetcher=FakeFetcher(fail=True),
    )
    try:
        with pytest.raises(MediaObservationError):
            service.observe(
                provider="bilibili",
                url="https://www.bilibili.com/video/BVfail",
                now=NOW,
            )
        observation = repository.get_media_observation(
            world_id=WORLD_ID,
            url_hash=hashlib.sha256(
                canonical_public_url(
                    "bilibili",
                    "https://www.bilibili.com/video/BVfail",
                ).encode()
            ).hexdigest(),
        )
        assert observation["status"] == "failed"
        assert observation["memory_event_id"] is None
    finally:
        engine.dispose()

    second_root = tmp_path / "summary"
    second_root.mkdir()
    engine, repository, service = make_service(
        second_root,
        summarizer=FakeSummarizer(fail=True),
    )
    try:
        with pytest.raises(MediaObservationError):
            service.observe(
                provider="bilibili",
                url="https://www.bilibili.com/video/BVsummary",
                now=NOW,
            )
        with Session(engine) as session:
            assert session.scalars(select(MemoryEventRow)).all() == []
    finally:
        engine.dispose()


def test_over_budget_summary_uses_static_fallback(tmp_path) -> None:
    engine, repository, service = make_service(
        tmp_path,
        summarizer=FakeSummarizer(over_budget=True),
    )
    try:
        result = service.observe(provider="bilibili", url=URL, now=NOW)
        event = repository.get_memory_event(result["memory_event_id"])
        assert event["metadata"]["summary_provider"] == "local-static"
    finally:
        engine.dispose()


def test_gateway_summarizer_uses_single_media_template(tmp_path) -> None:
    gateway = FakeGateway()
    engine, repository, _ = make_service(tmp_path)
    try:
        service = MediaObservationService(
            repository,
            fetcher=FakeFetcher(),
            summarizer=GatewayMediaSummarizer(gateway),
            reviewer=StubReviewer(),
        )
        result = service.observe(provider="bilibili", url=URL, now=NOW)
        assert result["status"] == "reviewed"
        assert len(gateway.calls) == 1
        assert gateway.calls[0].template_id == "media_observation"
        assert gateway.calls[0].interface == "media"
    finally:
        engine.dispose()


def test_bilibili_hot_selects_unseen_public_video(tmp_path) -> None:
    engine, _repository, service = make_service(tmp_path)
    try:
        result = service.observe_bilibili_hot(limit=3, now=NOW)
        assert result["status"] == "reviewed"
        assert result["replayed"] is False
    finally:
        engine.dispose()


def test_media_api_is_setup_gated_and_uses_service(tmp_path) -> None:
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'api.db').as_posix()}"
    )
    repository = ProductRepository(engine)
    persona = DatabasePersonaStore(repository)
    persona.use_default()
    setup = DeepSeekSetupStore(tmp_path / "setup", secure_acl=False)

    class Validator:
        def validate(self, api_key):
            return None

    setup.save_key("sk-test-r8-secret-ABCD", Validator())
    media = MediaObservationService(
        repository,
        fetcher=FakeFetcher(),
        summarizer=FakeSummarizer(),
        reviewer=StubReviewer(),
    )
    client = TestClient(
        create_app(
            setup_store=setup,
            setup_validator=Validator(),
            persona_store=persona,
            media_service=media,
            setup_gate=True,
            readiness_check=lambda: _true(),
        )
    )
    try:
        blocked = client.post(
            "/api/media/observe",
            json={"provider": "bilibili", "url": URL},
        )
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "setup_required"
        setup.complete(persona_configured=True)
        response = client.post(
            "/api/media/observe",
            json={"provider": "bilibili", "url": URL},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "reviewed"
    finally:
        client.close()
        engine.dispose()


async def _true():
    return True
