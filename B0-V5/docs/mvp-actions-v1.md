# MVP 行动与事件契约 V1

状态：B0 草案，等待 G1 冻结

契约编号：`rpg-mvp-actions-v1`

日期：2026-10-28

## 1. 目的

本契约定义主智能体在 MVP 中可提交的九个原子行动、行动请求、世界引擎裁决结果、正式事件和状态修改白名单。它是阻止模型用自由文本改写世界的执行边界。

首版动作固定为：

```text
move
attend_class
study
talk
rest
eat
explore
observe
write_journal
```

新增动作必须先更新本契约、补迁移说明和测试，再经 G1 或后续契约变更批准。

## 2. ActionIntent

`ActionIntent` 是未经验证的请求：

```json
{
  "schema_version": "rpg-action-intent-v1",
  "action_id": "act_8db6e0fa1f84c690",
  "operation_id": "op_20261104_lin_morning2_01",
  "tick_id": "tick_17a4d37d520abac9",
  "world_id": "world_qinghe_v1",
  "character_id": "char_lin_cheng",
  "action_type": "observe",
  "target_id": "notice_board",
  "parameters": {
    "kind": "read_notice"
  },
  "expected_state_version": 12,
  "origin": "main_agent",
  "intent_nonce": "31ee86aac14563de"
}
```

字段要求：

| 字段 | 要求 |
| --- | --- |
| `action_id` | 由世界引擎按规范输入生成，不接受模型自定义 |
| `operation_id` | 同一逻辑推进的幂等键 |
| `tick_id` | 当前已打开 slot |
| `world_id` | 当前小镇 |
| `character_id` | 当前主智能体；NPC 需使用独立脚本反应通道 |
| `action_type` | 九个已注册动作之一 |
| `target_id` | 从当前候选集合选择的目标 |
| `parameters` | 只允许动作 schema 声明的字段 |
| `expected_state_version` | 读取感知包时的状态版本 |
| `origin` | `main_agent`、`rule_engine`、`npc_script` 或 `test` |
| `intent_nonce` | 同 tick 内区分多个候选的逻辑序号 |

请求中不得出现 `event_id`、`state_changes`、关系数值、需求数值、奖励、记忆强度、数据库路径或任意状态路径。

## 3. 总体裁决顺序

1. JSON Schema 和未知字段检查；
2. 世界、角色、目标和地点作用域检查；
3. `expected_state_version` 检查；
4. `operation_id` 是否已执行及内容是否一致；
5. 当前 slot、动作前置条件、日程和地点检查；
6. 资源、人数、关系和目标检查；
7. 年龄与内容边界检查；
8. 模型文本或对话审核；
9. 生成有界状态 patch；
10. 事务内写入 state、event 和记忆投影任务；
11. 提交成功后才暴露 `event_id`。

任一步失败返回类型化错误。失败行动保留 `action_id` 和审计记录，但不生成 `event_id`，也不留下部分状态。

## 4. 动作定义

### 4.1 `move`

**用途：** 移动到相邻且可达的地点。

**允许目标：** 当前地点 `connected_to` 中的 `loc_id`。

**前置条件：**

- 目标存在且属于当前小镇；
- 当前和目标任务在开放窗口内；
- 路径相邻，首版不进行多跳隐式移动；
- 目标人数小于容量；
- 当前没有强制课堂锁定。

**效果范围：**

```text
character.location_id
character.needs.energy  -0.02 至 -0.05
location occupant sets 由引擎派生
```

**事件类型：** `character_moved`。

### 4.2 `attend_class`

**用途：** 参加日程安排的课程或小组任务。

**允许目标：** 当前 slot 的 `schedule_entry_id`。

**前置条件：**

- slot 和课程匹配；
- 角色位于正确教室；
- 课程内容审核为 `approved`；
- 本节尚未结算。

**效果范围：**

```text
character.needs.focus    +0.05 至 +0.15
character.needs.energy   -0.08 至 -0.15
character.needs.stress   +0.00 至 +0.10
course_progress.value    +0.05 至 +0.20
course_progress.attendance = true
```

**事件类型：** `class_attended`。

### 4.3 `study`

