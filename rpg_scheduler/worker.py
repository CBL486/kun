"""Long-running scheduler worker for deployment hosts."""

from __future__ import annotations

import time
from typing import Callable

from rpg_orm.repository import OrmRepository
from sqlalchemy import Engine

from .repository import SchedulerRepository
from .service import SchedulerService


def run_worker(
    engine: Engine,
    *,
    worker_id: str,
    poll_interval_seconds: float = 1.0,
    max_cycles: int | None = None,
    handlers=None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, int]:
    scheduler = SchedulerService(SchedulerRepository(engine))
    world = OrmRepository(engine)
    task_handlers = handlers or {
        "memory_reconcile": lambda task: world.reconcile(
            task["payload"].get("event_id")
        ),
    }
    counts = {
        "succeeded": 0,
        "fallback": 0,
        "dead_letter": 0,
        "idle": 0,
    }
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        outcome = scheduler.run_next(
            worker_id=worker_id,
            handlers=task_handlers,
            lease_seconds=30.0,
        )
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
        cycles += 1
        if outcome.status == "idle":
            sleep(max(0.05, poll_interval_seconds))
    return counts
