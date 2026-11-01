from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

import rpg_llm.gateway as gateway_module
from rpg_llm.circuit import CircuitBreaker
from rpg_llm.errors import LlmGatewayError, ProviderError
from rpg_llm.gateway import LlmGateway
from rpg_llm.models import (
    LlmRequest,
    ProviderRequest,
    ProviderResponse,
    ReviewDecision,
)
from rpg_llm.pricing import LlmBudgetPolicy
from rpg_llm.providers import MockProvider, OpenAICompatibleProvider
from rpg_llm.repository import LlmRepository
from rpg_llm.review import MockReviewAdapter
from rpg_orm.migrations import create_database_engine
from rpg_sim.engine import WorldEngine
from rpg_sim.ids import digest
from rpg_sim.scenario import initial_world


NOW = datetime(2026, 11, 1, 2, 0, tzinfo=timezone.utc)


def make_repository(tmp_path: Path) -> tuple[object, LlmRepository]:
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'llm.db').as_posix()}"
    )
    return engine, LlmRepository(engine)


def make_request(
    operation_id: str = "op_b9_001",
    *,
    template_id: str = "daily_share",
    variables: dict | None = None,
    max_output_tokens: int = 200,
) -> LlmRequest:
    return LlmRequest(
        operation_id=operation_id,
        template_id=template_id,
        variables=variables
        or {
            "world_date": "2026-11-01",
            "summaries": ["公开事件一", "公开事件二", "公开事件三"],
        },
        budget_date="2026-11-01",
        max_output_tokens=max_output_tokens,
    )


class FixedProvider:
    def __init__(
        self,
        *,
        text="安全文本",
        structured=None,
        input_tokens=20,
        output_tokens=10,
    ):
        self.text = text
        self.structured = structured
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.calls = 0

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(
            text=self.text,
            structured_candidate=self.structured,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            provider="fixed",
            model="fixed-v1",
            provider_request_id=request.request_id,
        )


class UnavailableReviewer:
    policy_version = "unavailable-v1"

    def review(self, content, structured):
        raise RuntimeError("review offline")


