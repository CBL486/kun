from __future__ import annotations

import json
from pathlib import Path

from rpg_llm.models import ProviderRequest
from rpg_llm.pricing import PRICE_VERSIONS
from rpg_llm.providers import OpenAICompatibleProvider
from rpg_llm.runtime import (
    DEEPSEEK_PRICE_VERSION,
    LlmRuntimeConfig,
    build_gateway,
)
from rpg_orm.migrations import create_database_engine


class FakeResponse:
    status_code = 200

    def __init__(self, content: str):
        self.content = content

    def json(self):
        return {
            "id": "deepseek-response-1",
            "model": "deepseek-flash",
            "choices": [{"message": {"content": self.content}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 40},
        }


class FakeClient:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.content)


def provider_request(template_id: str) -> ProviderRequest:
    return ProviderRequest(
        operation_id="op_deepseek_test",
        request_id="llmreq_deepseek_test",
        template_id=template_id,
        template_version="test-v1",
        prompt="return JSON",
        max_output_tokens=400,
    )


def test_deepseek_runtime_config_uses_current_model_and_hides_key(monkeypatch) -> None:
    monkeypatch.setenv("AIWORLD_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("AIWORLD_LLM_API_KEY", "deepseek-test-secret")
    monkeypatch.delenv("AIWORLD_LLM_MODEL", raising=False)
    config = LlmRuntimeConfig.from_env()
    assert config.provider == "deepseek"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-flash"
    assert config.price_version == DEEPSEEK_PRICE_VERSION
    assert config.safe_summary()["api_key_configured"] is True
    assert "deepseek-test-secret" not in repr(config)


def test_deepseek_flash_price_version_is_conservative_peak_rate() -> None:
    price = PRICE_VERSIONS[DEEPSEEK_PRICE_VERSION]
    assert str(price.input_cny_per_million) == "2.16"
    assert str(price.output_cny_per_million) == "8.64"


def test_deepseek_provider_disables_thinking_and_requests_json() -> None:
    client = FakeClient(
        json.dumps(
            {
                "event": "公开事件摘要。",
                "feeling": "林澄觉得今天很充实。",
                "reflection": "先核对事实，再安排明天。",
            },
            ensure_ascii=False,
        )
    )
    provider = OpenAICompatibleProvider(
        base_url="https://api.deepseek.com",
        model="deepseek-flash",
        api_key="test-key",
        client=client,
        provider_name="deepseek",
        json_mode=True,
        extra_body={"thinking": {"type": "disabled"}},
    )
    response = provider.complete(provider_request("daily_share"))
    _, kwargs = client.calls[0]
    assert kwargs["json"]["response_format"] == {"type": "json_object"}
    assert kwargs["json"]["thinking"] == {"type": "disabled"}
    assert response.provider == "deepseek"
    assert response.model == "deepseek-flash"
    assert response.structured_candidate is None
    assert response.text["event"] == "公开事件摘要。"


def test_action_candidate_json_remains_structured_candidate() -> None:
    client = FakeClient(
        json.dumps(
            {
                "action_type": "rest",
                "target_id": None,
                "parameters": {},
                "confidence": 0.7,
            }
        )
    )
    provider = OpenAICompatibleProvider(
        base_url="https://api.deepseek.com",
        model="deepseek-flash",
        api_key="test-key",
        client=client,
        provider_name="deepseek",
        json_mode=True,
        extra_body={"thinking": {"type": "disabled"}},
    )
    response = provider.complete(provider_request("action_candidate"))
    assert response.structured_candidate["action_type"] == "rest"


def test_runtime_builds_deepseek_gateway(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AIWORLD_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("AIWORLD_LLM_API_KEY", "test-key")
    monkeypatch.setenv("AIWORLD_LLM_MAX_COST_CNY", "0.25")
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'runtime.db').as_posix()}"
    )
    try:
        gateway, config = build_gateway(engine)
        assert isinstance(gateway.provider, OpenAICompatibleProvider)
        assert gateway.provider.provider_name == "deepseek"
        assert gateway.provider.json_mode is True
        assert gateway.price.version == DEEPSEEK_PRICE_VERSION
        assert gateway.budget_policy.max_cost_cny == config.max_cost_cny
    finally:
        engine.dispose()
