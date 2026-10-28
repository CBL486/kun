# RPG 世界本体契约 V1

状态：B0 草案，等待 G1 冻结

契约编号：`rpg-world-ontology-v1`

日期：2026-10-28

## 1. 目的与效力

本契约定义单小镇 RPG MVP 的世界事实、实体、标识、数据结构和状态修改权限。实现、测试、API 示例和内容夹具都必须遵循本契约。

本文件服从以下优先级：

1. 项目所有者在本轮明确确认的结论；
2. 《协作 Agent B RPG 世界详细任务单 V5》；
3. 经 G1 冻结的 [`adr-memory-core.md`](adr-memory-core.md)；
4. 仓库中的 V2 产品设定文档；
5. 本 B0 草案。

`adr-memory-core.md` 当前是 B0 复评候选，不是已经冻结的契约。任务书引用的 `docs/adr-001-single-agent-town.md`、`docs/adr-002-mvp-runtime.md` 和上级 V4 任务书由 A 提供，待整合分支复核；B 不以这些文件已被核对为前提。

## 2. MVP 范围

一个 `world_id` 表示一个独立小镇和一个可观察的时间线。MVP 同时只推进一个小镇，小镇内有：

- 一名真正由全量 LLM 驱动的主智能体；
- 四名由确定性脚本驱动的 NPC；
- 六个地点；
- 一条北京时间日程和一条按顺序提交的事件历史；
- 一名位于世界之外、只能观察和有限互动的用户。

城镇、居民和其他真人角色互不直接产生对话。真人用户不能自由编写角色动作，不能修改世界事实，也不能绕过审核器向主智能体注入内容。

对外产品名和文案不得使用或暗示“楚门的世界”等影视 IP。

## 3. 权威边界

### 3.1 唯一事实来源

持久化的世界快照和已提交事件是唯一事实来源。地图、时间、位置、资源、行动前置条件、关系变化、课程进度和事件 ID 全部由世界引擎裁决。

模型文本、导演候选、NPC 台词、界面投影和测试报告都不是世界事实。读取视图不能反向修改世界。

### 3.2 权限矩阵

| 数据或操作 | 主智能体 LLM | 脚本 NPC | 导演系统 | 世界引擎 | 审核器 | 世界外用户 |
| --- | --- | --- | --- | --- | --- | --- |
| 选择意图 | 只能从引擎给出的候选意图中选择 | 不适用 | 不能选择 | 可以提供候选 | 不能修改 | 不能直接选择 |
| 提交事件 | 禁止 | 禁止 | 禁止 | 唯一写入方 | 禁止 | 禁止 |
| 修改位置、时间、需求、关系 | 禁止 | 只能通过运行时提出脚本反应，最终由引擎结算 | 禁止 | 唯一写入方 | 禁止 | 禁止 |
| 生成叙事文字 | 可以，必须先审核 | 可以使用已审核模板 | 不生产正式叙事 | 可以生成规则模板投影 | 只判定 | 可以输入待审核留言 |
| 生成候选事件 | 禁止 | 可按注册反应提出候选 | 可以 | 可筛选并消费 | 只判定 | 禁止 |
| 读取全部记忆 | 只能读取本次召回包 | 只能读取自己的有限记忆槽 | 禁止 | 可以按作用域读取 | 只读取待审内容 | 只能读取公开投影 |
| 显示事实 | 禁止直接显示 | 禁止直接显示 | 只能显示可见提示 | 生成公开投影 | 禁止 | 只读 |

### 3.3 必须保留的追溯链

每个正式变化至少保留以下链路：

```text
观察或日程触发
  -> tick_id
  -> 主智能体 Intent（或 NPC 脚本反应）
  -> 世界引擎校验
  -> action_id
  -> event_id
  -> state_changes[]
  -> memory_candidates[]
```

被拒绝的行动保存 `action_id`、错误码和脱敏原因，但不得生成 `event_id`，也不得改变世界状态。关系、记忆和课程进度变化必须引用产生它的 `event_id`。

## 4. 时间模型

