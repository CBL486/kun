"""Run governed chat generation without printing prompts or credentials."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.persona import DatabasePersonaStore
from app.self_awareness import SelfAwarenessService
from rpg_llm.runtime import build_gateway
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="aiworld-r9-chat-smoke-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'chat.db').as_posix()}"
    )
    try:
        repository = ProductRepository(engine)
        persona = DatabasePersonaStore(repository)
        persona.use_default()
        gateway, config = build_gateway(engine)
        service = SelfAwarenessService(repository, gateway=gateway)
        operation_id = "r9-chat-smoke-" + datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S")
        reply = service.reply_in_world(
            "你还记得旧书区那段关于潮汐的谈话吗？",
            operation_id=operation_id,
            budget_date=datetime.now(timezone.utc).date().isoformat(),
        )
        operation = gateway.repository.get_operation(operation_id)
        payload = {
            "schema_version": "aiworld-r9-chat-smoke-v1",
            "provider": config.provider,
            "model": config.model,
            "api_key_configured": bool(config.api_key),
            "reply_kind": reply["kind"],
            "reply": reply["reply"],
            "operation": {
                "status": operation["status"] if operation else None,
                "run_mode": operation["run_mode"] if operation else None,
                "degradation_reason": (
                    operation["degradation_reason"] if operation else None
                ),
            },
        }
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(args.output)
        else:
            print(rendered, end="")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
