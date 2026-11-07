"""Run an isolated R6 API with schema-5 Persona and one evolved event."""

from __future__ import annotations

import tempfile
from pathlib import Path

import uvicorn

from app.main import create_app
from app.persona import DatabasePersonaStore
from app.self_awareness import SelfAwarenessService
from app.setup import DeepSeekSetupStore
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-r6-evidence-ABCD":
            raise AssertionError("unexpected evidence key")


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r6-evidence-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'product.db').as_posix()}"
    )
    repository = ProductRepository(engine)
    persona = DatabasePersonaStore(repository)
    persona.use_default()
    repository.record_memory_event(
        {
            "event_id": "evt_r6_evidence_001",
            "world_id": "world_qinghe_v1",
            "actor_id": "char_lin_cheng",
            "participants": ["char_lin_cheng", "observer_demo_001"],
            "location_id": "loc_library",
            "event_type": "conversation_completed",
            "occurred_at": "2026-11-07T18:00:00+08:00",
            "summary": "玩家认真听林澄讲完一段关于旧书与潮汐的回忆。",
            "valence": 0.6,
            "intensity": 0.8,
            "importance": 0.75,
            "confidence": 0.98,
            "visibility": "private",
            "source": "player",
            "dedupe_key": "r6:evidence:001",
            "metadata": {},
        }
    )
    SelfAwarenessService(repository).evolve_from_event(
        "evt_r6_evidence_001"
    )
    setup = DeepSeekSetupStore(root / "setup", secure_acl=False)
    setup.save_key("sk-test-r6-evidence-ABCD", FakeValidator())
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
        port=8095,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
