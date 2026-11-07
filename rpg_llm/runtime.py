"""Environment-driven real-provider runtime for the LLM gateway."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import Engine

from .gateway import LlmGateway
from .models import LlmRequest
from .pricing import LlmBudgetPolicy
from .providers import MockProvider, OpenAICompatibleProvider
from .repository import LlmRepository
from .review import MockReviewAdapter


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-flash"
DEEPSEEK_PRICE_VERSION = "deepseek-flash-peak-cny-2026-11-02"
MOCK_PRICE_VERSION = "mock-price-b9-2026-11-01"


@dataclass(frozen=True)
class LlmRuntimeConfig:
    provider: str = "mock"
    base_url: str = DEEPSEEK_BASE_URL
    model: str = DEEPSEEK_MODEL
    price_version: str = MOCK_PRICE_VERSION
    timeout_seconds: float = 45.0
    max_attempts: int = 2
    max_cost_cny: Decimal = Decimal("0.10")
    review_provider: str = "local"
    api_key: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "LlmRuntimeConfig":
        provider = os.environ.get("AIWORLD_LLM_PROVIDER", "mock").strip().lower()
        if provider not in {"mock", "deepseek"}:
            raise ValueError(f"unsupported AIWORLD_LLM_PROVIDER: {provider}")
        review_provider = os.environ.get(
            "AIWORLD_LLM_REVIEW_PROVIDER", "local"
        ).strip().lower()
        if review_provider != "local":
            raise ValueError(
                "only AIWORLD_LLM_REVIEW_PROVIDER=local is currently supported"
            )
        default_price = (
            DEEPSEEK_PRICE_VERSION
            if provider == "deepseek"
            else MOCK_PRICE_VERSION
        )
        try:
            max_cost = Decimal(
                os.environ.get("AIWORLD_LLM_MAX_COST_CNY", "0.10")
            )
        except InvalidOperation as error:
            raise ValueError("invalid AIWORLD_LLM_MAX_COST_CNY") from error
        api_key = os.environ.get("AIWORLD_LLM_API_KEY") or None
        key_file = os.environ.get("AIWORLD_LLM_API_KEY_FILE")
        if not api_key and key_file:
            try:
                from pathlib import Path

                api_key = Path(key_file).read_text(encoding="utf-8").strip() or None
            except OSError:
                api_key = None
        return cls(
            provider=provider,
            base_url=os.environ.get(
                "AIWORLD_LLM_BASE_URL", DEEPSEEK_BASE_URL
            ).rstrip("/"),
            model=os.environ.get("AIWORLD_LLM_MODEL", DEEPSEEK_MODEL),
            price_version=os.environ.get(
                "AIWORLD_LLM_PRICE_VERSION", default_price
            ),
            timeout_seconds=float(
                os.environ.get("AIWORLD_LLM_TIMEOUT_SECONDS", "45")
            ),
            max_attempts=int(
                os.environ.get("AIWORLD_LLM_MAX_ATTEMPTS", "2")
            ),
            max_cost_cny=max_cost,
            review_provider=review_provider,
            api_key=api_key,
        )

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "price_version": self.price_version,
            "review_provider": self.review_provider,
            "api_key_configured": bool(self.api_key),
        }


def build_gateway(
    engine: Engine,
    config: LlmRuntimeConfig | None = None,
) -> tuple[LlmGateway, LlmRuntimeConfig]:
    config = config or LlmRuntimeConfig.from_env()
    repository = LlmRepository(engine)
    if config.provider == "mock":
        provider = MockProvider()
    else:
        provider = OpenAICompatibleProvider(
            base_url=config.base_url,
            model=config.model,
            api_key=config.api_key,
            timeout_seconds=config.timeout_seconds,
            provider_name="deepseek",
            json_mode=True,
            extra_body={"thinking": {"type": "disabled"}},
        )
    gateway = LlmGateway(
        repository,
        provider=provider,
        reviewer=MockReviewAdapter(),
        price_version=config.price_version,
        budget_policy=LlmBudgetPolicy(max_cost_cny=config.max_cost_cny),
        max_attempts=config.max_attempts,
    )
    return gateway, config


def daily_share_request(
    *,
    operation_id: str,
    world_date: str,
    summaries: list[str],
    budget_date: str,
    max_output_tokens: int = 600,
) -> LlmRequest:
    if not summaries:
        raise ValueError("summaries cannot be empty")
    return LlmRequest(
        operation_id=operation_id,
        template_id="daily_share",
        variables={"world_date": world_date, "summaries": summaries},
        budget_date=budget_date,
        max_output_tokens=max_output_tokens,
        interface="deployment_smoke",
    )
