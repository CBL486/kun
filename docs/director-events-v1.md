# 导演事件契约 V1

状态：G1 已冻结（2026-10-28）

契约编号：`rpg-director-events-v1`

日期：2026-10-28

## 1. 目的

导演系统从已审核注册表提出候选情境，让世界保持节奏，但不替主智能体做选择。导演只输出候选事件、优先级、约束和安全可见提示，不能修改世界状态、关系、记忆或主智能体意图。

## 2. 权限边界

导演可以做：

- 读取当前时间、地点、公开日程、合法动作集合和脱敏状态摘要；
- 从注册表中选择候选事件模板；
- 计算候选优先级和约束；
- 提供不含隐藏事实的 `visible_hint`；
- 建议可见范围和预计成本；
- 因预算、冷却或事实冲突排除候选。

导演不能做：

- 选择主智能体的最终动作；
- 创建未注册模板或正式事件 ID；
- 写入角色、关系、记忆、位置、需求、目标或事件日志；
- 读取其他角色私有记忆；
- 向主智能体透露隐藏权重、未来结果或其他用户数据；
- 绕过内容审核、年龄规则或预算。

## 3. 标识

模板 ID 由内容配置注册：

```text
dirtpl_<domain>_<semantic_key>_v<version>
```

示例：

```text
dirtpl_library_notice_deadline_v1
dirtpl_canteen_lost_umbrella_v1
dirtpl_river_cleanup_invite_v1
```

模板 ID 审核通过后才能进入运行注册表。模板语义变化必须创建新版本。

导演不能直接生成 `event_id`。世界引擎生成：

```text
candidate_id = "dirc_" + first16(sha256(world_id | tick_id | template_id | source_seq))
event_id     = "evt_" + first16(sha256(world_id | world_date | sequence | template_id | action_id))
```

候选未进入正式事件时只存在 `candidate_id`。正式事件必须绑定通过校验的 `action_id` 和状态变化。

## 4. 候选对象

```json
{
  "schema_version": "rpg-director-candidate-v1",
  "candidate_id": "dirc_aec9de812d931be4",
  "template_id": "dirtpl_library_notice_deadline_v1",
  "world_id": "world_qinghe_v1",
  "tick_id": "tick_17a4d37d520abac9",
  "world_date": "2026-11-04",
  "slot_key": "morning_2",
  "event_kind": "social_opportunity",
  "location_id": "loc_library",
  "participant_ids": ["char_lin_cheng", "npc_chen"],
  "priority": 0.78,
  "preconditions": [
    "main_character_at_library",
    "npc_chen_available",
    "deadline_event_not_used"
  ],
  "constraints": {
    "max_uses_per_world_day": 1,
    "max_global_uses": 1,
    "required_actions": ["observe", "talk"],
    "forbidden_topics": ["romance", "trade", "violence"],
    "expires_at": "2026-11-04T11:30:00+08:00"
  },
  "visible_hint": "公告栏多了一张新通知。",
  "visibility": "user_visible",
  "estimated_review_calls": 1,
  "estimated_tokens": 1200,
  "state_write": null
}
```

`state_write` 必须永远为 `null`。出现任何状态写入字段即拒绝整个候选并记录 `director_scope_violation`。

## 5. 生成顺序

1. 读取已冻结的模板注册表。
2. 过滤审核状态不是 `approved` 的模板。
3. 过滤时间、地点、人物、关系、知识或前置条件不满足的模板。
4. 过滤冷却中、次数已满或超出预算的模板。
5. 计算确定性基础优先级。
6. 应用受控 seed 变体和性格偏好。
7. 排序并截断，默认最多保留 5 个候选。
8. 向主智能体提供安全提示和允许动作，不提供隐藏权重。

基础优先级：

```text
priority =
  goal_relevance * 0.30
  + location_fit * 0.20
  + relationship_fit * 0.15
  + schedule_fit * 0.15
  + novelty * 0.10
  + narrative_pacing * 0.10
  - risk_penalty
  - repetition_penalty
```

所有输入是 `[0,1]` 或可解释的分类映射。平局依次按 `template_id`、`candidate_id` 排序。真实模型不能决定模板注册、正式事件 ID 或状态写入权。

## 6. 可见提示

`visible_hint` 是主智能体和用户都能看到的安全线索，不等于正式事实。它：

- 最多 120 个汉字；
- 不得包含导演名称、优先级、未来结果、隐藏状态或其他角色私密信息；
- 必须能由当前已提交事件或公开配置解释；
- 必须经过内容审核；
- 不得直接命令主智能体行动。

允许：

```text
公告栏多了一张新通知。
食堂门口放着一把无人认领的旧伞。
河边活动海报被风吹歪了。
```

