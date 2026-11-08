"""Reproduce schema-5 migration, Persona JSON import, and rollback evidence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sqlalchemy import inspect

from app.persona import PersonaStore
from rpg_orm.migrations import (
    create_database_engine,
    migrate,
    rollback,
    schema_version,
)
from rpg_orm.product_repository import ProductRepository


WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r9-schema-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'schema5.db').as_posix()}"
    )
    try:
        migrated_version = migrate(engine)
        source = PersonaStore(root / "persona")
        source.use_default()
        source.save_custom(
            {
                "name": "潮汐",
                "pronouns": "她",
                "age": 21,
                "appearance": "深海蓝长发与透明鳍饰",
                "identity": "青禾镇夜间图书馆管理员",
                "speech_style": "简洁安静",
                "traits": ["克制", "敏锐"],
                "values": ["诚实", "保护秘密"],
                "interests": ["潮汐记录", "旧地图"],
                "initial_goals": ["整理旧地图"],
                "boundaries": ["不泄露私密记忆"],
                "relationship_to_player": "谨慎的观察者朋友",
            }
        )
        repository = ProductRepository(engine)
        imported = repository.migrate_persona_json(
            source.bundle_path,
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
        )
        bundle = repository.get_persona_bundle(
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
        )
        tables_before_rollback = sorted(inspect(engine).get_table_names())
        rolled_back_version = rollback(engine)
        tables_after_rollback = sorted(inspect(engine).get_table_names())
        payload = {
            "schema_version": "aiworld-r9-schema-evidence-v1",
            "migrated_version": migrated_version,
            "persona_json_import": {
                "revision": imported["revision"],
                "baseline_name": bundle["baseline"]["name"],
                "change_log_rows": len(bundle["state"]["change_log"]),
            },
            "rollback": {
                "schema_version": rolled_back_version,
                "table_count_before": len(tables_before_rollback),
                "table_count_after": len(tables_after_rollback),
                "tables_after": tables_after_rollback,
            },
        }
        output = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "r9-schema-evidence-2026-11-08.json"
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