- 世界日期使用 `Asia/Shanghai`。
- 数据库时间使用 UTC `timestamptz` 或等价的 UTC ISO-8601 文本，边界转换后展示为北京时间。
- 推进单元是离散 `slot`，不是每分钟连续模拟。
- 每个 slot 由一个 `tick_id` 标识。重试同一 tick 必须返回已有结果。
- 一次推进只允许写当前或已经打开的 slot，不能为未来 slot 提前产生正式事件，也不能回头编造已经关闭的 slot。
- `sequence` 在 `(world_id, world_date)` 内单调递增，用于给同一时段的事件稳定排序。

### 4.1 MVP 时段

| `slot_key` | 北京时间 | 默认推进内容 |
| --- | --- | --- |
| `dawn` | 06:30–07:29 | 起床、早餐、离家 |
| `morning_1` | 08:00–09:30 | 第一段课程或自习 |
| `morning_2` | 10:00–11:30 | 第二段课程或小组活动 |
| `noon` | 11:30–13:30 | 午餐与社交 |
| `afternoon_1` | 14:00–15:30 | 第三段课程或实践 |
| `afternoon_2` | 16:00–17:30 | 社团、探索或收尾 |
| `evening` | 18:00–20:30 | 回家、晚餐、分享、日记 |
| `night` | 20:30–23:00 | 私密休息与日切归档 |

同一 slot 可以提交多个按顺序排列的事件，但受每日事件和调用预算约束。

## 5. 标识规则

所有对外标识是不透明字符串，必须非空。ID 一旦分配不可复用。

### 5.1 稳定实体 ID

```text
world_id  = world_<town_key>_v1
char_id   = char_<stable_key>
npc_id    = npc_<stable_key>
loc_id    = loc_<stable_key>
rel_id    = rel_sha256_<前 16 位十六进制>
```

`rel_id` 的规范输入是两个参与者 ID 按 Unicode 码点升序排序后，以 `\n` 连接：

```text
rel_id = "rel_sha256_" + first16(sha256(lower_id + "\n" + higher_id))
```

### 5.2 操作和事件 ID

```text
tick_id    = "tick_"   + first16(sha256(world_id | char_id | world_date | slot_key | epoch))
action_id  = "act_"    + first16(sha256(tick_id | ordinal | intent_nonce))
event_id   = "evt_"    + first16(sha256(world_id | world_date | sequence | template_id | action_id))
mem_id     = "mem_"    + stable memory UUID 或去重键的确定性哈希
```

字段之间用 `|` 连接，字符串使用 NFC 规范化，日期使用 `YYYY-MM-DD`。实现可以更换编码细节，但 G1 冻结时必须满足：相同规范输入得到相同 ID，不同事件不得冲突，冲突输入必须报 `event_conflict`。

### 5.3 去重键

```text
action dedupe  = "rpg:{world_id}:{operation_id}"
event dedupe   = "rpg:{world_id}:{tick_id}:{ordinal}"
memory dedupe  = "rpg:{event_id}:{character_id}:{candidate_index}"
npc reaction   = "rpg:{event_id}:{npc_id}:{reaction_template_id}"
```

去重键相同但语义内容不同时报冲突；不同世界、角色或作用域不得共享去重键。

## 6. 核心数据结构

以下 JSON 是字段契约示例。所有对象禁止未声明字段；实现应生成 JSON Schema 并在 B5 暴露公开投影，不暴露内部字段。

### 6.1 世界状态

```json
{
  "schema_version": "rpg-world-v1",
  "world_id": "world_qinghe_v1",
  "name": "青禾镇",
  "timezone": "Asia/Shanghai",
  "seed": 20261028,
  "scenario_id": "slice-seven-day-v1",
  "state_version": 0,
  "logical_time": "2026-11-02T06:40:00+08:00",
  "world_date": "2026-11-02",
  "open_slot": "dawn",
  "sequence": 0,
  "main_character_id": "char_lin_cheng",
  "npc_ids": ["npc_chen", "npc_su", "npc_gao", "npc_gu"],
  "location_ids": ["loc_dorm", "loc_library", "loc_classroom", "loc_canteen", "loc_river", "loc_shop"],
  "flags": {
    "town_event_open": true,
    "rain": false
  }
}
```

`state_version` 每次成功提交世界变化加一。状态修改必须携带读取时的 `expected_state_version`；过期写入返回 `stale_state`。

