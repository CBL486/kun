"""Run an isolated configured API for R2 browser evidence."""

from __future__ import annotations

import tempfile
from pathlib import Path

import uvicorn

from app.main import create_app
from app.persona import PersonaStore
from app.setup import DeepSeekSetupStore


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-r2-evidence-ABCD":
            raise AssertionError("unexpected evidence key")


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r2-evidence-"))
    setup = DeepSeekSetupStore(root / "setup", secure_acl=False)
    setup.save_key("sk-test-r2-evidence-ABCD", FakeValidator())
    persona = PersonaStore(root / "persona")
    persona.use_default()
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
        port=8094,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
