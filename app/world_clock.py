"""Persistent world clock with bounded catch-up summaries."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


WORLD_TIMEZONE = ZoneInfo("Asia/Shanghai")
CLOCK_SCHEMA_VERSION = "rpg-world-clock-v1"


class WorldClockStore:
    def __init__(
        self,
        root: Path | str,
        *,
        world_id: str = "world_qinghe_v1",
        tick_interval_minutes: int = 10,
        catch_up_hours: int = 24,
    ):
        if not 5 <= tick_interval_minutes <= 15:
            raise ValueError("tick interval must be between 5 and 15 minutes")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.world_id = world_id
        self.tick_interval = timedelta(minutes=tick_interval_minutes)
        self.catch_up_window = timedelta(hours=catch_up_hours)
        self.path = self.root / "world_clock.json"
        self._guard = threading.RLock()

    @classmethod
    def from_settings(cls, settings: Any) -> "WorldClockStore":
        configured = getattr(settings, "world_clock_directory", None)
        root = Path(configured) if configured else Path.cwd() / "data" / "world"
        return cls(
            root,
            tick_interval_minutes=int(
                getattr(settings, "world_tick_minutes", 10)
            ),
        )

    def advance_if_due(
        self,
        *,
        now: datetime | None = None,
        base_revision: int = 0,
        initial_time: str | None = None,
    ) -> dict[str, Any]:
        current = _local_time(now or datetime.now(WORLD_TIMEZONE))
        with self._guard:
            state = self._read()
            if state is None:
                state = {
                    "schema_version": CLOCK_SCHEMA_VERSION,
                    "world_id": self.world_id,
                    "logical_time": _iso_time(
                        _parse_time(initial_time)
                        if initial_time
                        else current
                    ),
                    "state_revision": max(0, int(base_revision)),
                    "last_tick_at": _iso_time(current),
                    "catch_up_mode": "live",
                    "compressed_ticks": 0,
                    "last_summary": None,
                    "updated_at": _iso_time(current),
                }
                self._write(state)
                return state
            last_tick = _parse_time(state["last_tick_at"])
            elapsed = current - last_tick
            if elapsed < self.tick_interval:
                return state
            missed_ticks = max(1, int(elapsed / self.tick_interval))
            if elapsed <= self.catch_up_window:
                compressed = min(missed_ticks, 144)
                state["catch_up_mode"] = "compressed_catch_up"
                state["compressed_ticks"] = compressed
                state["state_revision"] = (
                    max(int(state["state_revision"]), int(base_revision))
                    + compressed
                )
                state["last_summary"] = (
                    f"离线 {int(elapsed.total_seconds() // 60)} 分钟，"
                    f"压缩为 {compressed} 个行动 tick。"
                )
            else:
                state["catch_up_mode"] = "offline_summary_jump"
                state["compressed_ticks"] = 0
                state["state_revision"] = (
                    max(int(state["state_revision"]), int(base_revision)) + 1
                )
                state["last_summary"] = (
                    "离线超过 24 小时，记录离线摘要后直接跳到当前时间。"
                )
            state["logical_time"] = _iso_time(current)
            state["last_tick_at"] = _iso_time(current)
            state["updated_at"] = _iso_time(current)
            self._write(state)
            return state

    def _read(self) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != CLOCK_SCHEMA_VERSION
            or payload.get("world_id") != self.world_id
        ):
            return None
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)


def run_tick() -> dict[str, Any]:
    from app.settings import settings

    store = WorldClockStore.from_settings(settings)
    return store.advance_if_due()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _local_time(parsed)


def _local_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=WORLD_TIMEZONE)
    return value.astimezone(WORLD_TIMEZONE)


def _iso_time(value: datetime) -> str:
    return _local_time(value).isoformat()


if __name__ == "__main__":
    print(json.dumps(run_tick(), ensure_ascii=False, indent=2))