**用途：** 推进当前课程或校刊任务。

**允许目标：** 当前角色拥有的 `goal_id`。

**前置条件：**

- 目标尚未完成；
- 地点有学习设施或允许学习；
- `focus >= 0.25`；
- 当前 slot 不是强制睡眠时段。

**效果范围：**

```text
goal.progress            +0.05 至 +0.18
character.needs.focus    -0.04 至 -0.10
character.needs.energy   -0.04 至 -0.10
character.needs.stress   +0.00 至 +0.08
```

**事件类型：** `study_progressed`。

### 4.4 `talk`

**用途：** 与在场的脚本 NPC 进行一次受控对话。

**允许目标：** 当前地点可见的 `npc_id`。

**前置条件：**

- NPC 在场且 `AVAILABLE`；
- 话题类别在允许集合内；
- NPC 拥有回答所需知识依据；
- 同一互动无冷却冲突；
- 对话输入和 NPC 台词审核通过。

**参数：**

```json
{
  "topic": "deadline",
  "max_turns": 2
}
```

`max_turns` 只能为 1 或 2。MVP 不开启自由长对话，不在 `talk` 中递归调用全量 LLM。

**效果范围：**

```text
关系单维度           -0.08 至 +0.08，且必须绑定 event_id
character.needs.social +0.04 至 +0.12
NPC memory_slot       仅在有正式事件依据时写入
```

**事件类型：** `conversation_completed`。对话没有完成、被审核阻断或 NPC 不在场时不生成完成事件。

### 4.5 `rest`

**用途：** 在安全地点短暂休息。

**允许目标：** 当前安全地点，或相邻的卧室。

**前置条件：** 地点允许休息；当前没有必须立即完成的课堂事件。

**效果范围：**

```text
character.needs.energy   +0.10 至 +0.25
character.needs.stress   -0.05 至 -0.15
character.state          由引擎重新计算
```

**事件类型：** `character_rested`。夜间睡眠使用 `rest` 的日切变体 `rest_night`，不创建第二个公开动作类型。

### 4.6 `eat`

**用途：** 在食堂、商店或宿舍用餐。

**允许目标：** 当前可用餐地点。

**前置条件：**

- 地点提供餐食或有角色库存；
- 饥饿需要允许进食；
- 用餐窗口或地点规则满足；
- 首版不做真实交易和经济。

**效果范围：**

```text
character.needs.hunger  -0.20 至 -0.45
character.needs.energy  +0.05 至 +0.15
```

**事件类型：** `meal_completed`。

### 4.7 `explore`

**用途：** 参与当前地点已注册的公开小活动，或沿相邻路径散步。

**允许目标：** 当前地点设施、相邻地点或注册活动 ID。

**前置条件：**

- 目标事件模板已注册并通过审核；
- 时间、地点和参与者满足；
- 当前不是强制课堂或睡眠时段；
- 不在冷却中。

**效果范围：**

```text
character.location_id（仅散步）
character.needs.focus      -0.02 至 +0.08
character.needs.energy     -0.02 至 -0.12
character.needs.stress     -0.10 至 +0.08
```

探索不能凭空创建地点、NPC 或奖励。

**事件类型：** `activity_participated` 或 `exploration_completed`。

### 4.8 `observe`

**用途：** 观察当前可见的设施、公开通知、场景细节或在场者外观行为。

**允许目标：** 由感知包列出的对象 ID 或场景标签。

**前置条件：**

- 对象可见；
- 角色注意力可用；
- 不读取其他角色内心、私密记忆或隐藏状态。

**效果范围：**

```text
character.needs.focus  -0.00 至 +0.06
新增可见事件记录
```

**事件类型：** `detail_observed`。

### 4.9 `write_journal`

**用途：** 主智能体在私密地点写一篇日记。

**允许目标：** 当前私密地点或随身日记本。

**前置条件：**

- 世界引擎已有日记触发条件；
- 当天尚无成功日记；
- 地点为私人空间；
- 日记内容通过审核且只引用已知事实。

**效果范围：**

```text
character.needs.stress  -0.02 至 -0.10
diary projection       最多 1 篇
memory candidate       可选 1 条 reflection
```

