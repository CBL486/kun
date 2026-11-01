"""Governed model-call pipeline with review and hard-cost controls."""

from __future__ import annotations

import json
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable

import httpx

from rpg_scheduler.locks import advisory_lock
from rpg_sim.ids import stable_id

from .circuit import CircuitBreaker
from .errors import LlmGatewayError, ProviderError
from .fallback import rule_fallback
from .models import LlmRequest, ProviderRequest
from .pricing import DEFAULT_PRICE_VERSION, PRICE_VERSIONS, LlmBudgetPolicy
from .prompts import PROMPT_TEMPLATES, prompt_audit
from .providers import LlmProvider
from .repository import LlmRepository
from .review import ReviewAdapter


STRUCTURED_ALLOWED_KEYS = {
    "summary",
    "action_type",
    "target_id",
    "parameters",
    "tone",
    "confidence",
}


class LlmGateway:
    def __init__(
        self,
        repository: LlmRepository,
        *,
        provider: LlmProvider,
        reviewer: ReviewAdapter,
        price_version: str = DEFAULT_PRICE_VERSION,
        budget_policy: LlmBudgetPolicy | None = None,
        max_attempts: int = 2,
        circuit: CircuitBreaker | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        if price_version not in PRICE_VERSIONS:
            raise ValueError(f"未知价格版本：{price_version}")
        self.repository = repository
        self.provider = provider
        self.reviewer = reviewer
        self.price = PRICE_VERSIONS[price_version]
        self.budget_policy = budget_policy or LlmBudgetPolicy()
        self.max_attempts = max_attempts
        self.circuit = circuit or CircuitBreaker()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._thread_lock = threading.RLock()

    def generate(self, request: LlmRequest) -> dict[str, Any]:
        started_at = time.perf_counter()
        deadline = time.monotonic() + 5.0
        with self._thread_lock:
            while True:
                with advisory_lock(
                    self.repository.engine,
                    f"llm-budget:{request.budget_date}",
                ) as acquired:
                    if acquired:
                        existing = self.repository.get_operation(
                            request.operation_id
                        )
                        if existing:
                            if (
                                existing["request_hash"]
                                != request.request_hash
                            ):
                                raise LlmGatewayError(
                                    "duplicate_operation",
                                    "同一 operation_id 的请求内容不一致",
                                )
                            result = deepcopy(existing["result"])
                            result["cache_hit"] = True
                            return result
                        return self._execute(request, started_at)
                if time.monotonic() >= deadline:
                    template = PROMPT_TEMPLATES.get(request.template_id)
                    if template is None:
                        return self._fallback_without_audit(
                            "budget_lock_busy",
                        )
                    prompt = template.render(request.variables)
                    audit = prompt_audit(template, prompt)
                    return self._save_fallback(
                        request,
                        template.version,
                        audit,
                        "budget_lock_busy",
                        started_at=started_at,
                    )
                time.sleep(0.02)

    def _execute(
        self,
        request: LlmRequest,
        started_at: float,
    ) -> dict[str, Any]:
        template = PROMPT_TEMPLATES.get(request.template_id)
        if template is None:
            raise LlmGatewayError(
                "prompt_template_unknown",
                "提示词模板未注册",
            )
        prompt = template.render(request.variables)
        audit = prompt_audit(template, prompt)
        estimated_input = max(1, len(prompt) // 4)
        if estimated_input > self.budget_policy.max_input_tokens_per_call:
            return self._save_fallback(
                request,
                template.version,
                audit,
                "input_token_limit",
                started_at=started_at,
            )
        if (
            request.max_output_tokens
            > self.budget_policy.max_output_tokens_per_call
        ):
            return self._save_fallback(
                request,
                template.version,
                audit,
                "output_token_limit",
                started_at=started_at,
            )
        worst_output = request.max_output_tokens
        prospective_cost = self.price.cost(
            input_tokens=estimated_input,
            output_tokens=worst_output,
            review_calls=1,
        )
        current = self.repository.usage_snapshot(request.budget_date)
        exceeded = self.budget_policy.exceeded_reason(
            current,
            prospective_input_tokens=estimated_input,
            prospective_output_tokens=worst_output,
            prospective_cost=prospective_cost,
            review_call=True,
        )
        if exceeded:
            return self._save_fallback(
                request,
                template.version,
                audit,
                f"budget_exceeded:{exceeded}",
                started_at=started_at,
            )
        if not self.circuit.allow():
            return self._save_fallback(
                request,
                template.version,
                audit,
                "circuit_open",
                started_at=started_at,
            )

        provider_request = ProviderRequest(
            operation_id=request.operation_id,
            request_id=stable_id(
                "llmreq",
                [request.operation_id, audit.prompt_sha256],
            ),
            template_id=template.template_id,
            template_version=template.version,
            prompt=prompt,
            max_output_tokens=worst_output,
        )
        response = None
        attempts = 0
        last_error = None
        for attempt_index in range(1, self.max_attempts + 1):
            attempts = attempt_index
            try:
                response = self.provider.complete(provider_request)
                self.circuit.record_success()
                break
            except ProviderError as error:
                last_error = error
                self.circuit.record_failure()
                if not error.transient:
                    break
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPError,
            ):
                last_error = ProviderError(
                    "模型供应商网络请求失败",
                    transient=True,
                    code="provider_transport_error",
                )
                self.circuit.record_failure()
            except Exception:
                last_error = ProviderError(
                    "模型供应商发生未分类异常",
                    transient=False,
                    code="provider_failure",
                )
                self.circuit.record_failure()
                break
        if response is None:
            return self._save_fallback(
                request,
                template.version,
                audit,
                getattr(last_error, "code", "provider_failure"),
                attempts=attempts,
                started_at=started_at,
            )
        review_status = "unavailable"
        review_payload: dict[str, Any] = {
            "status": "unavailable",
            "provider": type(self.reviewer).__name__,
            "policy_version": self.reviewer.policy_version,
        }
        try:
            decision = self.reviewer.review(
                response.text,
                response.structured_candidate,
            )
            review_status = decision.status
            review_payload = {
                "status": decision.status,
                "provider": decision.provider,
                "policy_version": decision.policy_version,
                "reason_code": decision.reason_code,
                "review_id": decision.review_id,
            }
        except Exception:
            review_status = "unavailable"

        now = self.clock()
        actual_cost = self.price.cost(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            review_calls=1,
        )
        self.repository.record_usage(
            operation_id=request.operation_id,
            attempt_id=stable_id("attempt", [request.operation_id, attempts]),
            provider_request_id=response.provider_request_id,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            review_calls=1,
            cost_cny=actual_cost,
            price_version=self.price.version,
            now=now,
            budget_date=request.budget_date,
            event_id=request.event_id,
            character_id=request.character_id,
            interface=request.interface,
        )
        invalid_structured = (
            response.structured_candidate is not None
            and not set(response.structured_candidate) <= STRUCTURED_ALLOWED_KEYS
        )
        token_limit_exceeded = (
            response.input_tokens > estimated_input + 100
            or response.output_tokens > worst_output
        )
        if (
            review_status != "approved"
            or invalid_structured
            or token_limit_exceeded
        ):
            reason = (
                "token_limit_exceeded"
                if token_limit_exceeded
                else (
                    "invalid_structured_output"
                    if invalid_structured
                    else f"review_{review_status}"
                )
            )
            result = self._build_result(
                request,
                audit,
                reviewed=False,
                review=review_payload,
                attempts=attempts,
                provider=response.provider,
                model=response.model,
                degradation_reason=reason,
                started_at=started_at,
                usage={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "review_calls": 1,
                    "cost_cny": f"{actual_cost:.8f}",
                    "price_version": self.price.version,
                },
            )
            if review_status == "blocked":
                result["status"] = "blocked"
            self._persist_result(
                request,
                template.version,
                result,
                status="blocked" if review_status == "blocked" else "fallback",
                now=now,
                started_at=started_at,
            )
            return result

        result = {
            "schema_version": "rpg-llm-result-v1",
            "status": "succeeded",
            "run_mode": "model",
            "text": response.text,
            "structured_candidate": response.structured_candidate,
            "review": review_payload,
            "provider": response.provider,
            "model": response.model,
            "attempts": attempts,
            "cache_hit": False,
            "degradation_reason": None,
            "latency_ms": round(
                (time.perf_counter() - started_at) * 1000,
                3,
            ),
            "prompt_audit": {
                "template_id": audit.template_id,
                "template_version": audit.template_version,
                "prompt_sha256": audit.prompt_sha256,
                "redacted_preview": audit.redacted_preview,
            },
            "usage": {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "review_calls": 1,
                "cost_cny": f"{actual_cost:.8f}",
                "price_version": self.price.version,
            },
        }
        self._persist_result(
            request,
            template.version,
            result,
            status="succeeded",
            now=now,
            started_at=started_at,
        )
        return result

    def _save_fallback(
        self,
        request: LlmRequest,
        template_version: str,
        audit,
        reason: str,
        *,
        attempts: int = 0,
        started_at: float,
    ) -> dict[str, Any]:
        result = self._build_result(
            request,
            audit,
            reviewed=False,
            review={
                "status": "unavailable",
                "provider": type(self.reviewer).__name__,
                "policy_version": self.reviewer.policy_version,
            },
            attempts=attempts,
            provider=None,
            model=None,
            degradation_reason=reason,
            started_at=started_at,
        )
        self._persist_result(
            request,
            template_version,
            result,
            status="fallback",
            now=self.clock(),
            started_at=started_at,
        )
        return result

    def _build_result(
        self,
        request: LlmRequest,
        audit,
        *,
        reviewed: bool,
        review: dict[str, Any],
        attempts: int,
        provider: str | None,
        model: str | None,
        degradation_reason: str,
        started_at: float,
        usage: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if reviewed:
            raise AssertionError("blocked model output must use the rule template")
        text, structured = rule_fallback(request)
        return {
            "schema_version": "rpg-llm-result-v1",
            "status": "fallback",
            "run_mode": "rule",
            "text": text,
            "structured_candidate": structured,
            "review": review,
            "provider": provider,
            "model": model,
            "attempts": attempts,
            "cache_hit": False,
            "degradation_reason": degradation_reason,
            "latency_ms": round(
                (time.perf_counter() - started_at) * 1000,
                3,
            ),
            "prompt_audit": {
                "template_id": audit.template_id,
                "template_version": audit.template_version,
                "prompt_sha256": audit.prompt_sha256,
                "redacted_preview": audit.redacted_preview,
            },
            "usage": usage,
        }

    def _persist_result(
        self,
        request: LlmRequest,
        template_version: str,
        result: dict[str, Any],
        *,
        status: str,
        now: datetime,
        started_at: float,
    ) -> None:
        self.repository.save_operation(
            operation_id=request.operation_id,
            request_hash=request.request_hash,
            template_id=request.template_id,
            template_version=template_version,
            status=status,
            result=result,
            review_status=result["review"]["status"],
            run_mode=result["run_mode"],
            provider=result["provider"],
            model=result["model"],
            attempts=result["attempts"],
            degradation_reason=result["degradation_reason"],
            prompt_sha256=result["prompt_audit"]["prompt_sha256"],
            redacted_prompt_preview=result["prompt_audit"]["redacted_preview"],
            latency_ms=round(
                (time.perf_counter() - started_at) * 1000,
                3,
            ),
            now=now,
        )

    @staticmethod
    def _fallback_without_audit(reason: str) -> dict[str, Any]:
        return {
            "schema_version": "rpg-llm-result-v1",
            "status": "fallback",
            "run_mode": "rule",
            "text": "当前暂不能生成新的表达，继续使用安全规则。",
            "structured_candidate": None,
            "review": {"status": "unavailable"},
            "provider": None,
            "model": None,
            "attempts": 0,
            "cache_hit": False,
            "degradation_reason": reason,
            "prompt_audit": None,
            "usage": None,
        }
