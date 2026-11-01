from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from rpg_llm.gateway import LlmGateway
from rpg_llm.models import LlmRequest
from rpg_llm.providers import MockProvider
from rpg_llm.repository import LlmRepository
from rpg_llm.review import MockReviewAdapter
from rpg_orm.migrations import create_database_engine
from rpg_scheduler import ScheduleSpec, SchedulerRepository
from rpg_stress import (
    ConfirmationRequired,
    ManualConfirmationGate,
    SlidingWindowRateLimiter,
    build_cost_report,
    run_cost_matrix,
)


NOW = datetime(2026, 11, 1, 4, 0, tzinfo=timezone.utc)


def make_engine(path: Path):
    return create_database_engine(f"sqlite:///{path.as_posix()}")


def test_worst_case_cost_matrix_stays_under_each_daily_cap() -> None:
    report = run_cost_matrix(budget_date="2026-11-01")
    assert report["bill_matches"] is True
    assert report["mock_bill"]["total"]["cost_cny"] == report["total"]["cost_cny"]
    assert {
        "normal_day",
        "abnormal_day",
        "long_conversation",
        "consecutive_retries",
        "concurrency",
    } == {item["name"] for item in report["scenarios"]}
    for scenario in report["scenarios"]:
        assert Decimal(scenario["total_cost_cny"]) <= Decimal("0.10")
    assert len(report["by_date"]) == 5
    assert all(
        Decimal(item["cost_cny"]) <= Decimal("0.10")
        for item in report["by_date"].values()
    )
    by_name = {item["name"]: item for item in report["scenarios"]}
    assert by_name["normal_day"]["blocked_requests"] == 0
    assert by_name["abnormal_day"]["blocked_requests"] > 0
    assert by_name["long_conversation"]["blocked_requests"] > 0
    assert by_name["consecutive_retries"]["blocked_requests"] > 0
    assert by_name["concurrency"]["blocked_requests"] > 0


def test_real_gateway_cost_report_matches_usage_bill(tmp_path) -> None:
    engine = make_engine(tmp_path / "costs.db")
    repository = LlmRepository(engine)
    gateway = LlmGateway(
        repository,
        provider=MockProvider(),
        reviewer=MockReviewAdapter(),
        clock=lambda: NOW,
    )
    try:
        for index, (event_id, character_id, interface) in enumerate(
            (
                ("evt_1", "char_lin_cheng", "agent_loop"),
                ("evt_2", "npc_chen", "npc_reaction"),
                ("evt_3", "char_lin_cheng", "observer_chat"),
            ),
            start=1,
        ):
            gateway.generate(
                LlmRequest(
                    operation_id=f"op_b11_cost_{index}",
                    template_id="observer_message_ack",
                    variables={"message_id": f"msg_{index}"},
                    budget_date="2026-11-01",
                    event_id=event_id,
                    character_id=character_id,
                    interface=interface,
                )
            )
        report = repository.cost_report("2026-11-01")
        usage = repository.list_usage()
        expected = sum(Decimal(item["cost_cny"]) for item in usage)
        assert report["total"]["calls"] == 3
        assert Decimal(report["total"]["cost_cny"]) == expected
        assert set(report["by_event"]) == {"evt_1", "evt_2", "evt_3"}
        assert set(report["by_character"]) == {
            "char_lin_cheng",
            "npc_chen",
        }
        assert set(report["by_interface"]) == {
            "agent_loop",
            "npc_reaction",
            "observer_chat",
        }
        assert report["price_versions"] == [gateway.price.version]
    finally:
        engine.dispose()


def test_rate_limiter_is_thread_safe_and_refills_by_window() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(
        limit=5,
        window_seconds=10,
        clock=lambda: now[0],
    )
    with ThreadPoolExecutor(max_workers=10) as executor:
        decisions = list(
            executor.map(
                lambda _: limiter.acquire("observer"),
                range(20),
            )
        )
    assert sum(item.allowed for item in decisions) == 5
    blocked = next(item for item in decisions if not item.allowed)
    assert blocked.retry_after_seconds == 10

    now[0] = 10.1
    assert limiter.acquire("observer").allowed is True


def test_manual_confirmation_blocks_until_approved() -> None:
    gate = ManualConfirmationGate()
    gate.request(
        operation_id="op_sensitive",
        reason_code="publish_private_summary",
    )
    executions = []
    with pytest.raises(ConfirmationRequired) as caught:
        gate.execute(
            operation_id="op_sensitive",
            action=lambda: executions.append("executed"),
        )
    assert caught.value.status == "pending"
    assert executions == []

    decision = gate.decide(
        operation_id="op_sensitive",
        approved=True,
        reviewer="operator_001",
    )
    assert decision.status == "approved"
    assert gate.execute(
        operation_id="op_sensitive",
        action=lambda: "released",
    ) == "released"

    gate.request(
        operation_id="op_rejected",
        reason_code="publish_private_summary",
    )
    gate.decide(
        operation_id="op_rejected",
        approved=False,
        reviewer="operator_001",
    )
    with pytest.raises(ConfirmationRequired):
        gate.execute(
            operation_id="op_rejected",
            action=lambda: executions.append("must_not_run"),
        )
    assert "must_not_run" not in executions


def test_scheduler_backlog_does_not_duplicate_claims(tmp_path) -> None:
    engine = make_engine(tmp_path / "backlog.db")
    repository = SchedulerRepository(engine)
    try:
        for index in range(50):
            repository.enqueue(
                ScheduleSpec(
                    kind="stress_probe",
                    operation_id=f"op_b11_backlog_{index:03}",
                    payload={},
                    available_at=NOW,
                )
            )
        backlog = repository.backlog(now=NOW)
        assert backlog["pending_due"] == 50
        claimed = [
            repository.claim_next(
                worker_id="stress-worker",
                now=NOW,
                lease_seconds=30,
            )
            for _ in range(10)
        ]
        assert all(item is not None for item in claimed)
        assert len({item["task_id"] for item in claimed}) == 10
        backlog = repository.backlog(now=NOW)
        assert backlog["leased"] == 10
        assert backlog["pending_due"] == 40
        assert repository.recover_expired(
            now=NOW + timedelta(seconds=31)
        )["released"] == 10
    finally:
        engine.dispose()


def test_cost_report_rejects_negative_budget_values() -> None:
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(limit=0, window_seconds=1)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(limit=1, window_seconds=0)
    assert build_cost_report([])["total"]["cost_cny"] == "0.00000000"
