"""B13 backup, restore and evidence CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backup import (
    backup_database,
    inspect_database,
    restore_database,
    verify_backup,
)
from .evidence import build_release_evidence


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="B13 database and release evidence")
    commands = parser.add_subparsers(dest="command", required=True)

    backup = commands.add_parser("backup")
    backup.add_argument("--url", required=True)
    backup.add_argument("--output", required=True)
    backup.add_argument("--pg-bin")

    verify = commands.add_parser("verify-backup")
    verify.add_argument("--backup", required=True)

    restore = commands.add_parser("restore")
    restore.add_argument("--backup", required=True)
    restore.add_argument("--url", required=True)
    restore.add_argument("--pg-bin")
    restore.add_argument("--confirm-restore", action="store_true")

    inspect = commands.add_parser("inspect")
    inspect.add_argument("--url", required=True)

    evidence = commands.add_parser("evidence")
    evidence.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "backup":
        result = backup_database(
            database_url=args.url,
            output=Path(args.output),
            pg_bin=Path(args.pg_bin) if args.pg_bin else None,
        )
    elif args.command == "verify-backup":
        result = {"issues": verify_backup(Path(args.backup))}
    elif args.command == "restore":
        result = restore_database(
            backup=Path(args.backup),
            database_url=args.url,
            confirm_restore=args.confirm_restore,
            pg_bin=Path(args.pg_bin) if args.pg_bin else None,
        )
    elif args.command == "inspect":
        result = inspect_database(args.url)
    else:
        result = build_release_evidence(ROOT)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(output)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 1 if result.get("issues") else 0


if __name__ == "__main__":
    raise SystemExit(main())
