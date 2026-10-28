"""四名 NPC 的确定性日程和状态机。"""

from __future__ import annotations

from datetime import datetime

from .models import RuntimeState, ScheduleState

SLOT_TIMES = {
    "dawn": "06:45",
    "morning_1": "08:15",
    "morning_2": "10:15",
    "noon": "12:15",
    "afternoon_1": "14:15",
    "afternoon_2": "16:15",
    "evening": "19:00",
    "night": "22:00",
}

ALLOWED_TRANSITIONS = {
    RuntimeState.SCHEDULED: {
        RuntimeState.COMMUTING,
        RuntimeState.AVAILABLE,
        RuntimeState.CLOSED,
    },
    RuntimeState.COMMUTING: {
        RuntimeState.AVAILABLE,
        RuntimeState.BUSY,
        RuntimeState.CLOSED,
    },
    RuntimeState.AVAILABLE: {
        RuntimeState.REACTION_PENDING,
        RuntimeState.INTERACTION_COOLDOWN,
        RuntimeState.BUSY,
        RuntimeState.CLOSED,
        RuntimeState.ASLEEP,
    },
    RuntimeState.REACTION_PENDING: {
        RuntimeState.AVAILABLE,
        RuntimeState.INTERACTION_COOLDOWN,
    },
    RuntimeState.INTERACTION_COOLDOWN: {
        RuntimeState.AVAILABLE,
        RuntimeState.BUSY,
        RuntimeState.CLOSED,
    },
    RuntimeState.BUSY: {
        RuntimeState.AVAILABLE,
        RuntimeState.CLOSED,
        RuntimeState.ASLEEP,
    },
    RuntimeState.CLOSED: {
        RuntimeState.ASLEEP,
        RuntimeState.SCHEDULED,
    },
    RuntimeState.ASLEEP: {
        RuntimeState.SCHEDULED,
        RuntimeState.COMMUTING,
    },
}


def can_transition(current: RuntimeState, target: RuntimeState) -> bool:
    return current == target or target in ALLOWED_TRANSITIONS[current]


def _minutes(time_text: str) -> int:
    hour, minute = (int(part) for part in time_text.split(":", maxsplit=1))
    return hour * 60 + minute


def _between(now: int, start: str, end: str) -> bool:
    return _minutes(start) <= now < _minutes(end)


def schedule_state(
    npc_id: str,
    world_date: str,
    time_text: str,
    slot_key: str,
) -> ScheduleState:
    weekday = datetime.fromisoformat(world_date).weekday()
    now = _minutes(time_text)

    location: str | None = None
    state = RuntimeState.CLOSED

    if npc_id == "npc_chen":
        if weekday >= 5:
            if _between(now, "10:00", "17:00"):
                location, state = "loc_library", RuntimeState.AVAILABLE
        elif _between(now, "08:00", "12:00") or _between(now, "13:00", "17:30"):
            location, state = "loc_library", RuntimeState.AVAILABLE
        elif _between(now, "12:00", "13:00"):
            location, state = "loc_canteen", RuntimeState.AVAILABLE
    elif npc_id == "npc_su":
        if weekday >= 5:
            if _between(now, "10:00", "16:00"):
                location, state = "loc_river", RuntimeState.AVAILABLE
        elif _between(now, "08:00", "11:30"):
            location, state = "loc_classroom", RuntimeState.AVAILABLE
        elif _between(now, "11:30", "13:00"):
            location, state = "loc_canteen", RuntimeState.AVAILABLE
        elif _between(now, "14:00", "17:30"):
            location = "loc_river" if weekday == 3 else "loc_classroom"
            state = RuntimeState.AVAILABLE
    elif npc_id == "npc_gao":
        if _between(now, "06:00", "09:00"):
            location, state = "loc_canteen", RuntimeState.BUSY
        elif _between(now, "10:30", "14:00") or _between(now, "16:30", "19:30"):
            location, state = "loc_canteen", RuntimeState.AVAILABLE
    elif npc_id == "npc_gu":
        if weekday >= 5:
            if _between(now, "10:00", "16:00"):
                location, state = "loc_river", RuntimeState.AVAILABLE
        elif _between(now, "08:00", "09:00"):
            location, state = "loc_classroom", RuntimeState.COMMUTING
        elif _between(now, "09:00", "12:00"):
            location, state = "loc_classroom", RuntimeState.AVAILABLE
        elif _between(now, "14:00", "17:00"):
            location, state = "loc_river", RuntimeState.AVAILABLE
    else:
        raise KeyError(f"unknown_npc:{npc_id}")

    if now < 6 * 60 or now >= 21 * 60:
        location = None
        state = RuntimeState.ASLEEP
    elif location is None:
        state = RuntimeState.CLOSED

    return ScheduleState(
        slot_key=slot_key,
        time=time_text,
        location_id=location,
        runtime_state=state,
    )


def day_schedule(npc_id: str, world_date: str) -> dict[str, ScheduleState]:
    return {
        slot_key: schedule_state(npc_id, world_date, time_text, slot_key)
        for slot_key, time_text in SLOT_TIMES.items()
    }
