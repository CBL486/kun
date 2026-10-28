from __future__ import annotations

import os
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from embedded_postgres._commands import POSTGRES_BIN_PATH, pg_ctl


HOST = os.environ.get("AIWORLD_PGHOST", "127.0.0.1")
PORT = int(os.environ.get("AIWORLD_PGPORT", "55432"))
PGDATA = Path(os.environ.get("AIWORLD_PGDATA", r"C:\AIWorld\data\postgres"))
SECRET_DIR = Path(os.environ.get("AIWORLD_SECRET_DIR", r"C:\AIWorld\data\secrets"))
BACKUP_DIR = Path(os.environ.get("AIWORLD_BACKUP_DIR", r"C:\AIWorld\backups"))
APP_USER = "aiworld"
APP_DB = "aiworld"
RESTORE_DB = "aiworld_restore_test"


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def psql(
    sql: str,
    *,
    database: str = "postgres",
    user: str = "postgres",
    password: str | None = None,
    scalar: bool = False,
) -> str:
    env = os.environ.copy()
    if password is not None:
        env["PGPASSWORD"] = password
    args = [
        str(POSTGRES_BIN_PATH / "psql.exe"),
        "-h",
        HOST,
        "-p",
        str(PORT),
        "-U",
        user,
        "-d",
        database,
        "-v",
        "ON_ERROR_STOP=1",
        "-tA" if scalar else "-q",
        "-c",
        sql,
    ]
    result = subprocess.run(args, env=env, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def tool(*args: str, password: str | None = None) -> None:
    env = os.environ.copy()
    if password is not None:
        env["PGPASSWORD"] = password
    result = subprocess.run(list(args), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {args[0]}\n{result.stderr}")


def restrict_acl(path: Path) -> None:
    subprocess.run(
        [
            "icacls",
            str(path),
            "/inheritance:r",
            "/grant:r",
            "Administrator:(R,W)",
            "SYSTEM:(R,W)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def write_secret(path: Path, value: str) -> None:
    path.write_text(value + "\n", encoding="utf-8", newline="\n")
    restrict_acl(path)


def read_or_create_secret(path: Path) -> str:
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    return secrets.token_urlsafe(32)


def ensure_role(name: str, password: str, *, superuser: bool = False) -> None:
    exists = psql(
        f"SELECT 1 FROM pg_roles WHERE rolname = {sql_literal(name)}",
        scalar=True,
    )
    if exists == "1":
        psql(
            f"ALTER ROLE {name} WITH LOGIN PASSWORD {sql_literal(password)}"
            + (" SUPERUSER" if superuser else "")
        )
    else:
        psql(
            f"CREATE ROLE {name} WITH LOGIN PASSWORD {sql_literal(password)}"
            + (" SUPERUSER" if superuser else "")
        )


def ensure_database(name: str, owner: str) -> None:
    exists = psql(
        f"SELECT 1 FROM pg_database WHERE datname = {sql_literal(name)}",
        scalar=True,
    )
    if exists != "1":
        psql(f"CREATE DATABASE {name} OWNER {owner}")


def harden_host_auth() -> None:
    path = PGDATA / "pg_hba.conf"
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "host" and parts[-1] == "trust":
            parts[-1] = "scram-sha-256"
            lines.append(" ".join(parts))
        else:
            lines.append(line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    pg_ctl(["reload"], pgdata=PGDATA, timeout=15)


def main() -> None:
    SECRET_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    app_password_path = SECRET_DIR / "aiworld_database_password.txt"
    admin_password_path = SECRET_DIR / "postgres_admin_password.txt"
    app_password = read_or_create_secret(app_password_path)
    admin_password = read_or_create_secret(admin_password_path)

    ensure_role("postgres", admin_password, superuser=True)
    ensure_role(APP_USER, app_password)
    ensure_database(APP_DB, APP_USER)
    harden_host_auth()
    write_secret(app_password_path, app_password)
    write_secret(admin_password_path, admin_password)

    identity = psql(
        "SELECT current_user || ':' || current_database()",
        database=APP_DB,
        user=APP_USER,
        password=app_password,
        scalar=True,
    )
    if identity != f"{APP_USER}:{APP_DB}":
        raise RuntimeError(f"unexpected app identity: {identity}")

    psql(
        "CREATE TABLE IF NOT EXISTS backup_probe "
        "(id integer PRIMARY KEY, note text NOT NULL); "
        "INSERT INTO backup_probe (id, note) VALUES (1, 'restore-ok') "
        "ON CONFLICT (id) DO UPDATE SET note = EXCLUDED.note",
        database=APP_DB,
        user=APP_USER,
        password=app_password,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dump_path = BACKUP_DIR / f"postgres-{APP_DB}-{stamp}.dump"
    globals_path = BACKUP_DIR / f"postgres-globals-{stamp}.sql"
    tool(
        str(POSTGRES_BIN_PATH / "pg_dump.exe"),
        "-h",
        HOST,
        "-p",
        str(PORT),
        "-U",
        APP_USER,
        "-d",
        APP_DB,
        "-Fc",
        "-f",
        str(dump_path),
        password=app_password,
    )
    tool(
        str(POSTGRES_BIN_PATH / "pg_dumpall.exe"),
        "-h",
        HOST,
        "-p",
        str(PORT),
        "-U",
        "postgres",
        "--globals-only",
        "-f",
        str(globals_path),
        password=admin_password,
    )

    psql(
        f"DROP DATABASE IF EXISTS {RESTORE_DB} WITH (FORCE)",
        password=admin_password,
    )
    psql(f"CREATE DATABASE {RESTORE_DB} OWNER {APP_USER}", password=admin_password)
    tool(
        str(POSTGRES_BIN_PATH / "pg_restore.exe"),
        "-h",
        HOST,
        "-p",
        str(PORT),
        "-U",
        APP_USER,
        "-d",
        RESTORE_DB,
        str(dump_path),
        password=app_password,
    )
    restored = psql(
        "SELECT note FROM backup_probe WHERE id = 1",
        database=RESTORE_DB,
        user=APP_USER,
        password=app_password,
        scalar=True,
    )
    if restored != "restore-ok":
        raise RuntimeError("restore verification failed")
    psql(f"DROP DATABASE {RESTORE_DB} WITH (FORCE)", password=admin_password)
    psql(
        "DROP TABLE backup_probe",
        database=APP_DB,
        user=APP_USER,
        password=app_password,
    )

    print(f"BOOTSTRAP_OK auth=scram-sha-256 identity={identity}")
    print(f"BACKUP_OK path={dump_path} bytes={dump_path.stat().st_size}")
    print(f"RESTORE_OK verified={restored}")
    print(f"GLOBALS_OK path={globals_path} bytes={globals_path.stat().st_size}")


if __name__ == "__main__":
    main()