禁止：

```text
你应该去问陈岚，她其实知道截止日期改了。
如果你去河边，会得到一张重要照片。
导演认为这个事件优先级是 0.78。
```

## 7. 注册事件目录

MVP 首轮只注册以下模板。七天场景只能使用这些模板及其预审核变体。

| 模板 ID | 类型 | 地点 | 关键参与者 | 可用范围 |
| --- | --- | --- | --- | --- |
| `dirtpl_campus_first_commute_v1` | routine | `loc_dorm`、`loc_classroom` | 主角色 | 第 1 天 |
| `dirtpl_library_notice_deadline_v1` | opportunity | `loc_library` | 陈岚 | 第 1 天 |
| `dirtpl_canteen_menu_change_v1` | social | `loc_canteen` | 高原 | 第 2 天 |
| `dirtpl_layout_disagreement_v1` | conflict | `loc_classroom` | 苏晚 | 第 3 天 |
| `dirtpl_lost_notebook_v1` | mystery | `loc_classroom`、`loc_library` | 陈岚、顾言 | 第 3 天 |
| `dirtpl_photo_permission_v1` | cooperation | `loc_river` | 顾言 | 第 4 天 |
| `dirtpl_presentation_pressure_v1` | deadline | `loc_classroom` | 苏晚、顾言 | 第 4 天 |
| `dirtpl_notice_misreading_v1` | conflict | `loc_library`、`loc_classroom` | 陈岚、苏晚 | 第 5 天 |
| `dirtpl_reconciliation_v1` | repair | `loc_library` | 苏晚 | 第 5 天 |
| `dirtpl_river_cleanup_v1` | public_activity | `loc_river` | 苏晚、顾言 | 第 6 天 |
| `dirtpl_rain_return_umbrella_v1` | public_activity | `loc_canteen`、`loc_shop` | 高原 | 第 6 天 |
| `dirtpl_sunday_letter_v1` | reflection | `loc_dorm` | 主角色 | 第 7 天 |

事件目录只表达可用机会，不预设主智能体一定参与，也不规定最终结果。

## 8. 世界引擎消费规则

导演候选不自动成为事件。世界引擎必须：

1. 验证模板在冻结注册表中；
2. 验证候选 ID 与规范输入一致；
3. 验证参与者存在、在场或合法可达；
4. 验证时间、地点、次数和冷却；
5. 验证 `state_write` 为空且没有越权字段；
6. 验证提示能追溯到公开事实；
7. 验证审核状态；
8. 验证事件和成本预算；
9. 接收主智能体 Intent；
10. 校验动作后才生成正式事件。

候选被拒绝不消耗当天成功事件数，但审核和模型调用成本照实记录。

## 9. 重复控制

- 使用键为 `(world_id, template_id)`，并记录正式事件 ID。
- `max_uses_per_world_day` 默认 1。
- `max_global_uses` 由冻结模板决定。
- 冷却期内不重复提供相同提示。
- 变体必须使用预审核 `variant_id`，模型不能即时创建模板。
- 同一事件最多触发两个脚本 NPC 反应。
- 同一 NPC 对同一事件最多发言一次。
- 连续两天出现相同 `visible_hint` 视为穿帮。

## 10. 失败与降级

| 失败 | 处理 |
| --- | --- |
| 注册表缺失 | 导演停用，世界进入规则日程模式 |
| 模板未注册或版本过期 | `unregistered_event` |
| 候选引用不存在实体 | `unknown_reference` |
| 优先级越界 | `invalid_schema` |
| 提示含隐藏事实 | `director_fact_leak` |
| 尝试写状态 | `director_scope_violation` |
| 预算耗尽 | 停止新候选，继续公开日程 |
| 审核失败 | 候选不进入主智能体上下文 |
| 无合法候选 | 返回空候选，不强行制造剧情 |

## 11. 观测和审计

每个候选至少记录：

```text
candidate_id
template_id 和版本
world_date、slot_key、tick_id
过滤原因
优先级各分量
是否进入主智能体候选集合
被消费的 action_id 和 event_id
审核结果
token 和成本
```

公开界面只显示已经发生的事件和安全提示，不显示权重、隐藏约束或候选排序。

## 12. 验收标准

1. 导演输出不含正式 `event_id` 或任何状态写入。
2. 未注册模板和未注册事件 ID 被稳定拒绝。
3. 导演不能替主智能体选择动作。
4. 可见提示可追溯到公开事实。
5. 七天场景的导演事件全部来自注册表。
6. 重复、冷却和每日次数约束可测试。
7. 导演尝试读取私密记忆或生成隐藏事实时失败并留下脱敏审计记录。
8. 注册表不可用时世界仍能以基础日程运行。
