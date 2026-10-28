# 主智能体循环契约 V1

状态：B0 草案，等待 G1 冻结

契约编号：`rpg-agent-loop-v1`

日期：2026-10-28

## 1. 目的

本契约定义单镇中唯一主智能体的感知、记忆召回、意图形成、行动选择、表达和反思循环。目标是让主智能体拥有连续生活感，同时保证世界结果只由世界引擎产生。

一个镇只能有一个主智能体使用全量 LLM。其他居民只能是脚本 NPC，不得偷偷升级为第二个常驻模型智能体。

## 2. 核心原则

- 世界状态是唯一事实来源。
- LLM 只提出结构化意图和表达文本。
- 意图必须从世界引擎提供的合法候选集合中选择。
- 正式结果由世界引擎校验、裁决并生成事件。
- 每次推进有固定 `tick_id` 和 `operation_id`，可以重放。
- 模型失败、超时和审核失败均有确定降级路径。
- 故事只能引用本次已召回的记忆和已提交的可见事件。
- 世界行为可复现；真实模型生成的文字允许不同，但事实来源必须相同。

## 3. 循环状态机

```text
WAITING
  -> LOCKED
  -> SNAPSHOT_READ
  -> MEMORY_RECALLED
  -> INTENT_PROPOSED
  -> VALIDATED
  -> COMMITTED
  -> PROJECTED
  -> RELEASED
```

任意校验失败进入 `REJECTED`，模型不可用进入 `DEGRADED`。事件已提交但记忆投影未完成时进入 `RECONCILIATION_REQUIRED`，不能向界面报告该次推进已完整完成。

### 3.1 步骤

1. 世界引擎打开当前 slot，生成或恢复 `tick_id`。
2. 按 `(world_id, character_id, world_date, slot_key)` 获取角色锁。
3. 读取带 `state_version` 的世界快照和公开感知包。
4. 如果 `operation_id` 已有结果，返回原结果；内容不同则报冲突。
5. 检查是否已经生成过当前 tick 的正式事件。
6. 按完整 `Scope` 召回有限记忆，并保存可解释召回结果。
7. 世界引擎计算合法动作、目标、约束和候选事件。
8. 主智能体在候选内提出一个 `Intent`。
9. 世界引擎做结构、范围、权限、前置条件和年龄内容校验。
10. 世界引擎裁决并在一个事务中写入 state patch 和正式事件。
11. 生成事件关联的记忆候选，幂等投影到记忆核心。
12. 如有需要，生成审核后的叙事投影、对话或分享。
13. 写入运行统计，释放锁并返回结果。

第 10 至 12 步必须处于同一数据库事务，或由可测试的待投影记录和核对流程保证。事件已提交但记忆丢失，不能报告为成功。

## 4. 感知包

主智能体不能读取世界数据库。世界引擎生成最小化、已过滤的感知包：

```json
{
  "tick_id": "tick_17a4d37d520abac9",
  "world_id": "world_qinghe_v1",
  "character_id": "char_lin_cheng",
  "world_date": "2026-11-04",
  "slot_key": "morning_2",
  "logical_time": "2026-11-04T10:14:00+08:00",
  "location": {
    "location_id": "loc_library",
    "name": "青禾书院",
    "visible_facilities": ["notice_board", "reading_desk"],
    "scene_tags": ["quiet", "campus"]
  },
  "self": {
    "needs": {"energy": 0.75, "hunger": 0.31, "focus": 0.68, "social": 0.42, "stress": 0.24},
    "state": "calm",
    "active_goals": ["goal_finish_feature"]
  },
  "nearby_characters": [
    {
      "character_id": "npc_chen",
      "display_name": "陈岚",
      "visible_state": "整理书架",
      "known_relationship": {"familiarity": 0.18, "trust": 0.20, "tension": 0.10}
    }
  ],
  "visible_events": [
    {
      "event_id": "evt_f3c84ba429a8076e",
      "summary": "公告栏贴出“本周五截稿”的新通知。",
      "event_type": "notice_observed",
      "visibility": "user_visible"
    }
  ],
  "allowed_actions": [
    {"action_type": "observe", "target_ids": ["notice_board"], "parameter_schema": {"kind": "enum", "values": ["read_notice"]}},
    {"action_type": "talk", "target_ids": ["npc_chen"], "parameter_schema": {"topic": "string", "max_length": 120}},
    {"action_type": "move", "target_ids": ["loc_classroom"], "parameter_schema": {}},
    {"action_type": "study", "target_ids": ["goal_finish_feature"], "parameter_schema": {}}
  ],
  "constraints": [
    "不得声称知道未列出的通知内容",
    "不参加恋爱、冲突升级或交易话题",
    "本次只能选择一个动作"
  ]
}
```

