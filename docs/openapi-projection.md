# 公开 API 与投影契约

状态：生效契约（R1 升级为 world v2）

日期：2026-10-28

OpenAPI：`3.1.0`

静态契约：[openapi-v2.json](openapi-v2.json)

## 1. 端点

| 端点 | operationId | 用途 |
| --- | --- | --- |
| `GET /health` | `getHealth` | 进程存活，不依赖数据库 |
| `GET /ready` | `getReadiness` | 数据库可查询时才返回 ready |
| `GET /world` | `getWorld` | 小镇、地点、人物和观察者能力 |
| `GET /agent` | `getAgent` | 主智能体公开角色卡 |
| `GET /timeline` | `getTimeline` | 公开事件与放学分享 |
| `POST /chat` | `sendObserverMessage` | 提交受审核观察者留言 |
| `GET /api/setup/status` | `getSetupStatus` | 读取脱敏启动状态 |
| `POST /api/setup/deepseek/validate` | `validateDeepSeekKey` | 只校验 Key，不保存 |
| `POST /api/setup/deepseek/save` | `saveDeepSeekKey` | 校验并保存私有 Key |
| `POST /api/setup/complete` | `completeSetup` | 完成启动流程 |
| `POST /api/setup/deepseek/clear` | `clearDeepSeekKey` | 清除 Key，不清空世界 |
| `GET /api/persona/status` | `getPersonaStatus` | 读取人设配置状态 |
| `GET /api/persona` | `getPersona` | 读取基线与当前状态摘要 |
| `POST /api/persona/default` | `useDefaultPersona` | 使用默认原创人设 |
| `PUT /api/persona/baseline` | `replacePersonaBaseline` | 创建新的自定义基础人设 |
| `POST /api/media/observe` | `observePublicMedia` | 观察用户提供的公开视频链接 |
| `POST /api/media/bilibili/hot` | `observeBilibiliHot` | 从B站公开热门列表选择新视频 |

## 2. 响应版本

| Schema | 版本 |
| --- | --- |
| `WorldResponse` | `rpg-public-world-v2` |
| `AgentResponse` | `rpg-public-agent-v1` |
| `TimelineResponse` | `rpg-public-timeline-v1` |
| `ChatResponse` | `rpg-public-chat-v1` |
| `APIErrorResponse` | `rpg-error-v1` |

字段删除、重命名或语义变化必须升级对应版本。新增可选字段可以保持版本，但 B7 必须以响应模型为唯一字段来源。

## 3. 观察者可用字段

### 世界

```text
world.world_id
world.name
world.timezone
world.current_date
world.current_time
world.current_location_id
world.current_location_name
world.state_revision
world.updated_at
agent_presence.character_id
agent_presence.x
agent_presence.y
agent_presence.location_id
agent_presence.facing
agent_presence.animation
agent_presence.speed
agent_presence.moving
agent_presence.updated_at
agent_presence.revision
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

`location_id` 和 `location_name` 在人物离开公开地点时可以为 `null`。前端必须显示
“当前不在公开地点”，不能推测位置。`agent_presence` 是服务端权威只读投影；
公开 API 不提供位置写入端点。

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

`/memory` 已从公开 API 移除。记忆、日记和学习笔记只能由服务端内部模块、管理员
CLI 或测试工具访问，不进入玩家 UI 或公开响应。

### 观察者留言

请求只有：

```json
{
  "message": "1 至 280 字的公开留言"
}
```

响应只返回留言 ID、`delivered` 状态、已审核的可见留言和角色世界内回应。内部
消息表仍保留，用于持久化与审计，但不再把公开状态描述为“排队”。

角色回应通过 `LlmGateway` 生成，内部上下文只包括经过裁剪的 PersonaBaseline、
PersonaState、关系、情绪和有限近期事件摘要。provider、审核或预算失败时返回安全
规则文本；聊天本身不创建世界事件、关系变化或记忆。

### 启动状态

`GET /api/setup/status` 只返回：

```text
configured
provider
key_hint
persona_configured
world_ready
```

Key 只通过请求体提交一次。响应、日志、浏览器存储和 URL 不包含完整 Key。

### Persona

玩家只可写 `PersonaBaseline`，不能直接修改 `PersonaState`。每次替换基础人设都会
创建新的 `baseline_revision`；默认保留当前世界、关系、记忆和位置。响应包含玩家
可编辑的基础字段、当前自我叙事、习惯、兴趣和 change log，不包含系统提示词。

### 媒体观察

只接受 `https` 的 B站/抖音公开视频链接。重定向后的最终域名必须仍在白名单内。
观察结果只保存公开标题/简介摘要和一条私有低强度事件；不保存完整视频、登录
Cookie、账号信息或互动动作。审核失败不写记忆。

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

## 8. 本地 Mock 与生产边界

- 世界数据来自冻结 `seed=20261028` 的本地七日场景，R1 为其增加只读 presence；
- 本地和 CI 的观察者回复来自 mock provider，生产使用配置的 DeepSeek provider；
- 留言审核来自 mock 审核器；
- 模型输出审核、预算、成本统计、重试和熔断由既有 `LlmGateway` 执行；
- 留言和角色回应均不直接创建世界事件、关系变化或记忆。
