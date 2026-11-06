"""B6 公开 API 响应与请求模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    service: str


class PublicLocation(BaseModel):
    location_id: str
    name: str
    kind: str
    description: str
    is_open: bool
    people: list[str]


class WorldInfo(BaseModel):
    world_id: str
    name: str
    timezone: str
    current_date: str
    current_time: str
    current_location_id: str
    current_location_name: str


class PublicPerson(BaseModel):
    person_id: str
    name: str
    role: str
    identity: str
    location_id: str | None
    location_name: str | None


class WorldResponse(BaseModel):
    schema_version: Literal["rpg-public-world-v1"]
    world: WorldInfo
    locations: list[PublicLocation]
    people: list[PublicPerson]
    observer_capabilities: list[str]


class RelationshipView(BaseModel):
    person_id: str
    name: str
    label: str
    recent_context: str


class GoalView(BaseModel):
    title: str
    progress_label: str
    due_date: str


class AgentView(BaseModel):
    person_id: str
    name: str
    age: int
    identity: str
    location_id: str
    location_name: str
    mood_label: str
    current_goal: GoalView
    relationships: list[RelationshipView]


class AgentResponse(BaseModel):
    schema_version: Literal["rpg-public-agent-v1"]
    agent: AgentView


class TimelineItem(BaseModel):
    item_id: str
    kind: Literal["event", "share"]
    occurred_at: str
    title: str
    summary: str
    location_name: str | None = None
    participants: list[str] = Field(default_factory=list)


class TimelineResponse(BaseModel):
    schema_version: Literal["rpg-public-timeline-v1"]
    items: list[TimelineItem]
    next_cursor: str | None = None


class MemoryItem(BaseModel):
    memory_id: str
    date: str
    category: Literal["经历", "回顾", "关系", "偏好"]
    summary: str
    source_item_id: str | None = None


class DiarySummaryItem(BaseModel):
    diary_id: str
    date: str
    summary: str


class MemoryResponse(BaseModel):
    schema_version: Literal["rpg-public-memory-v1"]
    items: list[MemoryItem]
    diary_summaries: list[DiarySummaryItem]
    next_cursor: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=280,
        description="公开观察者留言，只作为待审核数据，不直接生成角色动作。",
    )


class ChatResponse(BaseModel):
    schema_version: Literal["rpg-public-chat-v1"]
    message_id: str
    status: Literal["queued"]
    visible_message: str
    reply: str


class DeepSeekKeyRequest(BaseModel):
    api_key: SecretStr = Field(
        min_length=12,
        max_length=256,
        description="只提交一次，服务端不会回显完整 Key。",
    )


class SetupCompleteRequest(BaseModel):
    pass


class SetupStatusResponse(BaseModel):
    configured: bool
    provider: Literal["deepseek"]
    key_hint: str | None
    persona_configured: bool
    world_ready: bool


class SetupValidationResponse(BaseModel):
    valid: Literal[True]
    provider: Literal["deepseek"]


class PersonaBaselineInput(BaseModel):
    name: str = Field(min_length=1, max_length=24)
    pronouns: str = Field(min_length=1, max_length=8)
    age: int = Field(ge=18, le=120)
    appearance: str = Field(min_length=1, max_length=500)
    identity: str = Field(min_length=1, max_length=500)
    speech_style: str = Field(min_length=1, max_length=300)
    traits: list[str] = Field(min_length=1, max_length=8)
    values: list[str] = Field(min_length=1, max_length=8)
    interests: list[str] = Field(min_length=1, max_length=12)
    initial_goals: list[str] = Field(min_length=1, max_length=8)
    boundaries: list[str] = Field(min_length=1, max_length=12)
    relationship_to_player: str = Field(min_length=1, max_length=300)


class PersonaBaselineView(PersonaBaselineInput):
    persona_id: str
    is_default: bool
    revision: int
    updated_at: str


class PersonaStateView(BaseModel):
    baseline_persona_id: str
    self_narrative: str
    behavior_habits: list[dict[str, Any]]
    value_weights: dict[str, float]
    interests: list[str]
    active_goals: list[str]
    change_log: list[dict[str, Any]]
    updated_at: str


class PersonaResponse(BaseModel):
    schema_version: Literal["rpg-persona-v1"]
    baseline_revision: int
    baseline: PersonaBaselineView
    state: PersonaStateView


class PersonaStatusResponse(BaseModel):
    configured: bool
    revision: int
    name: str | None
    is_default: bool


class APIErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class APIErrorResponse(BaseModel):
    schema_version: Literal["rpg-error-v1"]
    error: APIErrorDetail
