"""B1 每日硬预算。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal


class BudgetExceeded(RuntimeError):
    def __init__(self, metric: str, message: str):
        super().__init__(message)
        self.code = "budget_exceeded"
        self.metric = metric


@dataclass(frozen=True)
class BudgetPolicy:
    world_events: int = 6
    shares: int = 1
    journals: int = 1
    model_calls: int = 8
    review_calls: int = 12
    input_tokens: int = 24_000
    output_tokens: int = 6_000
    cost_cny: Decimal = Decimal("0.10")


@dataclass
class DailyBudget:
    world_date: str
    world_events: int = 0
    shares: int = 0
    journals: int = 0
    model_calls: int = 0
    review_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cny: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        self.cost_cny = Decimal(self.cost_cny)

    def can_commit_event(self, action_type: str) -> tuple[bool, str | None]:
        if action_type == "write_journal":
            if self.journals >= 1:
                return False, "journals"
            return True, None
        if self.world_events >= 6:
            return False, "world_events"
        return True, None

    def record_event(
        self,
        action_type: str,
        *,
        visible: bool,
        input_tokens: int = 520,
        output_tokens: int = 110,
    ) -> None:
        if action_type == "write_journal":
            self.journals += 1
        else:
            self.world_events += 1
        self.model_calls += 1
        # 私密日记也要经过内容审核，只是不进入公开投影。
        self.review_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        # 固定 mock 价格：输入 4 元/百万 token，输出 16 元/百万 token。
        self.cost_cny += (
            Decimal(input_tokens) * Decimal("0.000004")
            + Decimal(output_tokens) * Decimal("0.000016")
        )
        self._assert_limits()

    def discard_failed_attempt(
        self,
        *,
        input_tokens: int = 120,
        output_tokens: int = 20,
    ) -> None:
        self.model_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost_cny += (
            Decimal(input_tokens) * Decimal("0.000004")
            + Decimal(output_tokens) * Decimal("0.000016")
        )
        self._assert_limits()

    def record_share(
        self,
        *,
        input_tokens: int = 760,
        output_tokens: int = 240,
    ) -> None:
        if self.shares >= 1:
            raise BudgetExceeded("shares", "每日分享预算已耗尽")
        self.shares += 1
        self.model_calls += 1
        self.review_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost_cny += (
            Decimal(input_tokens) * Decimal("0.000004")
            + Decimal(output_tokens) * Decimal("0.000016")
        )
        self._assert_limits()

    def _assert_limits(self) -> None:
        checks = (
            ("world_events", self.world_events, 6),
            ("shares", self.shares, 1),
            ("journals", self.journals, 1),
            ("model_calls", self.model_calls, 8),
            ("review_calls", self.review_calls, 12),
            ("input_tokens", self.input_tokens, 24_000),
            ("output_tokens", self.output_tokens, 6_000),
        )
        for metric, value, limit in checks:
            if value > limit:
                raise BudgetExceeded(metric, f"每日 {metric} 超限：{value}/{limit}")
        if self.cost_cny > Decimal("0.10"):
            raise BudgetExceeded(
                "cost_cny",
                f"每日 mock 成本超限：{self.cost_cny:.6f}/0.100000 元",
            )

    def to_dict(self) -> dict:
        result = asdict(self)
        result["limits"] = {
            "world_events": 6,
            "shares": 1,
            "journals": 1,
            "model_calls": 8,
            "review_calls": 12,
            "input_tokens": 24_000,
            "output_tokens": 6_000,
            "cost_cny": "0.10",
        }
        result["provider"] = "mock"
        result["price_version"] = "mock-price-b1-2026-10-28"
        result["cost_cny"] = f"{self.cost_cny:.6f}"
        return result
