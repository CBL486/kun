"""B6 本地演示世界、公开投影和观察者留言。"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from rpg_scheduler import PersistentMessageQueue
from rpg_sim.ids import stable_id
from rpg_sim.mocks import MockLLM, MockReviewer
from rpg_sim.scenario import LOCATIONS, MAIN_ID, SEED, location_is_open
from rpg_sim.simulator import SevenDaySimulator

from .api_models import (
    AgentPresence,
    AgentResponse,
    AgentView,
    ChatResponse,
    DiarySummaryItem,
    GoalView,
    MemoryItem,
    MemoryResponse,
    PublicLocation,
    PublicPerson,
    RelationshipView,
    TimelineItem,
    TimelineResponse,
    WorldInfo,
    WorldResponse,
)
from .persona import PersonaStore
from .world_clock import WorldClockStore

PRESENCE_STARTS = {
    "loc_dorm": (430.0, 338.0),
    "loc_classroom": (960.0, 338.0),
    "loc_library": (1510.0, 338.0),
    "loc_canteen": (530.0, 456.0),
    "loc_river": (1120.0, 724.0),
    "loc_shop": (2120.0, 456.0),
}

FACING_VALUES = {"left", "right", "up", "down"}
ANIMATION_VALUES = {
    "idle",
    "walk",
    "enter_place",
    "sit",
    "study",
    "talk",
}


class PublicProjectionError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class LocalWorldStore:
    def __init__(
        self,
        *,
        seed: int = SEED,
        reviewer: MockReviewer | None = None,
        message_store: PersistentMessageQueue | None = None,
        persona_store: PersonaStore | None = None,
        world_clock_store: WorldClockStore | None = None,
    ):
        self.seed = seed
        self.llm = MockLLM(seed)
        self.reviewer = reviewer or MockReviewer()
        self.message_store = message_store
        self.persona_store = persona_store
        self.world_clock_store = world_clock_store
        self._lock = threading.RLock()
        self._public_messages: list[dict[str, Any]] = []
        self._message_counter = 0
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self.simulator = SevenDaySimulator(seed=self.seed)
            result = self.simulator.run()
            if not result.complete:
                raise RuntimeError("本地七日场景未完成")
            self.state = self.simulator.engine.snapshot()
            self.events = [
                event
                for event in self.state["events"]
                if event["visibility"] == "user_visible"
            ]
            self.shares = list(self.simulator.daily_shares)
            self.memories = list(self.simulator.memories)
            self.diaries = list(self.simulator.diary_records)
            self._state_revision = int(self.state["state_version"])
            self._presence = self._initial_presence()
            if self.message_store:
                self._public_messages = self.message_store.list_messages()
                self._message_counter = len(self._public_messages)
            else:
                self._public_messages = []
                self._message_counter = 0

    def world(self) -> WorldResponse:
        with self._lock:
            clock = None
            if self.world_clock_store:
                clock = self.world_clock_store.advance_if_due(
                    base_revision=int(self.state["state_version"]),
                )
                if int(clock["state_revision"]) > self._state_revision:
                    self._state_revision = int(clock["state_revision"])
                    self._presence["revision"] = self._state_revision
                    self._presence["updated_at"] = clock["logical_time"]
            character = self.state["characters"][MAIN_ID]
            locations = [
                self._location(location_id)
                for location_id in self.state["location_ids"]
            ]
            people = [self._person(MAIN_ID)]
            for npc_id in self.state["npc_ids"]:
                people.append(self._person(npc_id))
            return WorldResponse(
                schema_version="rpg-public-world-v2",
                world=WorldInfo(
                    world_id=self.state["world_id"],
                    name=self.state["name"],
                    timezone=self.state["timezone"],
                    current_date=(
                        clock["logical_time"][:10]
                        if clock
                        else self.state["world_date"]
                    ),
                    current_time=(
                        clock["logical_time"][11:16]
                        if clock
                        else self.state["logical_time"][11:16]
                    ),
                    current_location_id=character["location_id"],
                    current_location_name=LOCATIONS[character["location_id"]]["name"],
                    state_revision=self._state_revision,
                    updated_at=(
                        clock["logical_time"]
                        if clock
                        else self._presence["updated_at"]
                    ),
                ),
                agent_presence=AgentPresence(**self._presence),
                locations=locations,
                people=people,
                observer_capabilities=[
                    "以只读上帝视角查看世界、角色位置与公开时间线",
                    "查看角色卡",
                    "发送受审核留言",
                    "请求角色在下一个合法时段回应",
                ],
            )

    def update_agent_presence(
        self,
        *,
        location_id: str | None = None,
        x: float | None = None,
        y: float | None = None,
        facing: str = "right",
        animation: str = "idle",
        speed: float = 0.0,
        moving: bool = False,
        updated_at: str | None = None,
        revision: int | None = None,
    ) -> AgentPresence:
        """Internal/test adapter used by agent actions, never by public writes."""
        with self._lock:
            if facing not in FACING_VALUES:
                raise PublicProjectionError(
                    "invalid_presence",
                    "角色朝向无效",
                )
            if animation not in ANIMATION_VALUES:
                raise PublicProjectionError(
                    "invalid_presence",
                    "角色动画无效",
                )
            if speed < 0:
                raise PublicProjectionError(
                    "invalid_presence",
                    "角色速度不能为负数",
                )
            target_location = (
                location_id
                or self._presence["location_id"]
                or self.state["characters"][MAIN_ID]["location_id"]
            )
            if target_location not in PRESENCE_STARTS:
                raise PublicProjectionError(
                    "invalid_presence",
                    "角色位置不属于当前世界",
                )
            default_x, default_y = PRESENCE_STARTS[target_location]
            next_revision = (
                self._state_revision + 1 if revision is None else revision
            )
            if next_revision <= self._state_revision:
                raise PublicProjectionError(
                    "stale_presence_revision",
                    "presence revision 不能回退",
                    status_code=409,
                )
            self._state_revision = next_revision
            self._presence = {
                "character_id": MAIN_ID,
                "x": round(default_x if x is None else float(x), 3),
                "y": round(default_y if y is None else float(y), 3),
                "location_id": target_location,
                "facing": facing,
                "animation": animation,
                "speed": round(float(speed), 3),
                "moving": bool(moving),
                "updated_at": updated_at or self.state["logical_time"],
                "revision": self._state_revision,
            }
            self.state["characters"][MAIN_ID]["location_id"] = target_location
            return AgentPresence(**self._presence)

    def _initial_presence(self) -> dict[str, Any]:
        location_id = self.state["characters"][MAIN_ID]["location_id"]
        x, y = PRESENCE_STARTS.get(location_id, PRESENCE_STARTS["loc_dorm"])
        return {
            "character_id": MAIN_ID,
            "x": x,
            "y": y,
            "location_id": location_id,
            "facing": "right",
            "animation": "idle",
            "speed": 0.0,
            "moving": False,
            "updated_at": self.state["logical_time"],
            "revision": self._state_revision,
        }

    def agent(self, person_id: str = MAIN_ID) -> AgentResponse:
        if person_id != MAIN_ID:
            raise PublicProjectionError(
                "unknown_character",
                "只能查看当前主智能体",
                status_code=404,
            )
        with self._lock:
            character = self.state["characters"][MAIN_ID]
            persona = self._persona_baseline()
            goal = character["goals"]["goal_finish_feature"]
            relationships = []
            for npc_id in self.state["npc_ids"]:
                npc = self.state["npcs"][npc_id]
                relationship = self.state["relationships"][npc["relationship_id"]]
                relationships.append(
                    RelationshipView(
                        person_id=npc_id,
                        name=npc["display_name"],
                        label=self._relationship_label(relationship),
                        recent_context="最近有过公开交流"
                        if relationship["change_log"]
                        else "还没有充分互动",
                    )
                )
            return AgentResponse(
                schema_version="rpg-public-agent-v1",
                agent=AgentView(
                    person_id=MAIN_ID,
                    name=persona["name"] if persona else character["display_name"],
                    age=persona["age"] if persona else character["age"],
                    identity=persona["identity"] if persona else character["identity"],
                    location_id=character["location_id"],
                    location_name=LOCATIONS[character["location_id"]]["name"],
                    mood_label=self._mood_label(character),
                    current_goal=GoalView(
                        title=goal["title"],
                        progress_label=self._progress_label(goal["progress"]),
                        due_date=goal["expires_on"],
                    ),
                    relationships=relationships,
                ),
            )

    def timeline(
        self,
        *,
        cursor: str | None = None,
        limit: int = 20,
    ) -> TimelineResponse:
        with self._lock:
            items = [self._timeline_event(event) for event in self.events]
            items.extend(self._timeline_share(share) for share in self.shares)
            items.sort(
                key=lambda item: (item.occurred_at, item.item_id),
                reverse=True,
            )
            if cursor:
                positions = {
                    item.item_id: index for index, item in enumerate(items)
                }
                if cursor not in positions:
                    raise PublicProjectionError(
                        "invalid_cursor",
                        "时间线游标无效",
                        status_code=400,
                    )
                items = items[positions[cursor] + 1 :]
            selected = items[:limit]
            next_cursor = (
                selected[-1].item_id
                if selected and len(items) > len(selected)
                else None
            )
            return TimelineResponse(
                schema_version="rpg-public-timeline-v1",
                items=selected,
                next_cursor=next_cursor,
            )

    def memory(
        self,
        *,
        kind: str | None = None,
        limit: int = 20,
    ) -> MemoryResponse:
        public_event_ids = {event["event_id"] for event in self.events}
        items = []
        with self._lock:
            for memory in self.memories:
                if memory["state"] not in {"active", "fuzzy"}:
                    continue
                if memory["source_event_id"] not in public_event_ids:
                    continue
                category = {
                    "event": "经历",
                    "reflection": "回顾",
                    "summary": "经历",
                    "relationship": "关系",
                    "preference": "偏好",
                }.get(memory["kind"])
                if not category:
                    continue
                if kind and kind != category:
                    continue
                items.append(
                    MemoryItem(
                        memory_id=memory["memory_id"],
                        date=memory["world_date"],
                        category=category,
                        summary=memory["content"],
                        source_item_id=memory["source_event_id"],
                    )
                )
            items.sort(
                key=lambda item: (item.date, item.memory_id),
                reverse=True,
            )
            diaries = [
                DiarySummaryItem(
                    diary_id=diary["diary_id"],
                    date=diary["world_date"],
                    summary=diary["summary"],
                )
                for diary in self.diaries
            ]
            diaries.sort(key=lambda item: (item.date, item.diary_id), reverse=True)
            return MemoryResponse(
                schema_version="rpg-public-memory-v1",
                items=items[:limit],
                diary_summaries=diaries[:limit],
                next_cursor=items[limit - 1].memory_id
                if len(items) > limit
                else None,
            )

    def chat(self, message: str) -> ChatResponse:
        normalized = message.strip()
        if not normalized:
            raise PublicProjectionError(
                "invalid_message",
                "留言不能为空",
                status_code=422,
            )
        review_status = self.reviewer.review(normalized)
        if review_status != "approved":
            raise PublicProjectionError(
                "content_policy_blocked",
                "留言未通过内容审核",
                status_code=422,
            )
        with self._lock:
            self._message_counter += 1
            created_at = datetime.now(timezone.utc).isoformat()
            message_id = stable_id(
                "msg",
                [self.seed, self._message_counter, normalized, created_at],
            )
            if self.message_store:
                self.message_store.enqueue(
                    message_id=message_id,
                    content=normalized,
                    created_at=datetime.fromisoformat(created_at),
                )
            else:
                self._public_messages.append(
                    {
                        "message_id": message_id,
                        "message": normalized,
                        "created_at": created_at,
                        "status": "queued",
                    }
                )
        generated = self.llm.complete(
            "observer_message_ack",
            {"message_id": message_id},
        )
        return ChatResponse(
            schema_version="rpg-public-chat-v1",
            message_id=message_id,
            status="queued",
            visible_message=normalized,
            reply=(
                "留言已收下，会留到下一个合法时段再考虑回应。"
                if generated.text.startswith("mock-observer_message_ack-")
                else generated.text
            ),
        )

    def public_event_count(self) -> int:
        with self._lock:
            return len(self.events)

    def queued_messages(self) -> list[dict[str, Any]]:
        with self._lock:
            if self.message_store:
                return self.message_store.list_messages()
            return [dict(message) for message in self._public_messages]

    def _location(self, location_id: str) -> PublicLocation:
        source = LOCATIONS[location_id]
        occupants = self.state["locations"][location_id]["occupants"]
        return PublicLocation(
            location_id=location_id,
            name=source["name"],
            kind=source["kind"],
            description="、".join(source["scene_tags"]),
            is_open=location_is_open(
                location_id,
                self.state["logical_time"][11:16],
            ),
            people=[self._display_name(character_id) for character_id in occupants],
        )

    def _person(self, person_id: str) -> PublicPerson:
        source = (
            self.state["characters"][person_id]
            if person_id == MAIN_ID
            else self.state["npcs"][person_id]
        )
        location_id = source["location_id"]
        persona = self._persona_baseline() if person_id == MAIN_ID else None
        return PublicPerson(
            person_id=person_id,
            name=persona["name"] if persona else source["display_name"],
            role="主智能体" if person_id == MAIN_ID else "小镇居民",
            identity=persona["identity"] if persona else source["identity"],
            location_id=location_id,
            location_name=LOCATIONS[location_id]["name"]
            if location_id in LOCATIONS
            else None,
        )

    def _timeline_event(self, event: dict[str, Any]) -> TimelineItem:
        type_labels = {
            "character_moved": "移动",
            "class_attended": "课堂",
            "study_progressed": "写作",
            "conversation_completed": "交流",
            "character_rested": "休息",
            "meal_completed": "用餐",
            "activity_participated": "活动",
            "detail_observed": "观察",
        }
        return TimelineItem(
            item_id=event["event_id"],
            kind="event",
            occurred_at=event["occurred_at"],
            title=type_labels.get(event["event_type"], "小镇记录"),
            summary=event["summary"],
            location_name=LOCATIONS[event.get("location_id")]["name"]
            if event.get("location_id") in LOCATIONS
            else None,
            participants=[
                self._display_name(person_id)
                for person_id in event.get("participants", [])
                if self._known_person(person_id)
            ],
        )

    def _timeline_share(self, share: dict[str, Any]) -> TimelineItem:
        return TimelineItem(
            item_id=share["share_id"],
            kind="share",
            occurred_at=share["created_at"],
            title="林澄的放学分享",
            summary=share["layers"]["reflection"],
            participants=["林澄"],
        )

    def _relationship_label(self, relationship: dict[str, Any]) -> str:
        if relationship["tension"] >= 0.45:
            return "有些紧张"
        if (
            relationship["familiarity"] >= 0.45
            and relationship["trust"] >= 0.35
        ):
            return "彼此熟悉"
        if relationship["familiarity"] >= 0.20:
            return "认识"
        return "刚刚认识"

    @staticmethod
    def _mood_label(character: dict[str, Any]) -> str:
        return {
            "calm": "平静",
            "flow": "专注",
            "low": "有些疲惫",
            "excited": "心情不错",
            "tired": "需要休息",
        }.get(character["state"], "平静")

    @staticmethod
    def _progress_label(progress: float) -> str:
        if progress >= 0.85:
            return "接近完成"
        if progress >= 0.45:
            return "正在推进"
        return "刚刚起步"

    def _display_name(self, person_id: str) -> str:
        if person_id == MAIN_ID:
            persona = self._persona_baseline()
            if persona:
                return persona["name"]
            return self.state["characters"][MAIN_ID]["display_name"]
        npc = self.state["npcs"].get(person_id)
        return npc["display_name"] if npc else "小镇居民"

    def _persona_baseline(self) -> dict[str, Any] | None:
        if not self.persona_store:
            return None
        bundle = self.persona_store.get()
        return bundle["baseline"] if bundle else None

    def _known_person(self, person_id: str) -> bool:
        return person_id == MAIN_ID or person_id in self.state["npcs"]
