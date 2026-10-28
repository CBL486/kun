"""B4 SQLite 迁移命令。"""

from __future__ import annotations

import argparse
import json

from .migrations import migrate, rollback, schema_version


def main() -> int:
    parser = argparse.ArgumentParser(description="B4 SQLite 迁移与回滚")
    parser.add_argument("command", choices=["migrate", "rollback", "version"])
    parser.add_argument("--database", required=True)
    parser.add_argument("--target-version", type=int, default=0)
    args = parser.parse_args()

    if args.command == "migrate":
        version = migrate(args.database)
    elif args.command == "rollback":
        version = rollback(args.database, args.target_version)
    else:
        version = schema_version(args.database)
    print(json.dumps({"schema_version": version}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
