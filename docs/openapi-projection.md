# B6 公开 API 与投影契约

状态：生效契约（B6 冻结，B7 已按此验收通过）

日期：2026-10-28

OpenAPI：`3.1.0`

静态契约：[openapi-v1.json](openapi-v1.json)

## 1. 端点

| 端点 | operationId | 用途 |
| --- | --- | --- |
| `GET /health` | `getHealth` | 进程存活，不依赖数据库 |
| `GET /ready` | `getReadiness` | 数据库可查询时才返回 ready |
| `GET /world` | `getWorld` | 小镇、地点、人物和观察者能力 |
| `GET /agent` | `getAgent` | 主智能体公开角色卡 |
| `GET /timeline` | `getTimeline` | 公开事件与放学分享 |
| `POST /chat` | `sendObserverMessage` | 提交受审核观察者留言 |
| `GET /memory` | `getMemory` | 安全记忆摘要与日记摘要 |

## 2. 响应版本

| Schema | 版本 |
| --- | --- |
| `WorldResponse` | `rpg-public-world-v1` |
| `AgentResponse` | `rpg-public-agent-v1` |
| `TimelineResponse` | `rpg-public-timeline-v1` |
| `ChatResponse` | `rpg-public-chat-v1` |
| `MemoryResponse` | `rpg-public-memory-v1` |
| `APIErrorResponse` | `rpg-error-v1` |

字段删除、重命名或语义变化必须升级对应版本。新增可选字段可以保持版本，但 B7 必须以响应模型为唯一字段来源。

## 3. B7 可用字段

### 世界

```text
world.world_id
world.name
world.timezone
world.current_date
world.current_time
world.current_location_id
world.current_location_name
locations[].location_id
locations[].name
locations[].kind
locations[].description
locations[].is_open
locations[].people
people[].person_id
people[].name
people[].role
people[].identity
people[].location_id
people[].location_name
observer_capabilities[]
```

`location_id` 和 `location_name` 在人物离开公开地点时可以为 `null`。前端必须显示“当前不在公开地点”，不能推测位置。

### 角色卡

```text
agent.person_id
agent.name
agent.age
agent.identity
agent.location_id
agent.location_name
agent.mood_label
agent.current_goal.title
agent.current_goal.progress_label
agent.current_goal.due_date
agent.relationships[].person_id
agent.relationships[].name
agent.relationships[].label
agent.relationships[].recent_context
```

关系只暴露可读标签，不暴露 `familiarity`、`trust`、`tension` 数值。

### 时间线

```text
item_id
kind
occurred_at
title
summary
location_name
participants[]
next_cursor
```

`kind` 只允许 `event` 或 `share`。游标是上一页最后一项的 `item_id`。

### 记忆和日记

```text
memory_id
date
category
summary
source_item_id
diary_summaries[].diary_id
diary_summaries[].date
diary_summaries[].summary
next_cursor
```

不返回记忆分数、强度、情绪权重、作用域、去重键或完整私有记忆。

### 观察者留言

请求只有：

```json
{
  "message": "1 至 280 字的公开留言"
}
```

响应只返回留言 ID、排队状态、已审核的可见留言和安全回复。

## 4. 禁止字段

公开响应不得包含：

```text
tick_id
prompt
action_id
action_score
state
state_version
importance
emotional_weight
confidence
strength
visibility
template_id
memory_slots
scope
database_url
```

B6 测试会递归检查 JSON 字段名，并对所有公开响应执行检查。

## 5. 错误契约

所有预期错误使用：

```json
{
  "schema_version": "rpg-error-v1",
  "error": {
    "code": "database_unavailable",
    "message": "数据库当前不可用",
    "request_id": "uuid"
  }
}
```

当前错误码：

```text
database_unavailable
unknown_character
invalid_cursor
invalid_request
invalid_message
content_policy_blocked
not_found
http_error
```

错误响应不包含原始模型内容、SQL、文件路径、密钥或供应商响应。成功和错误响应都带 `X-Request-ID`。

## 6. READY 语义

- `/health` 只证明 API 进程运行；
- `/ready` 必须实际执行数据库 `SELECT 1`；
- 数据库不可用时返回 `503 database_unavailable`；
- B6 不连接生产数据库，测试通过依赖注入验证 ready/unready。

## 7. 缓存与安全头

公开 API 当前统一返回：

```text
Cache-Control: no-store
X-Content-Type-Options: nosniff
X-Request-ID: <uuid>
```

## 8. Mock 边界

- 世界数据来自冻结 `seed=20261028` 的本地七日场景；
- 观察者回复来自 mock LLM；
- 留言审核来自 mock 审核器；
- 留言只进入待处理队列，不直接创建世界事件；
- B9 接入真实供应商时必须保持本文件字段和错误契约不变。
