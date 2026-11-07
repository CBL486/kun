from __future__ import annotations

from datetime import datetime, timedelta

from app.world_clock import WORLD_TIMEZONE, WorldClockStore


START = datetime(2026, 11, 7, 8, 0, tzinfo=WORLD_TIMEZONE)


def test_world_clock_persists_and_uses_bounded_catch_up(tmp_path) -> None:
    store = WorldClockStore(tmp_path / "world", tick_interval_minutes=10)
    initial = store.advance_if_due(now=START, base_revision=49)
    assert initial["logical_time"] == START.isoformat()
    assert initial["state_revision"] == 49

    before_tick = store.advance_if_due(
        now=START + timedelta(minutes=5),
        base_revision=49,
    )
    assert before_tick == initial

    one_tick = store.advance_if_due(
        now=START + timedelta(minutes=10),
        base_revision=49,
    )
    assert one_tick["state_revision"] == 50
    assert one_tick["catch_up_mode"] == "compressed_catch_up"
    assert one_tick["compressed_ticks"] == 1
    assert "压缩为 1 个行动 tick" in one_tick["last_summary"]

    reloaded = WorldClockStore(
        tmp_path / "world",
        tick_interval_minutes=10,
    )
    resumed = reloaded.advance_if_due(
        now=START + timedelta(hours=10),
        base_revision=50,
    )
    assert resumed["state_revision"] == 109
    assert resumed["compressed_ticks"] == 59
    assert "590 分钟" in resumed["last_summary"]


def test_world_clock_offline_over_24_hours_jumps_with_summary(tmp_path) -> None:
    store = WorldClockStore(tmp_path / "world", tick_interval_minutes=10)
    store.advance_if_due(now=START, base_revision=10)
    jumped = store.advance_if_due(
        now=START + timedelta(days=3),
        base_revision=10,
    )
    assert jumped["catch_up_mode"] == "offline_summary_jump"
    assert jumped["compressed_ticks"] == 0
    assert jumped["state_revision"] == 11
    assert "超过 24 小时" in jumped["last_summary"]


def test_world_clock_interval_is_between_five_and_fifteen_minutes(tmp_path) -> None:
    try:
        WorldClockStore(tmp_path / "world", tick_interval_minutes=4)
    except ValueError as error:
        assert "between 5 and 15" in str(error)
    else:
        raise AssertionError("invalid interval should fail")
