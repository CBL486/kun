"""B6 本地演示世界、公开投影和观察者留言。"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from rpg_sim.ids import stable_id
from rpg_sim.mocks import MockLLM, MockReviewer
from rpg_sim.scenario import LOCATIONS, MAIN_ID, SEED, location_is_open
from rpg_sim.simulator import SevenDaySimulator

from .api_models import (
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
    ):
        self.seed = seed
        self.llm = MockLLM(seed)
        self.reviewer = reviewer or MockReviewer()
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
            self._public_messages = []
            self._message_counter = 0

    def world(self) -> WorldResponse:
        with self._lock:
            character = self.state["characters"][MAIN_ID]
            locations = [
                self._location(location_id)
                for location_id in self.state["location_ids"]
            ]
            people = [self._person(MAIN_ID)]
            for npc_id in self.state["npc_ids"]:
                people.append(self._person(npc_id))
            return WorldResponse(
                schema_version="rpg-public-world-v1",
                world=WorldInfo(
                    world_id=self.state["world_id"],
                    name=self.state["name"],
                    timezone=self.state["timezone"],
                    current_date=self.state["world_date"],
                    current_time=self.state["logical_time"][11:16],
                    current_location_id=character["location_id"],
                    current_location_name=LOCATIONS[character["location_id"]]["name"],
                ),
                locations=locations,
                people=people,
                observer_capabilities=[
                    "查看世界与公开时间线",
                    "查看角色卡与安全记忆摘要",
                    "发送受审核留言",
                    "请求角色在下一个合法时段回应",
                ],
            )

    def agent(self, person_id: str = MAIN_ID) -> AgentResponse:
        if person_id != MAIN_ID:
            raise PublicProjectionError(
                "unknown_character",
                "只能查看当前主智能体",
                status_code=404,
            )
        with self._lock:
            character = self.state["characters"][MAIN_ID]
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
                    name=character["display_name"],
                    age=character["age"],
                    identity=character["identity"],
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
                [self.seed, self._message_counter, normalized],
            )
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
            reply=generated.text,
        )

    def public_event_count(self) -> int:
        with self._lock:
            return len(self.events)

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
        return PublicPerson(
            person_id=person_id,
            name=source["display_name"],
            role="主智能体" if person_id == MAIN_ID else "小镇居民",
            identity=source["identity"],
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
            return self.state["characters"][MAIN_ID]["display_name"]
        npc = self.state["npcs"].get(person_id)
        return npc["display_name"] if npc else "小镇居民"

    def _known_person(self, person_id: str) -> bool:
        return person_id == MAIN_ID or person_id in self.state["npcs"]
