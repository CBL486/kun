"""Mock and OpenAI-compatible provider implementations."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

import httpx

from rpg_sim.ids import digest

from .errors import ProviderError, ProviderUnavailable
from .models import ProviderRequest, ProviderResponse


class LlmProvider(Protocol):
    def complete(self, request: ProviderRequest) -> ProviderResponse: ...


class MockProvider:
    def __init__(
        self,
        *,
        seed: int = 20261028,
        failures_before_success: int = 0,
        unavailable: bool = False,
    ):
        self.seed = seed
        self.failures_before_success = failures_before_success
        self.unavailable = unavailable
        self.calls = 0

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        if self.unavailable:
            raise ProviderUnavailable()
        if self.calls <= self.failures_before_success:
            raise ProviderError("模拟传输失败")
        if request.template_id == "daily_share":
            text: Any = {
                "event": "今天整理了公开事件。",
                "feeling": "林澄觉得事情正在逐步变清楚。",
                "reflection": "先核对事实，再决定下一步。",
            }
            structured = None
        elif request.template_id == "action_candidate":
            text = "按当前公开状态保持原计划。"
            structured = {
                "action_type": "rest",
                "target_id": None,
                "parameters": {},
                "confidence": 0.7,
            }
        else:
            text = (
                "留言已收下，会留到下一个合法时段再考虑回应。"
                f"（mock-{digest([self.seed, request.request_id])[:8]}）"
            )
            structured = None
        return ProviderResponse(
            text=text,
            structured_candidate=structured,
            input_tokens=max(1, len(request.prompt) // 4),
            output_tokens=max(1, len(json.dumps(text, ensure_ascii=False)) // 4),
            provider="mock",
            model="mock-rule-v1",
            provider_request_id=request.request_id,
        )


class OpenAICompatibleProvider:
    """Thin real-provider skeleton with mandatory local credentials."""

    provider_name = "openai-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._api_key = api_key or os.environ.get("AIWORLD_LLM_API_KEY")
        self.client = client or httpx.Client(timeout=timeout_seconds)

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if not self._api_key:
            raise ProviderUnavailable()
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Idempotency-Key": request.request_id,
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": request.max_output_tokens,
            },
        )
        if response.status_code >= 500:
            raise ProviderError("模型供应商暂时不可用")
        if response.status_code >= 400:
            raise ProviderError(
                "模型请求被拒绝",
                transient=False,
            )
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        structured = None
        text: Any = content
        if isinstance(content, str):
            stripped = content.strip()
            if stripped.startswith("{"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, dict):
                        structured = parsed
                        text = parsed.get("text", stripped)
                except json.JSONDecodeError:
                    pass
        usage = payload.get("usage", {})
        provider_id = payload.get("id") or request.request_id
        return ProviderResponse(
            text=text,
            structured_candidate=structured,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            provider=self.provider_name,
            model=payload.get("model", self.model),
            provider_request_id=str(provider_id),
        )