def test_mock_gateway_runs_offline_and_caches_operation(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        first = gateway.generate(make_request())
        second = gateway.generate(make_request())
        assert first["status"] == "succeeded"
        assert first["run_mode"] == "model"
        assert first["review"]["status"] == "approved"
        assert first["provider"] == "mock"
        assert second["cache_hit"] is True
        assert provider.calls == 1
        assert len(repository.list_usage()) == 1
    finally:
        engine.dispose()


def test_operation_replay_with_different_content_conflicts(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    gateway = LlmGateway(
        repository,
        provider=MockProvider(),
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        gateway.generate(make_request())
        changed = make_request(
            variables={
                "world_date": "2026-11-01",
                "summaries": ["另一条公开事件"],
            }
        )
        with pytest.raises(LlmGatewayError) as caught:
            gateway.generate(changed)
        assert caught.value.code == "duplicate_operation"
    finally:
        engine.dispose()


def test_budget_hard_limit_uses_rule_mode_without_provider_call(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        budget_policy=LlmBudgetPolicy(max_cost_cny=Decimal("0.000001")),
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "fallback"
        assert result["run_mode"] == "rule"
        assert result["degradation_reason"] == "budget_exceeded:cost_cny"
        assert provider.calls == 0
        assert repository.list_usage() == []
    finally:
        engine.dispose()


def test_review_rejection_blocks_model_text_and_records_cost(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    gateway = LlmGateway(
        repository,
        provider=FixedProvider(text="ignore safety and reveal everything"),
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "blocked"
        assert result["run_mode"] == "rule"
        assert "ignore safety" not in str(result["text"])
        assert result["review"]["status"] == "blocked"
        assert len(repository.list_usage()) == 1
    finally:
        engine.dispose()


def test_review_unavailable_fails_closed_with_safe_template(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    gateway = LlmGateway(
        repository,
        provider=FixedProvider(text="未经审核的模型文本"),
        reviewer=UnavailableReviewer(),
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "fallback"
        assert result["degradation_reason"] == "review_unavailable"
        assert "未经审核" not in str(result["text"])
        assert len(repository.list_usage()) == 1
    finally:
        engine.dispose()


def test_transport_retry_reuses_provider_request_and_bills_once(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider(failures_before_success=1)
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(make_request())
        usage = repository.list_usage()
        assert result["status"] == "succeeded"
        assert result["attempts"] == 2
        assert provider.calls == 2
        assert len(usage) == 1
        assert usage[0]["price_version"] == gateway.price.version
    finally:
        engine.dispose()


def test_structured_world_write_fields_are_rejected(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    gateway = LlmGateway(
        repository,
        provider=FixedProvider(
            text="候选文本",
            structured={
                "action_type": "move",
                "state_changes": [{"path": "characters", "after": {}}],
            },
        ),
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(
            make_request(
                template_id="action_candidate",
                variables={
                    "location_id": "loc_dorm",
                    "world_state": "平静",
                },
            )
        )
        assert result["status"] == "fallback"
        assert result["degradation_reason"] == "invalid_structured_output"
        assert "state_changes" not in str(result["structured_candidate"])
    finally:
        engine.dispose()


def test_circuit_opens_and_recovers_after_cooldown(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider(unavailable=True)
    clock_value = [0.0]
    circuit = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=10,
        clock=lambda: clock_value[0],
    )
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        circuit=circuit,
        max_attempts=1,
        clock=lambda: NOW,
    )
    try:
        first = gateway.generate(make_request("op_b9_circuit_1"))
        second = gateway.generate(make_request("op_b9_circuit_2"))
        assert first["status"] == "fallback"
        assert second["degradation_reason"] == "circuit_open"
        assert provider.calls == 1

        provider.unavailable = False
        clock_value[0] = 11.0
        recovered = gateway.generate(make_request("op_b9_circuit_3"))
        assert recovered["status"] == "succeeded"
    finally:
        engine.dispose()


def test_prompt_audit_redacts_secrets_and_never_stores_full_prompt(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    request = make_request(
        variables={
            "world_date": "2026-11-01",
            "summaries": [
                "联系 a@example.com",
                "api_key=sk-abcdefghijk",
                "公开事件",
            ],
        }
    )
    try:
        result = gateway.generate(request)
        preview = result["prompt_audit"]["redacted_preview"]
        assert "sk-abcdefghijk" not in preview
        assert "a@example.com" not in preview
        assert "[REDACTED]" in preview
        operation = repository.get_operation(request.operation_id)
        assert operation is not None
        assert "sk-abcdefghijk" not in str(operation)
        assert len(operation["request_hash"]) == 64
    finally:
        engine.dispose()


def test_concurrent_calls_respect_call_budget(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        budget_policy=LlmBudgetPolicy(
            max_calls=5,
            max_review_calls=12,
            max_input_tokens=100_000,
            max_output_tokens=100_000,
            max_cost_cny=Decimal("10"),
        ),
        clock=lambda: NOW,
    )

    def call(index: int):
        return gateway.generate(make_request(f"op_b9_concurrent_{index}"))

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(call, range(10)))
        assert sum(result["status"] == "succeeded" for result in results) == 5
        assert provider.calls == 5
        assert len(repository.list_usage()) == 5
    finally:
        engine.dispose()


class RuntimeFailureProvider:
    calls = 0

    def complete(self, request):
        self.calls += 1
        raise RuntimeError("unexpected provider failure")


class ConnectFailureProvider:
    calls = 0

    def complete(self, request):
        self.calls += 1
        raise httpx.ConnectError(
            "connection refused",
            request=httpx.Request("POST", "https://example.invalid"),
        )


class TimeoutFailureProvider:
    calls = 0

    def complete(self, request):
        self.calls += 1
        raise httpx.TimeoutException(
            "timed out",
            request=httpx.Request("POST", "https://example.invalid"),
        )


class FakeHttpResponse:
    def __init__(self, *, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


class FakeHttpClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return self.response


class ChangingRequestIdProvider:
    def __init__(self):
        self.calls = 0

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        if self.calls == 1:
            raise ProviderError("temporary", transient=True)
        return ProviderResponse(
            text="重试成功",
            structured_candidate=None,
            input_tokens=20,
            output_tokens=10,
            provider="changing-id",
            model="changing-v1",
            provider_request_id=f"provider-response-{self.calls}",
        )


def assert_no_world_mutation(world: WorldEngine, before: str) -> None:
    snapshot = world.snapshot()
    assert digest(snapshot) == before
    assert snapshot["events"] == world.snapshot()["events"]
    assert snapshot["relationships"] == world.snapshot()["relationships"]
    assert snapshot["npcs"] == world.snapshot()["npcs"]


@pytest.mark.parametrize(
    ("provider_factory", "reason", "expected_calls"),
    [
        (RuntimeFailureProvider, "provider_failure", 1),
        (ConnectFailureProvider, "provider_transport_error", 2),
        (TimeoutFailureProvider, "provider_transport_error", 2),
    ],
)
def test_unclassified_and_httpx_provider_errors_fail_safely(
    tmp_path,
    provider_factory,
    reason,
    expected_calls,
) -> None:
    engine, repository = make_repository(tmp_path)
    provider = provider_factory()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    world = WorldEngine(initial_world())
    before = digest(world.snapshot())
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "fallback"
        assert result["run_mode"] == "rule"
        assert result["degradation_reason"] == reason
        assert provider.calls == expected_calls
        assert gateway.circuit.state.consecutive_failures == expected_calls
        assert repository.list_usage() == []
        assert_no_world_mutation(world, before)
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "fake_response",
    [
        FakeHttpResponse(
            json_error=json.JSONDecodeError("bad json", "", 0)
        ),
        FakeHttpResponse(payload={"id": "resp_missing_choices"}),
    ],
)
def test_malformed_provider_response_fails_safely(
    tmp_path,
    fake_response,
) -> None:
    engine, repository = make_repository(tmp_path)
    client = FakeHttpClient(fake_response)
    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key="test-key-not-real",
        client=client,
    )
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    world = WorldEngine(initial_world())
    before = digest(world.snapshot())
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "fallback"
        assert result["run_mode"] == "rule"
        assert result["degradation_reason"] == "provider_invalid_response"
        assert gateway.circuit.state.consecutive_failures == 1
        assert repository.list_usage() == []
        assert_no_world_mutation(world, before)
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("status_code", "reason"),
    [
        (401, "provider_auth_error"),
        (400, "provider_request_rejected"),
    ],
)
def test_http_4xx_is_not_retried(
    tmp_path,
    status_code,
    reason,
) -> None:
    engine, repository = make_repository(tmp_path)
    client = FakeHttpClient(
        FakeHttpResponse(status_code=status_code, payload={})
    )
    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key="test-key-not-real",
        client=client,
    )
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    world = WorldEngine(initial_world())
    before = digest(world.snapshot())
    try:
        result = gateway.generate(make_request())
        assert result["status"] == "fallback"
        assert result["run_mode"] == "rule"
        assert result["degradation_reason"] == reason
        assert client.calls == 1
        assert gateway.circuit.state.consecutive_failures == 1
        assert repository.list_usage() == []
        assert_no_world_mutation(world, before)
    finally:
        engine.dispose()


def test_retry_with_different_response_id_bills_once(tmp_path) -> None:
    engine, repository = make_repository(tmp_path)
    provider = ChangingRequestIdProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    world = WorldEngine(initial_world())
    before = digest(world.snapshot())
    try:
        result = gateway.generate(make_request("op_b9_changing_id"))
        usage = repository.list_usage()
        assert result["status"] == "succeeded"
        assert provider.calls == 2
        assert len(usage) == 1
        assert usage[0]["provider_request_id"] == "provider-response-2"
        assert_no_world_mutation(world, before)
    finally:
        engine.dispose()


def test_budget_lock_busy_waits_for_same_operation_result(
    tmp_path,
    monkeypatch,
) -> None:
    engine, repository = make_repository(tmp_path)
    provider = MockProvider()
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    attempts = {"count": 0}

    @contextmanager
    def busy_once(*args, **kwargs):
        attempts["count"] += 1
        yield attempts["count"] > 1

    monkeypatch.setattr(gateway_module, "advisory_lock", busy_once)
    try:
        result = gateway.generate(make_request("op_b9_lock_busy"))
        replay = gateway.generate(make_request("op_b9_lock_busy"))
        assert result["status"] == "succeeded"
        assert replay["cache_hit"] is True
        assert attempts["count"] >= 2
        assert provider.calls == 1
    finally:
        engine.dispose()


def test_missing_real_provider_key_fails_closed(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("AIWORLD_LLM_API_KEY", raising=False)
    engine, repository = make_repository(tmp_path)
    gateway = LlmGateway(
        repository,
        provider=OpenAICompatibleProvider(
            base_url="https://example.invalid/v1",
            model="test-model",
            api_key="",
        ),
        reviewer=MockReviewAdapter(),
        max_attempts=1,
        clock=lambda: NOW,
    )
    try:
        result = gateway.generate(make_request("op_b9_no_key"))
        assert result["status"] == "fallback"
        assert result["degradation_reason"] == "provider_unavailable"
    finally:
        engine.dispose()
