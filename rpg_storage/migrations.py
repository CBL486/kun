"""SQLite schema 迁移与回滚。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

LATEST_SCHEMA_VERSION = 1
MIGRATION_DIR = Path(__file__).resolve().parent / "migrations"


class ManagedConnection(sqlite3.Connection):
    """事务上下文结束时同时关闭连接，适配 Windows 文件锁。"""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, factory=ManagedConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(db_path: str | Path) -> int:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {
            row["version"]
            for row in conn.execute("SELECT version FROM schema_versions")
        }
        for version in range(1, LATEST_SCHEMA_VERSION + 1):
            if version in applied:
                continue
            script = _migration_script(version, rollback=False)
            conn.executescript(script)
            conn.execute(
                """
                INSERT INTO schema_versions(version, applied_at)
                VALUES (?, datetime('now'))
                """,
                (version,),
            )
        return int(
            conn.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_versions"
            ).fetchone()[0]
        )


def rollback(db_path: str | Path, target_version: int = 0) -> int:
    if target_version < 0 or target_version > LATEST_SCHEMA_VERSION:
        raise ValueError("target_version 无效")
    with connect(db_path) as conn:
        exists = conn.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_versions'
            """
        ).fetchone()
        if not exists:
            return 0
        current = int(
            conn.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_versions"
            ).fetchone()[0]
        )
        while current > target_version:
            conn.executescript(_migration_script(current, rollback=True))
            current -= 1
        return current


def schema_version(db_path: str | Path) -> int:
    with connect(db_path) as conn:
        exists = conn.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_versions'
            """
        ).fetchone()
        if not exists:
            return 0
        return int(
            conn.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_versions"
            ).fetchone()[0]
        )


def _migration_script(version: int, *, rollback: bool) -> str:
    direction = "rollback" if rollback else "apply"
    path = MIGRATION_DIR / f"{version:03d}_{direction}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"迁移文件不存在：{path.name}")
    return path.read_text(encoding="utf-8")
