"""Run an isolated R7 API with a visible active study session."""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn

from app.main import create_app
from app.persona import DatabasePersonaStore
from app.school import SCHOOL_START, SchoolAutonomyService, WORLD_TIMEZONE
from app.setup import DeepSeekSetupStore
from app.world_clock import WorldClockStore
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-r7-evidence-ABCD":
            raise AssertionError("unexpected evidence key")


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r7-evidence-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'product.db').as_posix()}"
    )
    repository = ProductRepository(engine)
    persona = DatabasePersonaStore(repository)
    persona.use_default()
    today = datetime.now(WORLD_TIMEZONE).replace(
        hour=SCHOOL_START.hour,
        minute=1,
        second=0,
        microsecond=0,
    )
    school = SchoolAutonomyService(repository)
    school.tick(today)
    school.tick(today + timedelta(minutes=6))
    clock = WorldClockStore(root / "world")
    clock.advance_if_due(
        now=today + timedelta(minutes=7),
        base_revision=50,
    )
    setup = DeepSeekSetupStore(root / "setup", secure_acl=False)
    setup.save_key("sk-test-r7-evidence-ABCD", FakeValidator())
    setup.complete(persona_configured=True)
    application = create_app(
        setup_store=setup,
        setup_validator=FakeValidator(),
        persona_store=persona,
        setup_gate=True,
    )
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=8096,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