**事件类型：** `journal_written`。日记内容默认不是公开事件；其他 NPC 不能读取。

## 5. 动作参数范围

| 动作 | 参数 | 范围 |
| --- | --- | --- |
| `move` | 无 | 目标由 `target_id` 指定 |
| `attend_class` | 无 | 目标必须等于当前日程条目 |
| `study` | `focus_mode`（可选） | `reading`、`drafting` |
| `talk` | `topic`、`max_turns` | 话题长度 1–40 字；轮数 1–2 |
| `rest` | `duration_slot_fraction` | `0.25` 或 `0.5` |
| `eat` | `meal_kind` | `breakfast`、`lunch`、`dinner`、`snack` |
| `explore` | `activity_id` 或 `walk` | 必须来自候选集合 |
| `observe` | `focus_kind` | `notice`、`object`、`behavior` |
| `write_journal` | `trigger_id` | 必须由引擎触发 |

参数 schema 之外的字段一律拒绝。模型不能使用 `parameters` 传入补丁、脚本、SQL、URL 或工具调用。

## 6. 状态修改白名单

世界引擎只能修改以下路径：

```text
characters.<character_id>.location_id
characters.<character_id>.needs.energy
characters.<character_id>.needs.hunger
characters.<character_id>.needs.focus
characters.<character_id>.needs.social
characters.<character_id>.needs.stress
characters.<character_id>.state
characters.<character_id>.goal_progress.<goal_id>
relationships.<relationship_id>.familiarity
relationships.<relationship_id>.trust
relationships.<relationship_id>.tension
relationships.<relationship_id>.last_event_id
npc.<npc_id>.location_id
npc.<npc_id>.runtime_state
npc.<npc_id>.memory_slots
world.flags.town_event_open
world.flags.rain
world.sequence
world.state_version
```

所有数值 patch 必须有 `before`、`delta` 或 `value`、`after` 和边界。关系 patch 必须有事件依据。模型不能提交这些路径。

## 7. 正式事件

```json
{
  "schema_version": "rpg-event-v1",
  "event_id": "evt_7a4f05ce8b8093d1",
  "world_id": "world_qinghe_v1",
  "tick_id": "tick_17a4d37d520abac9",
  "action_id": "act_8db6e0fa1f84c690",
  "source_candidate_id": "dirc_aec9de812d931be4",
  "template_id": "dirtpl_library_notice_deadline_v1",
  "world_date": "2026-11-04",
  "slot_key": "morning_2",
  "sequence": 20,
  "occurred_at": "2026-11-04T10:24:00+08:00",
  "event_type": "detail_observed",
  "participants": ["char_lin_cheng"],
  "location_id": "loc_library",
  "causality": {
    "kind": "character_action",
    "reason_code": "goal_relevant_observation"
  },
  "summary": "林澄在公告栏看到截稿日期提前。",
  "state_changes": [
    {
      "path": "characters.char_lin_cheng.needs.focus",
      "operation": "delta",
      "before": 0.68,
      "value": 0.02,
      "after": 0.70
    }
  ],
  "relationship_changes": [],
  "memory_candidates": [
    {
      "candidate_index": 0,
      "kind": "event",
      "source": "school_event",
      "summary": "林澄发现校刊截稿日期提前。",
      "importance": 0.66,
      "emotional_weight": 0.42,
      "scene_tags": ["library", "deadline", "campus"]
    }
  ],
  "visibility": "user_visible",
  "review": {
    "status": "approved",
    "policy_version": "mvp-content-v1"
  },
  "state_version_before": 12,
  "state_version_after": 13,
  "committed_at": "2026-11-04T10:24:00+08:00"
}
```

规则：

- `event_id` 在事务提交后才对外可见；
- `participants` 全部存在并包含行动发起者；
- `state_changes` 只能使用白名单路径；
- `state_version_after` 必须等于 `state_version_before + 1`；
- `visibility` 只能是 `user_visible`、`character_visible` 或 `internal`；
- `memory_candidates` 保存结构化事实，不保存已生成的叙事；
- 同一事件 ID 对应不同内容时必须报冲突。

## 8. 可见范围

