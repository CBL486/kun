"""B5 SQLAlchemy 迁移命令。"""

from __future__ import annotations

import argparse
import json

from .migrations import create_database_engine, migrate, rollback, schema_version


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在明确指定的 SQLite/PostgreSQL 数据库上执行 B5 迁移"
    )
    parser.add_argument("command", choices=["migrate", "rollback", "version"])
    parser.add_argument("--url", required=True)
    parser.add_argument(
        "--confirm-rollback",
        action="store_true",
        help="回滚会删除 B5 表，必须显式确认",
    )
    args = parser.parse_args()
    if args.command == "rollback" and not args.confirm_rollback:
        parser.error("rollback 必须同时提供 --confirm-rollback")

    engine = create_database_engine(args.url)
    try:
        if args.command == "migrate":
            version = migrate(engine)
        elif args.command == "rollback":
            version = rollback(engine)
        else:
            version = schema_version(engine)
    finally:
        engine.dispose()
    print(json.dumps({"schema_version": version}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
