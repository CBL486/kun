"""主智能体的最小感知包。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpg_sim.scenario import LOCATIONS, MAIN_ID


@dataclass(frozen=True)
class Perception:
    tick_id: str
    world_id: str
    character_id: str
    world_date: str
    slot_key: str
    logical_time: str
    location: dict[str, Any]
    self_state: dict[str, Any]
    nearby_characters: list[dict[str, Any]]
    visible_events: list[dict[str, Any]]
    constraints: list[str]

    @classmethod
    def from_world(
        cls,
        state: dict[str, Any],
        tick_id: str,
    ) -> "Perception":
        character = state["characters"][MAIN_ID]
        location = state["locations"][character["location_id"]]
        nearby = []
        for npc_id, npc in state["npcs"].items():
            if npc["location_id"] != character["location_id"]:
                continue
            relationship = state["relationships"][npc["relationship_id"]]
            nearby.append(
                {
                    "character_id": npc_id,
                    "display_name": npc["display_name"],
                    "visible_state": npc["runtime_state"],
                    "known_relationship": {
                        "familiarity": relationship["familiarity"],
                        "trust": relationship["trust"],
                        "tension": relationship["tension"],
                    },
                }
            )
        visible_events = [
            {
                "event_id": event["event_id"],
                "summary": event["summary"],
                "event_type": event["event_type"],
                "visibility": event["visibility"],
            }
            for event in state["events"]
            if event["visibility"] == "user_visible"
        ][-12:]
        return cls(
            tick_id=tick_id,
            world_id=state["world_id"],
            character_id=MAIN_ID,
            world_date=state["world_date"],
            slot_key=state["open_slot"],
            logical_time=state["logical_time"],
            location={
                "location_id": location["location_id"],
                "name": location["name"],
                "visible_facilities": list(location["facilities"]),
                "scene_tags": list(location["scene_tags"]),
            },
            self_state={
                "needs": dict(character["needs"]),
                "state": character["state"],
                "active_goals": [
                    goal_id
                    for goal_id, goal in character["goals"].items()
                    if goal["progress"] < 1.0
                ],
            },
            nearby_characters=sorted(
                nearby,
                key=lambda item: item["character_id"],
            ),
            visible_events=visible_events,
            constraints=[
                "只能选择世界引擎提供的合法动作和目标",
                "不得声称知道未公开事件或他人私密记忆",
                "不参加恋爱、交易、冲突升级或暴力话题",
                "本次只提出一个原子动作",
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "world_id": self.world_id,
            "character_id": self.character_id,
            "world_date": self.world_date,
            "slot_key": self.slot_key,
            "logical_time": self.logical_time,
            "location": self.location,
            "self": self.self_state,
            "nearby_characters": self.nearby_characters,
            "visible_events": self.visible_events,
            "constraints": self.constraints,
        }