感知包不得包含完整记忆库、其他角色私有记忆、导演隐藏分数、数据库路径、模型提示词、真实用户资料或密钥。

## 5. Intent 契约

主智能体必须返回一个结构化对象。若输出无法解析，视为本次模型失败，不能把自然语言猜测成动作。

```json
{
  "schema_version": "rpg-intent-v1",
  "operation_id": "op_20261104_lin_morning2_01",
  "tick_id": "tick_17a4d37d520abac9",
  "character_id": "char_lin_cheng",
  "intent_id": "intent_31ee86aac14563de",
  "action_type": "observe",
  "target_id": "notice_board",
  "parameters": {
    "kind": "read_notice"
  },
  "reason": "截稿日期变化与自己的目标直接相关。",
  "expected_outcome": "看清通知，更新对截止日期的理解。",
  "confidence": 0.83
}
```

允许字段只有上述字段。模型不能提交：

- `event_id`、`state_changes`、关系数值、需求数值、奖励或成本；
- 任意数据库路径、状态路径或补丁操作；
- 候选集合之外的动作、目标或地点；
- 其他角色 ID、真实账号信息或系统提示；
- 多步链式动作或隐藏工具调用。

`reason` 与 `expected_outcome` 仅用于可解释记录，不构成世界事实。

## 6. 决策与候选

世界引擎根据日程、位置、需求、目标、关系和近期事件生成合法候选。排序可以是规则或模型辅助，但：

1. 候选集合之外的动作永远拒绝；
2. 模型不能选择导演事件 ID；
3. 模型可以选择拒绝所有候选并表达“暂不行动”，此时返回 `no_op`；
4. 无合法候选时生成 `no_op`，而不是生成一个虚构行动；
5. 相同 seed、状态和规则模式必须产生相同决策轨迹；
6. 选择依据保存为脱敏 `decision_trace`，不暴露给用户界面。

```json
{
  "decision_trace": {
    "mode": "rule_only",
    "candidates": [
      {"action_type": "observe", "score": 0.82, "reason_codes": ["goal_relevant", "at_location"]},
      {"action_type": "talk", "score": 0.31, "reason_codes": ["npc_present"]}
    ],
    "selected_action": "observe",
    "model_used": false
  }
}
```

## 7. 记忆召回与写回

### 7.1 召回作用域

学校世界使用：

```text
tenant_id    = "rpg-world"
world_id     = 当前小镇
user_id      = 当前世界观察者
character_id = 主智能体
surface      = "school"
conversation_id = null
```

每次召回必须有 `max_items` 和 `max_tokens`。保存 `memory_id`、分数分解和选择原因供本地诊断，但用户界面不得显示分数。

### 7.2 写回

- 事件成功后生成 `event` 记忆候选；
- 高情绪或世界引擎触发时可生成 `reflection` 候选；
- 放学分享成功后生成独立 `summary` 记忆；
- 日记成功后生成独立 `diary` 记忆；
- 去重键为 `rpg:{event_id}:{character_id}:{candidate_index}`；
- 初始 importance、emotional weight 和 strength 由世界引擎规则决定；
- 分享、情境触发和重述的强化必须使用唯一操作 ID；
- 投影重放返回原记录，不重复加行或加分；
- 私密记忆只写入对应角色作用域。

没有召回到的记忆不能被写成“我记得”。允许表达不确定，不允许补造过去事实。

## 8. 叙事与表达

正式叙事分四种：

| 类型 | 输入 | 约束 |
| --- | --- | --- |
| 行动叙述 | 已提交事件 | 不得添加未记录的结果 |
| 对话 | 已提交说话事件和有限感知包 | 不得全知，不得写他人内心 |
| 放学分享 | 当日 3 至 5 件可见事件 | 必须为“发生—感受—反思”三层 |
| 日记 | 当日有依据的事件和感受 | 只能写主智能体知道的事 |

叙述输出进入审核器。审核失败时使用只含正式事实的中性模板，或将该投影标记为未完成；不能绕过审核。界面不得出现 `action`、`tick`、`prompt`、`memory score`、`state`、`flow` 等内部术语。

