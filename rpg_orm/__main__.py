"""B5 SQLAlchemy 迁移命令。"""

from __future__ import annotations

import argparse
import json

from .migrations import create_database_engine, migrate, rollback, schema_version
from .product_repository import ProductRepository


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在明确指定的 SQLite/PostgreSQL 数据库上执行 B5/B8 schema 迁移"
    )
    parser.add_argument(
        "command",
        choices=[
            "migrate",
            "rollback",
            "version",
            "import-persona-json",
            "import-setup-json",
        ],
    )
    parser.add_argument("--url", required=True)
    parser.add_argument(
        "--confirm-rollback",
        action="store_true",
        help="回滚会删除 B5 表，必须显式确认",
    )
    parser.add_argument("--path")
    parser.add_argument("--world-id", default="world_qinghe_v1")
    parser.add_argument("--character-id", default="char_lin_cheng")
    args = parser.parse_args()
    if args.command == "rollback" and not args.confirm_rollback:
        parser.error("rollback 必须同时提供 --confirm-rollback")

    engine = create_database_engine(args.url)
    try:
        if args.command == "migrate":
            version = migrate(engine)
        elif args.command == "rollback":
            version = rollback(engine)
        elif args.command == "import-persona-json":
            if not args.path:
                parser.error("import-persona-json 需要 --path")
            ProductRepository(engine).migrate_persona_json(
                args.path,
                world_id=args.world_id,
                character_id=args.character_id,
            )
            version = schema_version(engine)
        elif args.command == "import-setup-json":
            if not args.path:
                parser.error("import-setup-json 需要 --path")
            ProductRepository(engine).migrate_setup_json(
                args.path,
                world_id=args.world_id,
            )
            version = schema_version(engine)
        else:
            version = schema_version(engine)
    finally:
        engine.dispose()
    print(json.dumps({"schema_version": version}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
