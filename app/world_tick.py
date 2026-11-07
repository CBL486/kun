"""Unified background tick: advance clock and daily school state."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.school import SchoolAutonomyService
from app.school import GatewayStudyProvider
from app.settings import settings
from app.world_clock import WorldClockStore
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository
from rpg_llm.runtime import build_gateway


def run_tick(now: datetime | None = None) -> dict[str, Any]:
    clock_store = WorldClockStore.from_settings(settings)
    clock = clock_store.advance_if_due(now=now)
    product_url = (
        settings.product_database_url
        or settings.scheduler_database_url
        or "sqlite:///./data/local.sqlite3"
    )
    engine = create_database_engine(product_url)
    try:
        repository = ProductRepository(engine)
        gateway, _config = build_gateway(engine)
        school = SchoolAutonomyService(
            repository,
            provider=GatewayStudyProvider(gateway),
        ).tick(
            now=datetime.fromisoformat(
                clock["logical_time"].replace("Z", "+00:00")
            )
        )
    finally:
        engine.dispose()
    return {"clock": clock, "school": school}


if __name__ == "__main__":
    print(json.dumps(run_tick(), ensure_ascii=False, indent=2))