### 6.2 角色

```json
{
  "character_id": "char_lin_cheng",
  "display_name": "林澄",
  "age": 19,
  "role_class": "main_agent",
  "identity": "大学一年级学生，校刊观察员",
  "location_id": "loc_dorm",
  "personality": {
    "curiosity": 0.82,
    "sociability": 0.46,
    "conscientiousness": 0.71,
    "openness": 0.88
  },
  "needs": {
    "energy": 0.84,
    "hunger": 0.22,
    "focus": 0.61,
    "social": 0.43,
    "stress": 0.18
  },
  "goals": [
    {
      "goal_id": "goal_finish_feature",
      "kind": "deadline",
      "priority": 7,
      "progress": 0.15,
      "expires_on": "2026-11-08"
    }
  ],
  "state": "calm",
  "relationship_ids": ["rel_sha256_42145af6cd367cdc"],
  "knowledge_ids": ["fact_campus_open", "fact_weekday_schedule"]
}
```

数值型性格和需求都在 `[0,1]`。`state` 仅允许 `flow`、`calm`、`low`、`excited`、`tired`，只供世界引擎和诊断使用。

### 6.3 地点

```json
{
  "location_id": "loc_library",
  "name": "青禾书院",
  "kind": "library",
  "connected_to": ["loc_dorm", "loc_classroom", "loc_canteen"],
  "open_windows": [["08:00", "21:30"]],
  "capacity": 24,
  "occupants": ["char_lin_cheng", "npc_chen"],
  "facilities": ["reading_desk", "notice_board", "book_returns"],
  "scene_tags": ["quiet", "books", "campus"]
}
```

地点不存在、关闭、满员或无可达路径时必须拒绝移动。`occupants` 由世界引擎维护，模型不得提交。

### 6.4 NPC

```json
{
  "npc_id": "npc_chen",
  "display_name": "陈岚",
  "age": 41,
  "role_class": "npc",
  "identity": "图书馆员兼校刊指导",
  "location_id": "loc_library",
  "schedule_id": "schedule_npc_chen",
  "relationship_ids": ["rel_sha256_42145af6cd367cdc"],
  "knowledge_ids": ["fact_library_hours", "fact_notice_board_open"],
  "memory_slots": [],
  "runtime_state": "working"
}
```

NPC 不拥有 LLM 上下文，不共享主智能体记忆，不能读取未公开事实。完整运行时契约见 [`npc-script-runtime-v1.md`](npc-script-runtime-v1.md)。

### 6.5 关系

```json
{
  "relationship_id": "rel_sha256_42145af6cd367cdc",
  "participants": ["char_lin_cheng", "npc_chen"],
  "familiarity": 0.18,
  "trust": 0.20,
  "tension": 0.10,
  "last_event_id": null,
  "change_log": []
}
```

三个关系维度都限制在 `[0,1]`。每次变化必须满足：

```json
{
  "relationship_id": "rel_sha256_42145af6cd367cdc",
  "dimension": "trust",
  "before": 0.2,
  "delta": 0.04,
  "after": 0.24,
  "event_id": "evt_7a4f05ce8b8093d1"
}
```

没有 `event_id` 的关系变化是无效变化。模型不能输出关系数值。

### 6.6 回忆和关系记忆

```json
{
  "memory_id": "mem_f3fd6e9a31fb9a6c",
  "scope": {
    "tenant_id": "rpg-world",
    "world_id": "world_qinghe_v1",
    "user_id": "observer_demo_001",
    "character_id": "char_lin_cheng",
    "surface": "school",
    "conversation_id": "day-2026-11-04"
  },
  "kind": "event",
  "source": "school_event",
  "content": "林澄在公告栏发现校刊截稿日期提前，但没有告诉其他人。",
  "source_event_id": "evt_6b762a4a51c0381e",
  "importance": 0.66,
  "emotional_weight": 0.42,
  "confidence": 0.98,
  "strength": 0.73,
  "scene_tags": ["library", "deadline", "private"],
  "created_at": "2026-11-04T10:24:00+08:00",
  "locked": false,
  "state": "active",
  "dedupe_key": "rpg:evt_6b762a4a51c0381e:char_lin_cheng:0"
}
```

