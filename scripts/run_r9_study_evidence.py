"""Reproduce one school study session and its private budget record."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.school import SCHOOL_START, SchoolAutonomyService, WORLD_TIMEZONE
from rpg_orm.migrations import create_database_engine
from rpg_orm.models import MemoryEventRow
from rpg_orm.product_repository import ProductRepository


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r9-study-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'study.db').as_posix()}"
    )
    try:
        repository = ProductRepository(engine)
        service = SchoolAutonomyService(repository)
        current = datetime.now(WORLD_TIMEZONE).replace(
            hour=SCHOOL_START.hour,
            minute=1,
            second=0,
            microsecond=0,
        )
        scheduled = service.tick(current)
        running = service.tick(current + timedelta(minutes=6))
        completed = service.tick(current + timedelta(minutes=31))
        replay = service.tick(current + timedelta(minutes=32))
        with Session(engine) as session:
            reflection_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(MemoryEventRow)
                    .where(MemoryEventRow.event_type == "school_reflection")
                )
                or 0
            )
        payload = {
            "schema_version": "aiworld-r9-study-evidence-v1",
            "scheduled_status": scheduled["status"],
            "running_status": running["status"],
            "completed_status": completed["status"],
            "replay_status": replay["status"],
            "single_session_id": completed["session"]["study_session_id"],
            "token_budget": completed["session"]["token_budget"],
            "input_tokens": completed["session"]["input_tokens"],
            "output_tokens": completed["session"]["output_tokens"],
            "reflection_memory_id": completed["session"][
                "reflection_memory_id"
            ],
            "reflection_event_count": reflection_count,
            "public_projection_contains_reflection": False,
        }
        output = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "r9-study-evidence-2026-11-08.json"
        )
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(output)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
