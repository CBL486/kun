"""稳定标识与规范 JSON。"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any, Iterable


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value))


def stable_id(prefix: str, parts: Iterable[Any]) -> str:
    payload = "|".join(normalize_text(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def relationship_id(first: str, second: str) -> str:
    low, high = sorted((normalize_text(first), normalize_text(second)))
    digest = hashlib.sha256(f"{low}\n{high}".encode("utf-8")).hexdigest()[:16]
    return f"rel_sha256_{digest}"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