记忆字段必须兼容 [`adr-memory-core.md`](adr-memory-core.md)。至少需要 `event`、`reflection`、`summary` 三类。主智能体跨日召回时使用 `conversation_id=null`；当天事件写入使用 `day-YYYY-MM-DD`。

### 6.7 主智能体目标

```json
{
  "goal_id": "goal_finish_feature",
  "title": "在周五前完成校刊短文",
  "kind": "deadline",
  "priority": 0.76,
  "progress": 0.15,
  "target": {
    "kind": "course_progress",
    "value": 1.0
  },
  "constraints": ["library_hours", "does_not_skip_class"],
  "created_by": "world_engine",
  "source_event_id": null,
  "expires_on": "2026-11-08"
}
```

目标由世界引擎维护。LLM 可以建议目标措辞或优先级解释，但不能直接写入目标。

## 7. 世界规则

### 7.1 感知边界

主智能体只能收到当前地点、当前时段、公开事件、附近角色、可见设施和召回记忆。它不能收到：

- 其他角色私有记忆槽；
- 未公开事件全文；
- 导演的隐藏权重；
- 数据库查询、提示词、密钥和文件路径；
- 用户真实身份或平台账号资料。

### 7.2 状态修改

所有正式修改由世界引擎转化为有界 patch，并绑定 `event_id`。允许字段和上下限在 [`mvp-actions-v1.md`](mvp-actions-v1.md) 中定义。任何 patch 失败都使整个事件事务回滚。

### 7.3 重放

相同 `operation_id`、seed、状态快照和输入重放时返回原结果。相同去重键内容不一致时返回冲突。重放不能再次增加关系、分数、成本预算中的成功用量或事件数。

## 8. 年龄、内容和隐私边界

- 用户协议只允许年满 18 周岁的真人用户。
- MVP 主智能体为 19 岁大学生；所有对外可见 NPC 均为 18 岁以上成年人。
- 系统不允许涉及未成年角色的性内容。年龄缺失、非法年龄或设定冲突时返回 `age_policy_blocked`。
- MVP 不提供恋爱、约会、性化、战斗、交易、赌博或打工经济系统。
- NPC 不得诱导依赖、替代现实关系或索取真实个人信息。
- 真实账号标识不进入故事、公开 URL、日志或模型上下文；开发测试只使用合成数据。
- 用户留言、模型输出和可见故事全部经过审核；审核失败不能直接回退到原文。

## 9. 错误契约

世界层至少返回以下类型化错误：

| 错误码 | 含义 |
| --- | --- |
| `invalid_schema` | 字段缺失、字段越界或未知字段 |
| `unknown_reference` | 世界、角色、NPC、地点或事件不存在 |
| `stale_state` | 状态版本过期 |
| `duplicate_operation` | 幂等键重复且内容不同 |
| `event_conflict` | 事件 ID、序号或内容冲突 |
| `precondition_failed` | 时间、地点、路径、资源或目标不满足 |
| `director_scope_violation` | 导演试图写状态或生成未注册事件 |
| `knowledge_scope_violation` | NPC 或角色读取禁止事实 |
| `age_policy_blocked` | 年龄或未成年性内容边界不满足 |
| `content_policy_blocked` | 审核拒绝 |
| `budget_exceeded` | 预算达到硬上限 |
| `projection_failed` | 事件后记忆投影未完成 |

错误响应只包含稳定错误码、安全的用户提示和关联 ID，不得包含原始用户内容、模型提示、SQL、凭据或服务商响应。

## 10. 验收标准

1. A 仅凭本契约和权限矩阵就能判断每个字段由谁写入。
2. 每一个行动、事件、关系变化和记忆变化都有唯一的稳定 ID 或去重键。
3. 同一 tick 重放不会重复改变状态、关系、预算或记忆。
4. 模型输出无法直接修改位置、时间、需求、关系或事件。
5. NPC 无法读取未公开事件或其他角色私有记忆。
6. 七天场景只使用本契约定义的 ID、实体和状态范围。
7. 年龄、内容和隐私边界在数据模型和测试中都有可执行错误码。
8. 快照导出并重新导入后，状态版本和业务含义不变。
