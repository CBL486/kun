"""Run an isolated API for R4 browser evidence; never calls DeepSeek."""

from __future__ import annotations

import tempfile
from pathlib import Path

import uvicorn

from app.main import create_app
from app.persona import PersonaStore
from app.setup import DeepSeekSetupStore


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-r4-evidence-ABCD":
            raise AssertionError("unexpected evidence key")


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r4-evidence-"))
    setup = DeepSeekSetupStore(root / "setup", secure_acl=False)
    setup.save_key("sk-test-r4-evidence-ABCD", FakeValidator())
    application = create_app(
        setup_store=setup,
        setup_validator=FakeValidator(),
        persona_store=PersonaStore(root / "persona"),
        setup_gate=True,
    )
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=8093,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
