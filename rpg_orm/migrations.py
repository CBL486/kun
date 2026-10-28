"""SQLAlchemy 双后端迁移与回滚。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Engine,
    create_engine,
    event,
    inspect as sqlalchemy_inspect,
    select,
)
from sqlalchemy.orm import Session

from .models import Base, SchemaVersionRow

LATEST_SCHEMA_VERSION = 1


def create_database_engine(url: str, *, echo: bool = False) -> Engine:
    normalized = url
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )
    if normalized.startswith("sqlite:///"):
        path_text = normalized.removeprefix("sqlite:///")
        if path_text != ":memory:":
            Path(path_text).resolve().parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(normalized, echo=echo, pool_pre_ping=True)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
    return engine


def migrate(engine: Engine) -> int:
    Base.metadata.create_all(engine, checkfirst=True)
    with Session(engine) as session, session.begin():
        row = session.get(SchemaVersionRow, LATEST_SCHEMA_VERSION)
        if not row:
            session.add(
                SchemaVersionRow(
                    version=LATEST_SCHEMA_VERSION,
                    applied_at=datetime.now(timezone.utc),
                )
            )
    return schema_version(engine)


def rollback(engine: Engine) -> int:
    Base.metadata.drop_all(engine, checkfirst=True)
    return 0


def schema_version(engine: Engine) -> int:
    inspector = sqlalchemy_inspect(engine)
    if "schema_versions" not in inspector.get_table_names():
        return 0
    with Session(engine) as session:
        versions = session.scalars(select(SchemaVersionRow.version)).all()
        return max(versions, default=0)
