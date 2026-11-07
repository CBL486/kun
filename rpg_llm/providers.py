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
        elif request.template_id == "study_reflection":
            text = (
                "今天的学习让我更愿意先听清楚，再理解自己的感受与边界。"
            )
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
        provider_name: str | None = None,
        json_mode: bool = False,
        extra_body: dict[str, Any] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._api_key = api_key or os.environ.get("AIWORLD_LLM_API_KEY")
        self.client = client or httpx.Client(timeout=timeout_seconds)
        if provider_name:
            self.provider_name = provider_name
        self.json_mode = json_mode
        self.extra_body = dict(extra_body or {})

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if not self._api_key:
            raise ProviderUnavailable()
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_output_tokens,
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        payload.update(self.extra_body)
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Idempotency-Key": request.request_id,
                },
                json=payload,
            )
        except httpx.TimeoutException as error:
            raise ProviderError(
                "模型供应商请求超时",
                transient=True,
                code="provider_transport_error",
            ) from error
        except httpx.ConnectError as error:
            raise ProviderError(
                "模型供应商网络连接失败",
                transient=True,
                code="provider_transport_error",
            ) from error
        except httpx.NetworkError as error:
            raise ProviderError(
                "模型供应商网络连接失败",
                transient=True,
                code="provider_transport_error",
            ) from error
        except httpx.HTTPError as error:
            raise ProviderError(
                "模型供应商 HTTP 传输失败",
                transient=True,
                code="provider_transport_error",
            ) from error
        if response.status_code >= 500:
            raise ProviderError(
                "模型供应商暂时不可用",
                transient=True,
                code="provider_server_error",
            )
        if response.status_code in {401, 403}:
            raise ProviderError(
                "模型供应商鉴权失败",
                transient=False,
                code="provider_auth_error",
            )
        if response.status_code >= 400:
            raise ProviderError(
                "模型请求被拒绝",
                transient=False,
                code="provider_request_rejected",
            )
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as error:
            raise ProviderError(
                "模型供应商返回了无法解析的 JSON",
                transient=False,
                code="provider_invalid_response",
            ) from error
        try:
            content = payload["choices"][0]["message"]["content"]
            if not isinstance(content, (str, dict)):
                raise TypeError("content type invalid")
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderError(
                "模型供应商响应缺少 choices/message/content",
                transient=False,
                code="provider_invalid_response",
            ) from error
        structured = None
        text: Any = content
        if isinstance(content, str):
            stripped = content.strip()
            if stripped.startswith("{"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, dict):
                        if request.template_id == "action_candidate":
                            structured = parsed
                            text = parsed.get("text", stripped)
                        elif request.template_id == "daily_share":
                            text = parsed
                        else:
                            text = parsed.get("text", stripped)
                except json.JSONDecodeError:
                    pass
        usage = payload.get("usage", {})
        if not isinstance(usage, dict):
            raise ProviderError(
                "模型供应商 usage 结构非法",
                transient=False,
                code="provider_invalid_response",
            )
        provider_id = payload.get("id") or request.request_id
        try:
            return ProviderResponse(
                text=text,
                structured_candidate=structured,
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
                provider=self.provider_name,
                model=str(payload.get("model", self.model)),
                provider_request_id=str(provider_id),
            )
        except (TypeError, ValueError) as error:
            raise ProviderError(
                "模型供应商 token usage 非法",
                transient=False,
                code="provider_invalid_response",
            ) from error
