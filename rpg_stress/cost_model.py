"""Worst-case mock cost models and dimensionally aggregated billing."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Iterable

from rpg_llm.models import BudgetSnapshot
from rpg_llm.pricing import (
    DEFAULT_PRICE_VERSION,
    PRICE_VERSIONS,
    LlmBudgetPolicy,
)
from rpg_sim.ids import digest


@dataclass(frozen=True)
class StressRequest:
    request_id: str
    budget_date: str
    event_id: str | None
    character_id: str
    interface: str
    input_tokens: int
    output_tokens: int
    attempts: int = 1
    review_calls: int = 1


@dataclass(frozen=True)
class CostLine:
    request_id: str
    budget_date: str
    event_id: str | None
    character_id: str
    interface: str
    input_tokens: int
    output_tokens: int
    review_calls: int
    cost_cny: Decimal
    price_version: str
    attempts: int


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    budget_date: str
    accepted_requests: int
    blocked_requests: int
    billable_attempts: int
    total_cost_cny: Decimal
    lines: tuple[CostLine, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "budget_date": self.budget_date,
            "accepted_requests": self.accepted_requests,
            "blocked_requests": self.blocked_requests,
            "billable_attempts": self.billable_attempts,
            "total_cost_cny": f"{self.total_cost_cny:.8f}",
        }


def simulate_cost_scenario(
    name: str,
    requests: Iterable[StressRequest],
    *,
    budget_policy: LlmBudgetPolicy | None = None,
    price_version: str = DEFAULT_PRICE_VERSION,
) -> ScenarioResult:
    policy = budget_policy or LlmBudgetPolicy()
    price = PRICE_VERSIONS[price_version]
    request_list = list(requests)
    budget_date = (
        request_list[0].budget_date if request_list else "unknown"
    )
    current = BudgetSnapshot()
    accepted = 0
    blocked = 0
    attempts = 0
    lines = []
    for request in request_list:
        input_tokens = request.input_tokens * request.attempts
        output_tokens = request.output_tokens * request.attempts
        cost = price.cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            review_calls=request.review_calls,
        )
        reason = policy.exceeded_reason(
            current,
            prospective_input_tokens=input_tokens,
            prospective_output_tokens=output_tokens,
            prospective_cost=cost,
            review_call=bool(request.review_calls),
        )
        if reason:
            blocked += 1
            continue
        accepted += 1
        attempts += request.attempts
        current = BudgetSnapshot(
            calls=current.calls + request.attempts,
            review_calls=current.review_calls + request.review_calls,
            input_tokens=current.input_tokens + input_tokens,
            output_tokens=current.output_tokens + output_tokens,
            cost_cny=Decimal(current.cost_cny) + cost,
        )
        lines.append(
            CostLine(
                request_id=request.request_id,
                budget_date=request.budget_date,
                event_id=request.event_id,
                character_id=request.character_id,
                interface=request.interface,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                review_calls=request.review_calls,
                cost_cny=cost,
                price_version=price.version,
                attempts=request.attempts,
            )
        )
    return ScenarioResult(
        name=name,
        budget_date=budget_date,
        accepted_requests=accepted,
        blocked_requests=blocked,
        billable_attempts=attempts,
        total_cost_cny=Decimal(str(current.cost_cny)),
        lines=tuple(lines),
    )


def _cost_totals(lines: Iterable[CostLine]) -> dict[str, Any]:
    calls = 0
    input_tokens = 0
    output_tokens = 0
    review_calls = 0
    cost = Decimal("0")
    for line in lines:
        calls += line.attempts
        input_tokens += line.input_tokens
        output_tokens += line.output_tokens
        review_calls += line.review_calls
        cost += line.cost_cny
    return {
        "calls": calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "review_calls": review_calls,
        "cost_cny": cost,
    }


def _serialize_totals(totals: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in totals.items() if key != "cost_cny"},
        "cost_cny": f"{totals['cost_cny']:.8f}",
    }


def build_cost_report(
    lines: Iterable[CostLine],
    *,
    budget_date: str | None = None,
) -> dict[str, Any]:
    selected = [
        line
        for line in lines
        if budget_date is None or line.budget_date == budget_date
    ]
    groups = {
        "by_date": defaultdict(list),
        "by_event": defaultdict(list),
        "by_character": defaultdict(list),
        "by_interface": defaultdict(list),
    }
    for line in selected:
        groups["by_date"][line.budget_date].append(line)
        groups["by_event"][line.event_id or "unattributed"].append(line)
        groups["by_character"][line.character_id].append(line)
        groups["by_interface"][line.interface].append(line)
    totals = _cost_totals(selected)
    return {
        "schema_version": "rpg-cost-report-v1",
        "total": _serialize_totals(totals),
        "by_date": {
            key: _serialize_totals(_cost_totals(value))
            for key, value in sorted(groups["by_date"].items())
        },
        "by_event": {
            key: _serialize_totals(_cost_totals(value))
            for key, value in sorted(groups["by_event"].items())
        },
        "by_character": {
            key: _serialize_totals(_cost_totals(value))
            for key, value in sorted(groups["by_character"].items())
        },
        "by_interface": {
            key: _serialize_totals(_cost_totals(value))
            for key, value in sorted(groups["by_interface"].items())
        },
        "price_versions": sorted(
            {line.price_version for line in selected}
        ),
    }


def build_mock_bill(lines: Iterable[CostLine]) -> dict[str, Any]:
    bill_lines = list(lines)
    totals = _cost_totals(bill_lines)
    return {
        "schema_version": "rpg-mock-bill-v1",
        "line_count": len(bill_lines),
        "total": _serialize_totals(totals),
        "digest": digest(
            [
                (
                    line.request_id,
                    line.input_tokens,
                    line.output_tokens,
                    line.review_calls,
                    f"{line.cost_cny:.8f}",
                )
                for line in bill_lines
            ]
        ),
    }


def run_cost_matrix(
    *,
    budget_date: str,
    budget_policy: LlmBudgetPolicy | None = None,
    price_version: str = DEFAULT_PRICE_VERSION,
) -> dict[str, Any]:
    policy = budget_policy or LlmBudgetPolicy()
    base_date = date.fromisoformat(budget_date)
    scenario_dates = {
        name: (base_date + timedelta(days=index)).isoformat()
        for index, name in enumerate(
            (
                "normal_day",
                "abnormal_day",
                "long_conversation",
                "consecutive_retries",
                "concurrency",
            )
        )
    }

    def request(
        scenario: str,
        index: int,
        *,
        request_date: str,
        input_tokens: int,
        output_tokens: int,
        attempts: int = 1,
        character_id: str = "char_lin_cheng",
        interface: str = "agent_loop",
    ) -> StressRequest:
        return StressRequest(
            request_id=f"{scenario}_{index:03}",
            budget_date=request_date,
            event_id=f"evt_{scenario}_{index:03}",
            character_id=character_id,
            interface=interface,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            attempts=attempts,
        )

    scenarios = {
        "normal_day": [
            request(
                "normal",
                index,
                request_date=scenario_dates["normal_day"],
                input_tokens=1_200,
                output_tokens=300,
            )
            for index in range(1, 6)
        ],
        "abnormal_day": [
            request(
                "abnormal",
                index,
                request_date=scenario_dates["abnormal_day"],
                input_tokens=4_000,
                output_tokens=1_200,
            )
            for index in range(1, 11)
        ],
        "long_conversation": [
            request(
                "long",
                index,
                request_date=scenario_dates["long_conversation"],
                input_tokens=3_500,
                output_tokens=600,
                interface="observer_chat",
            )
            for index in range(1, 21)
        ],
        "consecutive_retries": [
            request(
                "retry",
                index,
                request_date=scenario_dates["consecutive_retries"],
                input_tokens=1_500,
                output_tokens=300,
                attempts=2,
            )
            for index in range(1, 7)
        ],
        "concurrency": [
            request(
                "concurrent",
                index,
                request_date=scenario_dates["concurrency"],
                input_tokens=1_000,
                output_tokens=250,
                interface="burst_api",
            )
            for index in range(1, 21)
        ],
    }
    results = [
        simulate_cost_scenario(
            name,
            requests,
            budget_policy=policy,
            price_version=price_version,
        )
        for name, requests in scenarios.items()
    ]
    all_lines = [line for result in results for line in result.lines]
    report = build_cost_report(all_lines)
    bill = build_mock_bill(all_lines)
    report["scenarios"] = [result.to_dict() for result in results]
    report["mock_bill"] = bill
    report["bill_matches"] = (
        report["total"]["cost_cny"] == bill["total"]["cost_cny"]
    )
    return report
