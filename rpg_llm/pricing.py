"""Price versions and hard-budget checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import BudgetSnapshot


@dataclass(frozen=True)
class PriceVersion:
    version: str
    input_cny_per_million: Decimal
    output_cny_per_million: Decimal
    review_cny_per_call: Decimal = Decimal("0")

    def cost(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        review_calls: int,
    ) -> Decimal:
        return (
            Decimal(input_tokens) * self.input_cny_per_million / Decimal(1_000_000)
            + Decimal(output_tokens)
            * self.output_cny_per_million
            / Decimal(1_000_000)
            + Decimal(review_calls) * self.review_cny_per_call
        )


@dataclass(frozen=True)
class LlmBudgetPolicy:
    max_calls: int = 8
    max_review_calls: int = 12
    max_input_tokens: int = 24_000
    max_output_tokens: int = 6_000
    max_input_tokens_per_call: int = 4_000
    max_output_tokens_per_call: int = 1_200
    max_cost_cny: Decimal = Decimal("0.10")

    def exceeded_reason(
        self,
        current: BudgetSnapshot,
        *,
        prospective_input_tokens: int,
        prospective_output_tokens: int,
        prospective_cost: Decimal,
        review_call: bool,
    ) -> str | None:
        checks = (
            ("model_calls", current.calls + 1, self.max_calls),
            (
                "review_calls",
                current.review_calls + int(review_call),
                self.max_review_calls,
            ),
            (
                "input_tokens",
                current.input_tokens + prospective_input_tokens,
                self.max_input_tokens,
            ),
            (
                "output_tokens",
                current.output_tokens + prospective_output_tokens,
                self.max_output_tokens,
            ),
        )
        for name, value, limit in checks:
            if value > limit:
                return name
        if Decimal(current.cost_cny) + prospective_cost > self.max_cost_cny:
            return "cost_cny"
        return None


PRICE_VERSIONS = {
    "mock-price-b9-2026-11-01": PriceVersion(
        version="mock-price-b9-2026-11-01",
        input_cny_per_million=Decimal("4"),
        output_cny_per_million=Decimal("16"),
    )
}
DEFAULT_PRICE_VERSION = "mock-price-b9-2026-11-01"