| 可见范围 | 谁能知道 | 能否展示 |
| --- | --- | --- |
| `user_visible` | 世界内按地点规则可感知者；世界外用户 | 可展示已提交摘要 |
| `character_visible` | 直接参与者 | 只能通过审核后的角色表达 |
| `internal` | 世界引擎 | 不展示，不进入分享和日记 |

公开用户能看地图事件和时间线，但不能看到角色全部私密事件。NPC 只能获得与其位置和知识集合匹配的可见事件。

## 9. 记忆候选和投影

每个候选由引擎生成：

```text
dedupe_key = "rpg:{event_id}:{character_id}:{candidate_index}"
```

投影规则：

- `source_event_id` 必须精确等于正式事件 ID；
- 当天的 `conversation_id` 为 `day-YYYY-MM-DD`；
- 跨日召回使用 `conversation_id=null`；
- 初始强度和情绪权重由引擎规则决定；
- 主模型不能返回记忆数值；
- 投影重放不新建记录、不重复加分；
- 私密日记只进入主智能体作用域；
- NPC 槽只通过独立 NPC 运行时写入。

## 10. 观察者互动

世界外用户可以：

- 查看世界、角色、时间线和日记；
- 发起受审核的留言或聊天；
- 对公开事件表达反应；
- 请求角色在下一个合适 slot 回应。

这些互动不直接改变位置、时间、需求、关系、课程、事件或记忆强度。它们可以生成待处理 `observer_message`，由世界引擎在下一个合法 slot 过滤和审核。

用户不能直接：

- 提交动作类型或状态 patch；
- 指定另一个 token 或事件结果；
- 读取导演隐藏分、NPC 私有记忆或主智能体完整提示；
- 让角色无视课程、睡眠和安全规则。

## 11. 标准错误码

| 错误码 | 含义 |
| --- | --- |
| `invalid_action_schema` | 缺字段、未知字段或参数越界 |
| `unsupported_action` | 不属于九个注册动作 |
| `unknown_reference` | 世界、角色、NPC、地点或目标不存在 |
| `precondition_failed` | 时间、地点、路径、资源或目标条件不满足 |
| `stale_state` | 状态版本过期 |
| `duplicate_operation` | 幂等键相同但内容不同 |
| `event_conflict` | 事件 ID、顺序或内容冲突 |
| `age_policy_blocked` | 年龄或未成年内容边界不满足 |
| `content_policy_blocked` | 输入、输出或模板审核失败 |
| `director_scope_violation` | 候选试图写状态或替角色选择 |
| `npc_knowledge_blocked` | NPC 缺少知识依据 |
| `budget_exceeded` | 模型、事件或成本预算超限 |
| `projection_failed` | 记忆投影未完成 |

## 12. 动作测试矩阵

| 测试 | 预期 |
| --- | --- |
| 九个动作各有一个合法示例 | 均生成一个事件和合法 patch |
| 模型提交未知动作 | `unsupported_action` |
| 模型提交状态路径 | `invalid_action_schema` |
| 关闭地点执行 `move` | `precondition_failed` |
| NPC 不在场执行 `talk` | `precondition_failed` |
| 过期版本提交 | `stale_state` |
| 同 operation 重放 | 返回原事件，不重复状态 |
| 事件 ID 复用到不同内容 | `event_conflict` |
| 审核阻断对话 | 无完成事件，无可见原文 |
| `internal` 事件进入分享 | 被过滤 |
| 私密日记被另一个角色读取 | 拒绝 |
| 关系变化无事件 ID | `relationship_event_required` |
| 超过每日事件硬上限 | `budget_exceeded` |
| 预算耗尽后的规则行动 | 仍可推进，不调用模型 |

## 13. 验收标准

1. 首版只存在九个注册动作。
2. 所有世界变化都由世界引擎在成功事务中提交。
3. 失败行动不会产生半条事件或部分关系变化。
4. 重试和重放不会重复事件、记忆、关系或加分。
5. 用户聊天不能直接变成世界动作。
6. NPC 对话不调用全量大模型，也不获得全局知识。
7. 所有正式状态变化都能追溯到 `event_id` 或 `action_id`。
