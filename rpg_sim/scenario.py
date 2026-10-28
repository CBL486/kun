"""冻结的七日场景、实体、日程和模板。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .ids import relationship_id, stable_id

SCENARIO_ID = "slice-seven-day-v1"
SEED = 20261028
WORLD_ID = "world_qinghe_v1"
MAIN_ID = "char_lin_cheng"
OBSERVER_ID = "observer_demo_001"
TIMEZONE = "Asia/Shanghai"
START_TIME = "2026-11-02T06:40:00+08:00"
END_TIME = "2026-11-09T00:00:00+08:00"
TEMPLATE_REGISTRY_VERSION = "b1-registry-2026-10-28"
CODE_VERSION = "rpg-sim-b1-0.1.0"

ACTIONS = (
    "move",
    "attend_class",
    "study",
    "talk",
    "rest",
    "eat",
    "explore",
    "observe",
    "write_journal",
)

SLOT_WINDOWS = {
    "dawn": ("06:30", "07:29"),
    "morning_1": ("08:00", "09:30"),
    "morning_2": ("10:00", "11:30"),
    "noon": ("11:30", "13:30"),
    "afternoon_1": ("14:00", "15:30"),
    "afternoon_2": ("16:00", "17:30"),
    "evening": ("18:00", "20:30"),
    "night": ("20:30", "23:00"),
}

LOCATIONS = {
    "loc_dorm": {
        "location_id": "loc_dorm",
        "name": "宿舍",
        "kind": "dorm",
        "connected_to": ["loc_classroom", "loc_canteen", "loc_shop"],
        "open_windows": [["06:00", "23:00"]],
        "capacity": 2,
        "facilities": ["desk", "private_space", "personal_diary"],
        "scene_tags": ["private", "quiet"],
    },
    "loc_classroom": {
        "location_id": "loc_classroom",
        "name": "教学楼",
        "kind": "classroom",
        "connected_to": ["loc_dorm", "loc_canteen", "loc_library", "loc_river"],
        "open_windows": [["07:30", "18:00"]],
        "capacity": 30,
        "facilities": ["desk", "projector", "writing_table"],
        "scene_tags": ["campus", "study"],
    },
    "loc_library": {
        "location_id": "loc_library",
        "name": "青禾书院",
        "kind": "library",
        "connected_to": ["loc_dorm", "loc_classroom", "loc_canteen"],
        "open_windows": [["08:00", "21:30"]],
        "capacity": 24,
        "facilities": ["reading_desk", "notice_board", "book_returns"],
        "scene_tags": ["quiet", "books", "campus"],
    },
    "loc_canteen": {
        "location_id": "loc_canteen",
        "name": "食堂",
        "kind": "canteen",
        "connected_to": [
            "loc_dorm",
            "loc_classroom",
            "loc_library",
            "loc_shop",
        ],
        "open_windows": [["06:30", "20:00"]],
        "capacity": 60,
        "facilities": ["meal_counter", "quiet_table"],
        "scene_tags": ["food", "social"],
    },
    "loc_river": {
        "location_id": "loc_river",
        "name": "河边步道",
        "kind": "waterside",
        "connected_to": ["loc_library", "loc_classroom"],
        "open_windows": [["06:30", "19:30"]],
        "capacity": 40,
        "facilities": ["writing_bench", "cleanup_route"],
        "scene_tags": ["outdoors", "public_activity"],
    },
    "loc_shop": {
        "location_id": "loc_shop",
        "name": "便利店",
        "kind": "shop",
        "connected_to": ["loc_dorm", "loc_canteen"],
        "open_windows": [["07:00", "22:00"]],
        "capacity": 12,
        "facilities": ["snack_shelf"],
        "scene_tags": ["shop", "everyday"],
    },
}

NPCS = {
    "npc_chen": {
        "npc_id": "npc_chen",
        "display_name": "陈岚",
        "age": 41,
        "identity": "图书馆员兼校刊指导",
        "location_id": "loc_library",
        "runtime_state": "scheduled",
        "knowledge_ids": [
            "fact_library_hours",
            "fact_submission_floor_public",
            "fact_notice_board_open",
        ],
        "memory_slots": [],
    },
    "npc_su": {
        "npc_id": "npc_su",
        "display_name": "苏晚",
        "age": 20,
        "identity": "视觉传达专业二年级学生，校刊版面成员",
        "location_id": "loc_classroom",
        "runtime_state": "scheduled",
        "knowledge_ids": [
            "fact_layout_brief",
            "fact_submission_floor_public",
            "fact_photo_activity",
            "fact_public_cleanup",
        ],
        "memory_slots": [],
    },
    "npc_gao": {
        "npc_id": "npc_gao",
        "display_name": "高原",
        "age": 46,
        "identity": "食堂经营者",
        "location_id": "loc_canteen",
        "runtime_state": "scheduled",
        "knowledge_ids": ["fact_canteen_public_menu", "fact_public_sold_out"],
        "memory_slots": [],
    },
    "npc_gu": {
        "npc_id": "npc_gu",
        "display_name": "顾言",
        "age": 22,
        "identity": "摄影专业学生，校刊摄影",
        "location_id": "loc_river",
        "runtime_state": "scheduled",
        "knowledge_ids": ["fact_photo_activity", "fact_public_cleanup"],
        "memory_slots": [],
    },
}

INITIAL_RELATIONSHIPS = {
    "npc_chen": (0.18, 0.20, 0.10),
    "npc_su": (0.32, 0.27, 0.15),
    "npc_gao": (0.22, 0.30, 0.05),
    "npc_gu": (0.14, 0.22, 0.08),
}

DIRECTOR_TEMPLATES = {
    "dirtpl_campus_first_commute_v1": {
        "day": "2026-11-02",
        "kind": "routine",
        "locations": ["loc_dorm", "loc_classroom"],
        "participants": [MAIN_ID],
        "hint": "今天是本周第一次去教学楼。",
    },
    "dirtpl_library_notice_deadline_v1": {
        "day": "2026-11-02",
        "kind": "opportunity",
        "locations": ["loc_library"],
        "participants": [MAIN_ID, "npc_chen"],
        "hint": "公告栏多了一张新通知。",
    },
    "dirtpl_canteen_menu_change_v1": {
        "day": "2026-11-03",
        "kind": "social",
        "locations": ["loc_canteen"],
        "participants": [MAIN_ID, "npc_gao"],
        "hint": "食堂门口的今日菜单换了。",
    },
    "dirtpl_layout_disagreement_v1": {
        "day": "2026-11-04",
        "kind": "conflict",
        "locations": ["loc_classroom"],
        "participants": [MAIN_ID, "npc_su"],
        "hint": "苏晚把一版新的版面草稿放在桌上。",
    },
    "dirtpl_lost_notebook_v1": {
        "day": "2026-11-04",
        "kind": "mystery",
        "locations": ["loc_classroom", "loc_library"],
        "participants": [MAIN_ID, "npc_chen", "npc_gu"],
        "hint": "阅览桌边有一本无人认领的笔记本。",
    },
    "dirtpl_photo_permission_v1": {
        "day": "2026-11-05",
        "kind": "cooperation",
        "locations": ["loc_classroom", "loc_river"],
        "participants": [MAIN_ID, "npc_gu"],
        "hint": "顾言带着相机来问活动照片怎么用。",
    },
    "dirtpl_presentation_pressure_v1": {
        "day": "2026-11-05",
        "kind": "deadline",
        "locations": ["loc_classroom"],
        "participants": [MAIN_ID, "npc_su", "npc_gu"],
        "hint": "墙上的展示安排比原先更紧了。",
    },
    "dirtpl_notice_misreading_v1": {
        "day": "2026-11-06",
        "kind": "conflict",
        "locations": ["loc_library", "loc_classroom"],
        "participants": [MAIN_ID, "npc_chen", "npc_su"],
        "hint": "公告栏的提交说明多了一行楼层信息。",
    },
    "dirtpl_reconciliation_v1": {
        "day": "2026-11-06",
        "kind": "repair",
        "locations": ["loc_library", "loc_classroom"],
        "participants": [MAIN_ID, "npc_su"],
        "hint": "新的提交要求让之前的版面分工需要再核对。",
    },
    "dirtpl_river_cleanup_v1": {
        "day": "2026-11-07",
        "kind": "public_activity",
        "locations": ["loc_river"],
        "participants": [MAIN_ID, "npc_su", "npc_gu"],
        "hint": "河边集合点摆着清理工具。",
    },
    "dirtpl_rain_return_umbrella_v1": {
        "day": "2026-11-07",
        "kind": "public_activity",
        "locations": ["loc_canteen", "loc_shop"],
        "participants": [MAIN_ID, "npc_gao"],
        "hint": "食堂门边放着一把无人认领的旧伞。",
    },
    "dirtpl_sunday_letter_v1": {
        "day": "2026-11-08",
        "kind": "reflection",
        "locations": ["loc_dorm"],
        "participants": [MAIN_ID],
        "hint": "桌上的本周摘要还空着最后一段。",
    },
}

CRITICAL_TEMPLATES = {
    "dirtpl_campus_first_commute_v1",
    "dirtpl_library_notice_deadline_v1",
    "dirtpl_canteen_menu_change_v1",
    "dirtpl_layout_disagreement_v1",
    "dirtpl_photo_permission_v1",
    "dirtpl_notice_misreading_v1",
    "dirtpl_reconciliation_v1",
    "dirtpl_river_cleanup_v1",
    "dirtpl_sunday_letter_v1",
}

ACTION_TEMPLATES = {
    "move": "action_move_v1",
    "attend_class": "action_attend_class_v1",
    "study": "action_study_v1",
    "talk": "action_talk_v1",
    "rest": "action_rest_v1",
    "eat": "action_eat_v1",
    "explore": "action_explore_v1",
    "observe": "action_observe_v1",
    "write_journal": "action_journal_v1",
}


def _route(
    time: str,
    slot: str,
    action_type: str,
    target: str,
    parameters: dict[str, Any] | None = None,
    template_id: str | None = None,
) -> dict[str, Any]:
    return {
        "time": time,
        "slot": slot,
        "action_type": action_type,
        "target_id": target,
        "parameters": parameters or {},
        "template_id": template_id,
    }


DAILY_ROUTES = {
    "2026-11-02": [
        _route("06:50", "dawn", "eat", "loc_dorm", {"meal_kind": "breakfast"}),
        _route(
            "08:00",
            "morning_1",
            "move",
            "loc_classroom",
            template_id="dirtpl_campus_first_commute_v1",
        ),
        _route("08:15", "morning_1", "attend_class", "morning_1"),
        _route("09:20", "morning_1", "move", "loc_library"),
        _route(
            "10:10",
            "morning_2",
            "observe",
            "notice_board",
            {"focus_kind": "notice"},
            "dirtpl_library_notice_deadline_v1",
        ),
        _route(
            "10:30",
            "morning_2",
            "study",
            "goal_finish_feature",
            {"focus_mode": "reading"},
        ),
    ],
    "2026-11-03": [
        _route("08:00", "morning_1", "move", "loc_classroom"),
        _route("08:15", "morning_1", "attend_class", "morning_1"),
        _route("11:30", "noon", "move", "loc_canteen"),
        _route("12:00", "noon", "eat", "loc_canteen", {"meal_kind": "lunch"}),
        _route(
            "12:15",
            "noon",
            "talk",
            "npc_gao",
            {"topic": "menu", "max_turns": 2},
            "dirtpl_canteen_menu_change_v1",
        ),
        _route(
            "12:40",
            "noon",
            "study",
            "goal_finish_feature",
            {"focus_mode": "drafting"},
        ),
    ],
    "2026-11-04": [
        _route("14:00", "afternoon_1", "move", "loc_classroom"),
        _route("14:15", "afternoon_1", "attend_class", "afternoon_1"),
        _route(
            "14:40",
            "afternoon_1",
            "talk",
            "npc_su",
            {"topic": "layout", "max_turns": 2},
            "dirtpl_layout_disagreement_v1",
        ),
        _route(
            "16:00",
            "afternoon_2",
            "study",
            "goal_finish_feature",
            {"focus_mode": "drafting"},
        ),
        _route("17:00", "afternoon_2", "move", "loc_library"),
        _route(
            "17:10",
            "afternoon_2",
            "observe",
            "notice_board",
            {"focus_kind": "notice"},
        ),
    ],
    "2026-11-05": [
        _route("08:00", "morning_1", "move", "loc_classroom"),
        _route("08:15", "morning_1", "attend_class", "morning_1"),
        _route(
            "10:00",
            "morning_2",
            "talk",
            "npc_gu",
            {"topic": "photo_consent", "max_turns": 2},
            "dirtpl_photo_permission_v1",
        ),
        _route("16:00", "afternoon_2", "move", "loc_river"),
        _route(
            "16:10",
            "afternoon_2",
            "talk",
            "npc_gu",
            {"topic": "photo_scope", "max_turns": 2},
        ),
        _route(
            "16:30",
            "afternoon_2",
            "study",
            "goal_finish_feature",
            {"focus_mode": "reading"},
        ),
        _route(
            "21:30",
            "night",
            "write_journal",
            "personal_diary",
            {"trigger_id": "photo_boundary"},
        ),
    ],
    "2026-11-06": [
        _route("08:00", "morning_1", "move", "loc_library"),
        _route(
            "08:10",
            "morning_1",
            "observe",
            "notice_board",
            {"focus_kind": "notice"},
            "dirtpl_notice_misreading_v1",
        ),
        _route(
            "08:20",
            "morning_1",
            "talk",
            "npc_chen",
            {"topic": "submission_floor", "max_turns": 2},
        ),
        _route("10:00", "morning_2", "move", "loc_classroom"),
        _route(
            "10:10",
            "morning_2",
            "talk",
            "npc_su",
            {"topic": "clarify", "max_turns": 2},
            "dirtpl_reconciliation_v1",
        ),
        _route(
            "14:00",
            "afternoon_1",
            "study",
            "goal_finish_feature",
            {"focus_mode": "drafting"},
        ),
    ],
    "2026-11-07": [
        _route("06:50", "dawn", "eat", "loc_dorm", {"meal_kind": "breakfast"}),
        _route("08:00", "morning_1", "move", "loc_river"),
        _route(
            "08:15",
            "morning_1",
            "explore",
            "river_cleanup",
            {"activity_id": "river_cleanup"},
            "dirtpl_river_cleanup_v1",
        ),
        _route(
            "10:00",
            "morning_2",
            "talk",
            "npc_su",
            {"topic": "cleanup", "max_turns": 2},
        ),
        _route(
            "10:05",
            "morning_2",
            "talk",
            "npc_gu",
            {"topic": "photos", "max_turns": 2},
        ),
        _route("12:00", "noon", "eat", "loc_river", {"meal_kind": "lunch"}),
    ],
    "2026-11-08": [
        _route("06:50", "dawn", "eat", "loc_dorm", {"meal_kind": "breakfast"}),
        _route("08:00", "morning_1", "move", "loc_library"),
        _route(
            "08:10",
            "morning_1",
            "study",
            "goal_finish_feature",
            {"focus_mode": "drafting"},
        ),
        _route("16:00", "afternoon_2", "move", "loc_dorm"),
        _route("16:10", "afternoon_2", "rest", "loc_dorm", {"duration_slot_fraction": 0.5}),
        _route(
            "21:30",
            "night",
            "write_journal",
            "personal_diary",
            {"trigger_id": "week_reflection"},
            "dirtpl_sunday_letter_v1",
        ),
    ],
}

SHARE_TIME = "19:00"

SHARE_EXPECTED_TEMPLATES = {
    "2026-11-02": {
        "dirtpl_campus_first_commute_v1",
        "dirtpl_library_notice_deadline_v1",
    },
    "2026-11-03": {"dirtpl_canteen_menu_change_v1"},
    "2026-11-04": {"dirtpl_layout_disagreement_v1"},
    "2026-11-05": {"dirtpl_photo_permission_v1"},
    "2026-11-06": {
        "dirtpl_notice_misreading_v1",
        "dirtpl_reconciliation_v1",
    },
    "2026-11-07": {"dirtpl_river_cleanup_v1"},
    "2026-11-08": {"dirtpl_sunday_letter_v1"},
}


def initial_world() -> dict[str, Any]:
    relationships = {}
    for npc_id, values in INITIAL_RELATIONSHIPS.items():
        rid = relationship_id(MAIN_ID, npc_id)
        relationships[rid] = {
            "relationship_id": rid,
            "participants": [MAIN_ID, npc_id],
            "familiarity": values[0],
            "trust": values[1],
            "tension": values[2],
            "last_event_id": None,
            "change_log": [],
        }

    npcs = {}
    for npc_id, source in NPCS.items():
        npc = {key: value for key, value in source.items()}
        npc["memory_slots"] = []
        npc["relationship_id"] = relationship_id(MAIN_ID, npc_id)
        npcs[npc_id] = npc

    return {
        "schema_version": "rpg-world-v1",
        "world_id": WORLD_ID,
        "name": "青禾镇",
        "timezone": TIMEZONE,
        "seed": SEED,
        "scenario_id": SCENARIO_ID,
        "state_version": 0,
        "logical_time": START_TIME,
        "world_date": "2026-11-02",
        "open_slot": "dawn",
        "sequence": 0,
        "main_character_id": MAIN_ID,
        "npc_ids": list(NPCS),
        "location_ids": list(LOCATIONS),
        "flags": {"town_event_open": True, "rain": False},
        "characters": {
            MAIN_ID: {
                "character_id": MAIN_ID,
                "display_name": "林澄",
                "age": 19,
                "role_class": "main_agent",
                "identity": "大学一年级学生，校刊观察员",
                "location_id": "loc_dorm",
                "personality": {
                    "curiosity": 0.82,
                    "sociability": 0.46,
                    "conscientiousness": 0.71,
                    "openness": 0.88,
                },
                "needs": {
                    "energy": 0.84,
                    "hunger": 0.22,
                    "focus": 0.61,
                    "social": 0.43,
                    "stress": 0.18,
                },
                "goals": {
                    "goal_finish_feature": {
                        "goal_id": "goal_finish_feature",
                        "title": "在周五前完成校刊短文",
                        "priority": 0.76,
                        "progress": 0.15,
                        "expires_on": "2026-11-08",
                    }
                },
                "state": "calm",
                "relationship_ids": [
                    relationship_id(MAIN_ID, npc_id) for npc_id in NPCS
                ],
                "knowledge_ids": ["fact_campus_open", "fact_weekday_schedule"],
            }
        },
        "npcs": npcs,
        "locations": {
            location_id: {**location, "occupants": []}
            for location_id, location in LOCATIONS.items()
        },
        "relationships": relationships,
        "course_progress": {
            "goal_finish_feature": 0.15,
            "attendance": {},
        },
        "settled_classes": [],
        "activities": {},
        "events": [],
    }


def _minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":", maxsplit=1))
    return hour * 60 + minute


def location_is_open(location_id: str, time_text: str) -> bool:
    location = LOCATIONS[location_id]
    now = _minutes(time_text)
    return any(
        _minutes(start) <= now <= _minutes(end)
        for start, end in location["open_windows"]
    )


def scheduled_npc(npc_id: str, world_date: str, time_text: str) -> tuple[str | None, str]:
    date = datetime.fromisoformat(world_date)
    now = _minutes(time_text)
    weekday = date.weekday()

    def between(start: str, end: str) -> bool:
        return _minutes(start) <= now < _minutes(end)

    if npc_id == "npc_chen":
        if weekday >= 5:
            return ("loc_library", "available") if between("10:00", "17:00") else (None, "closed")
        if between("08:00", "12:00") or between("13:00", "17:30"):
            return "loc_library", "available"
        if between("12:00", "13:00"):
            return "loc_canteen", "available"
        return None, "closed"

    if npc_id == "npc_su":
        if weekday >= 5:
            return ("loc_river", "available") if between("10:00", "16:00") else (None, "closed")
        if between("08:00", "11:30"):
            return "loc_classroom", "available"
        if between("11:30", "13:00"):
            return "loc_canteen", "available"
        if between("14:00", "17:30"):
            return ("loc_river", "available") if weekday == 3 else ("loc_classroom", "available")
        return None, "closed"

    if npc_id == "npc_gao":
        if between("10:30", "14:00") or between("16:30", "19:30"):
            return "loc_canteen", "available"
        return None, "closed"

    if npc_id == "npc_gu":
        if weekday >= 5:
            return ("loc_river", "available") if between("10:00", "16:00") else (None, "closed")
        if between("09:00", "12:00"):
            return "loc_classroom", "available"
        if between("14:00", "17:00"):
            return "loc_river", "available"
        return None, "closed"

    raise KeyError(npc_id)


def next_world_date(world_date: str) -> str:
    return (datetime.fromisoformat(world_date) + timedelta(days=1)).date().isoformat()


def candidate_id(world_id: str, tick_id: str, template_id: str, source_seq: int) -> str:
    return stable_id("dirc", [world_id, tick_id, template_id, source_seq])
