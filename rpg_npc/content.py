"""课程包与事件包加载。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rpg_sim.scenario import LOCATIONS


class ContentPackError(ValueError):
    pass


def load_content_packs(base_dir: Path | None = None) -> dict[str, Any]:
    root = base_dir or Path(__file__).resolve().parents[1] / "content" / "b3"
    course_path = root / "course-pack.json"
    event_path = root / "event-pack.json"
    course_pack = json.loads(course_path.read_text(encoding="utf-8"))
    event_pack = json.loads(event_path.read_text(encoding="utf-8"))
    _validate_courses(course_pack)
    _validate_events(event_pack)
    return {"courses": course_pack, "events": event_pack}


def _validate_courses(pack: dict[str, Any]) -> None:
    if pack.get("schema_version") != "rpg-course-pack-v1":
        raise ContentPackError("课程包 schema_version 无效")
    seen = set()
    for course in pack.get("courses", []):
        required = {
            "course_id",
            "title",
            "summary",
            "source",
            "rights_status",
            "review_status",
        }
        if set(course) != required:
            raise ContentPackError("课程字段与契约不一致")
        if course["course_id"] in seen:
            raise ContentPackError("课程 ID 重复")
        seen.add(course["course_id"])
        if course["rights_status"] not in {"original", "authorized"}:
            raise ContentPackError("课程授权状态无效")
        if course["review_status"] != "approved":
            raise ContentPackError("课程未审核")


def _validate_events(pack: dict[str, Any]) -> None:
    if pack.get("schema_version") != "rpg-event-pack-v1":
        raise ContentPackError("事件包 schema_version 无效")
    seen = set()
    for event in pack.get("events", []):
        required = {
            "template_id",
            "event_type",
            "location_ids",
            "summary",
            "source",
            "rights_status",
            "review_status",
        }
        if set(event) != required:
            raise ContentPackError("事件字段与契约不一致")
        if event["template_id"] in seen:
            raise ContentPackError("事件模板 ID 重复")
        seen.add(event["template_id"])
        if event["rights_status"] not in {"original", "authorized"}:
            raise ContentPackError("事件授权状态无效")
        if event["review_status"] != "approved":
            raise ContentPackError("事件未审核")
        if any(location_id not in LOCATIONS for location_id in event["location_ids"]):
            raise ContentPackError("事件包含未知地点")