## 9. 模型调用预算

以下为 B0 建议值，G1 必须根据供应商当前官方价格确认最终货币上限：

| 指标 | 建议值 | 硬上限 |
| --- | --- | --- |
| 每个正常日模型调用 | 4 至 8 次 | 8 次 |
| 单次输入上下文 | 2,500 至 4,000 tokens | 4,000 tokens |
| 单次输出 | 300 至 900 tokens | 1,200 tokens |
| 每日输入 tokens | 8,000 至 16,000 | 24,000 |
| 每日输出 tokens | 1,500 至 4,000 | 6,000 |
| 每日审核调用 | 与可见生成同量 | 12 次 |
| 每日估算成本 | 0.03 至 0.08 元 | 0.10 元 |

计数单位必须记录 provider、model、输入 token、输出 token、审核调用、重试次数、估算价格和价格版本。到达硬上限后停止模型调用，继续运行规则模式；不得为了用完事件预算而扩大调用。

预算限制是安全阀，不是产品目标。B11 将补充正常日、异常日、长对话、连续重试和并发的最坏成本模型。

## 10. 幂等、重试和计费

- `operation_id` 标识一次逻辑推进。
- 相同内容重放返回第一次的业务结果，不重复事件、关系、记忆或计数。
- 同一 HTTP 请求因网络超时进行传输层重试时，必须使用供应商幂等键或响应核对，不能把同一个成功响应当作两次收费。
- 一次真正的新模型尝试有独立 `attempt_id` 和真实计费记录；它是成本，但不是第二次世界结果。
- 模型失败不得自动增加额外事件或关系变化。
- 重试成功后只提交一个事件。
- 重放已提交事件时不能再次强化记忆。

## 11. 并发和恢复

- 同一主智能体同一 tick 串行执行。
- 不同 tick 不能在状态版本冲突时直接覆盖。
- 公共资源变动（地点人数、全天事件数）使用同一事务检查。
- 进程重启后扫描 `RECONCILIATION_REQUIRED`，按事件 ID 和去重键恢复投影。
- 已提交事件的恢复只补缺失投影，不重新调用行动模型。
- 未提交事件恢复可以重试原 tick，但必须核对最终事件是否已经由其他 worker 提交。

## 12. 失败与降级

| 失败 | 处理 | 用户或界面结果 |
| --- | --- | --- |
| 状态版本过期 | 重新读取快照，丢弃本次裁决 | 可安全重试，不生成事件 |
| 操作已提交 | 返回原结果 | 不出现重复内容 |
| 模型超时或格式错误 | 预算内重试一次，然后规则降级 | 仍可推进规则事件 |
| 模型返回非法动作 | 丢弃，选下一个规则候选 | 记录 `invalid_model_action` |
| 记忆读取失败 | 禁止具体记忆陈述 | 使用无记忆模板或延后 |
| 世界事务失败 | 全部回滚 | 无半条事件 |
| 记忆投影失败 | 待核对并幂等重试 | 报告 `incomplete_projection` |
| 审核器不可用 | 阻断输出，不绕过 | 使用安全模板或稍后重试 |
| 审核拒绝 | 丢弃内容 | `content_policy_blocked` |
| 预算超限 | 进入规则模式 | `budget_exceeded` 诊断 |

## 13. 运行记录

每次推进至少记录：

```text
tick_id
operation_id
action_id
event_id（如有）
world_date、slot_key、sequence
state_version_before、state_version_after
run_mode
model_attempt_ids
token_and_cost_counters
memory_recall_ids
memory_write_dedupe_keys
review_result
degradation_reason
latency_ms
```

记录默认脱敏，不保存完整提示词、完整用户原文、密钥、数据库参数或供应商原始响应。

## 14. 验收标准

1. 无真实 API Key 也能用 `rule_only` 模式完成一次合法推进。
2. 模型返回文字或额外字段时不能直接修改世界。
3. 相同 operation 重放不重复生成事件、关系、记忆或加分。
4. 同一角色同一 tick 不能并发提交两次。
5. 模型超时、非法格式、审核失败和预算耗尽都有可测试降级路径。
6. 记忆未召回的事件不能被叙述成明确记忆。
7. 故事中的事实能追溯到正式事件 ID。
8. 真实模型文字变化时，世界状态和决策依赖仍能按同一 seed 验证。
