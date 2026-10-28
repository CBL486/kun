from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from embedded_postgres._commands import POSTGRES_BIN_PATH


HOST = "127.0.0.1"
PORT = "55432"
APP_USER = "aiworld"
APP_DB = "aiworld"
SECRET_DIR = Path(r"C:\AIWorld\data\secrets")
BACKUP_DIR = Path(r"C:\AIWorld\backups")
RETENTION_DAYS = 14


def run(args: list[str], password: str) -> None:
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"backup command failed: {args[0]}\n{result.stderr}")


def prune(prefix: str) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    for path in BACKUP_DIR.glob(prefix):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < cutoff:
            path.unlink(missing_ok=True)


def main() -> None:
    app_password = (SECRET_DIR / "aiworld_database_password.txt").read_text(encoding="utf-8").strip()
    admin_password = (SECRET_DIR / "postgres_admin_password.txt").read_text(encoding="utf-8").strip()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dump_path = BACKUP_DIR / f"postgres-{APP_DB}-{stamp}.dump"
    globals_path = BACKUP_DIR / f"postgres-globals-{stamp}.sql"

    run(
        [
            str(POSTGRES_BIN_PATH / "pg_dump.exe"),
            "-h", HOST, "-p", PORT, "-U", APP_USER, "-d", APP_DB,
            "-Fc", "-f", str(dump_path),
        ],
        app_password,
    )
    run(
        [
            str(POSTGRES_BIN_PATH / "pg_dumpall.exe"),
            "-h", HOST, "-p", PORT, "-U", "postgres",
            "--globals-only", "-f", str(globals_path),
        ],
        admin_password,
    )
    if dump_path.stat().st_size < 100 or globals_path.stat().st_size < 100:
        raise RuntimeError("backup artifacts are unexpectedly small")

    prune(f"postgres-{APP_DB}-*.dump")
    prune("postgres-globals-*.sql")
    print(f"BACKUP_OK dump={dump_path} bytes={dump_path.stat().st_size}")
    print(f"GLOBALS_OK path={globals_path} bytes={globals_path.stat().st_size}")


if __name__ == "__main__":
    main()
