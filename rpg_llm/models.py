"""Provider-neutral gateway request and response models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rpg_sim.ids import digest


@dataclass(frozen=True)
class LlmRequest:
    operation_id: str
    template_id: str
    variables: dict[str, Any]
    budget_date: str
    max_output_tokens: int = 1_200

    def __post_init__(self) -> None:
        if not self.operation_id.strip():
            raise ValueError("operation_id 不能为空")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens 必须大于 0")

    @property
    def request_hash(self) -> str:
        return digest(
            {
                "operation_id": self.operation_id,
                "template_id": self.template_id,
                "variables": self.variables,
                "budget_date": self.budget_date,
                "max_output_tokens": self.max_output_tokens,
            }
        )


@dataclass(frozen=True)
class ProviderRequest:
    operation_id: str
    request_id: str
    template_id: str
    template_version: str
    prompt: str
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderResponse:
    text: str | dict[str, Any]
    structured_candidate: dict[str, Any] | None
    input_tokens: int
    output_tokens: int
    provider: str
    model: str
    provider_request_id: str


@dataclass(frozen=True)
class ReviewDecision:
    status: str
    provider: str
    policy_version: str
    reason_code: str | None = None
    review_id: str | None = None


@dataclass(frozen=True)
class PromptAudit:
    template_id: str
    template_version: str
    prompt_sha256: str
    redacted_preview: str


@dataclass(frozen=True)
class BudgetSnapshot:
    calls: int = 0
    review_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cny: object = 0


@dataclass(frozen=True)
class CircuitState:
    open: bool = False
    consecutive_failures: int = 0
    opened_at: float | None = None


@dataclass
class GatewayTrace:
    operation_id: str
    prompt_audit: PromptAudit
    attempts: int = 0
    provider_request_ids: list[str] = field(default_factory=list)
    degradation_reason: str | None = None
