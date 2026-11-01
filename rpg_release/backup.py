"""Cross-database backup, restore and integrity snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


KEY_TABLES = (
    "schema_versions",
    "world_heads",
    "world_versions",
    "actions",
    "events",
    "memory_projection_outbox",
    "memories",
    "memory_mutations",
    "npc_memory_slots",
    "scheduled_tasks",
    "observer_messages",
    "llm_operations",
    "llm_usage",
    "llm_cost_attributions",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_database(url: str) -> dict[str, Any]:
    engine = create_engine(url, pool_pre_ping=True)
    try:
        tables = set(inspect(engine).get_table_names())
        counts = {}
        for table in KEY_TABLES:
            if table in tables:
                with engine.connect() as connection:
                    counts[table] = int(
                        connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"'))
                    )
        schema_version = 0
        if "schema_versions" in tables:
            with engine.connect() as connection:
                schema_version = int(
                    connection.scalar(
                        text("SELECT COALESCE(MAX(version), 0) FROM schema_versions")
                    )
                    or 0
                )
        return {
            "schema_version": schema_version,
            "table_count": len(tables),
            "tables": sorted(tables),
            "key_counts": counts,
        }
    finally:
        engine.dispose()


def backup_database(
    *,
    database_url: str,
    output: Path,
    pg_bin: Path | None = None,
) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    parsed = make_url(database_url)
    before = inspect_database(database_url)
    if parsed.get_backend_name() == "sqlite":
        database = parsed.database
        if not database or database == ":memory:":
            raise ValueError("SQLite backup requires a file database")
        source_path = Path(database).resolve()
        with sqlite3.connect(source_path) as source, sqlite3.connect(output) as target:
            source.backup(target)
    elif parsed.get_backend_name() == "postgresql":
        _run_pg_tool(
            "pg_dump",
            parsed,
            [
                "--format=custom",
                "--file",
                str(output),
            ],
            pg_bin=pg_bin,
        )
    else:
        raise ValueError("unsupported database backend")
    metadata = {
        "schema_version": "rpg-database-backup-v1",
        "backend": parsed.get_backend_name(),
        "created_at": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "file": output.name,
        "bytes": output.stat().st_size,
        "sha256": _sha256(output),
        "database_schema_version": before["schema_version"],
        "key_counts": before["key_counts"],
    }
    metadata_path = output.with_suffix(output.suffix + ".json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return metadata


def verify_backup(backup: Path) -> list[str]:
    backup = backup.resolve()
    metadata_path = backup.with_suffix(backup.suffix + ".json")
    if not backup.is_file():
        return ["backup_missing"]
    if not metadata_path.is_file():
        return ["metadata_missing"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["metadata_invalid"]
    issues = []
    if metadata.get("bytes") != backup.stat().st_size:
        issues.append("size_mismatch")
    if metadata.get("sha256") != _sha256(backup):
        issues.append("sha256_mismatch")
    return issues


def restore_database(
    *,
    backup: Path,
    database_url: str,
    confirm_restore: bool,
    pg_bin: Path | None = None,
) -> dict[str, Any]:
    if not confirm_restore:
        raise ValueError("restore requires confirm_restore=True")
    issues = verify_backup(backup)
    if issues:
        raise ValueError(f"backup verification failed: {','.join(issues)}")
    metadata = json.loads(
        backup.with_suffix(backup.suffix + ".json").read_text(encoding="utf-8")
    )
    parsed = make_url(database_url)
    if parsed.get_backend_name() == "sqlite":
        database = parsed.database
        if not database or database == ":memory:":
            raise ValueError("SQLite restore requires a file database")
        target = Path(database).resolve()
        if target.exists():
            preserved = target.with_suffix(
                target.suffix + ".before-restore"
            )
            if preserved.exists():
                raise FileExistsError(preserved)
            shutil.move(target, preserved)
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(backup) as source, sqlite3.connect(target) as restored:
            source.backup(restored)
    elif parsed.get_backend_name() == "postgresql":
        _run_pg_tool(
            "pg_restore",
            parsed,
            [
                "--clean",
                "--if-exists",
                "--no-owner",
                str(backup),
            ],
            pg_bin=pg_bin,
        )
    else:
        raise ValueError("unsupported database backend")
    after = inspect_database(database_url)
    if after["schema_version"] != metadata["database_schema_version"]:
        raise RuntimeError("restored schema version mismatch")
    if after["key_counts"] != metadata["key_counts"]:
        raise RuntimeError("restored key row counts mismatch")
    return {
        "verified": True,
        "schema_version": after["schema_version"],
        "key_counts": after["key_counts"],
    }


def _run_pg_tool(
    name: str,
    parsed,
    extra_args: list[str],
    *,
    pg_bin: Path | None,
) -> None:
    executable = None
    if pg_bin:
        candidate = pg_bin / (
            f"{name}.exe" if os.name == "nt" else name
        )
        if candidate.is_file():
            executable = candidate
    executable = executable or Path(shutil.which(name) or "")
    if not executable or not Path(executable).is_file():
        raise FileNotFoundError(f"{name} executable not found")
    if not parsed.username or not parsed.database:
        raise ValueError("PostgreSQL URL requires username and database")
    environment = os.environ.copy()
    if parsed.password:
        environment["PGPASSWORD"] = parsed.password
    command = [
        str(executable),
        "--host",
        parsed.host or "127.0.0.1",
        "--port",
        str(parsed.port or 5432),
        "--username",
        parsed.username,
        "--dbname",
        parsed.database,
        *extra_args,
    ]
    result = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed")
