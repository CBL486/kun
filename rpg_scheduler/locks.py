"""PostgreSQL advisory locks with a local SQLite-compatible fallback."""

from __future__ import annotations

import hashlib
import threading
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, text


_LOCAL_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


def advisory_key(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFF_FFFF


def _local_lock(name: str) -> threading.Lock:
    with _LOCAL_LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(name, threading.Lock())


@contextmanager
def advisory_lock(
    engine: Engine,
    value: str,
    *,
    namespace: int = 1834,
) -> Iterator[bool]:
    """Try a non-blocking lock for the duration of the context."""

    key = advisory_key(value)
    if engine.dialect.name == "postgresql":
        with engine.connect() as connection:
            acquired = bool(
                connection.scalar(
                    text(
                        "SELECT pg_try_advisory_lock("
                        ":namespace, :key)"
                    ),
                    {"namespace": namespace, "key": key},
                )
            )
            try:
                yield acquired
            finally:
                if acquired:
                    connection.execute(
                        text(
                            "SELECT pg_advisory_unlock("
                            ":namespace, :key)"
                        ),
                        {"namespace": namespace, "key": key},
                    )
        return

    lock = _local_lock(f"{engine.url}:{namespace}:{key}")
    acquired = lock.acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            lock.release()
