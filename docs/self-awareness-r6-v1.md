# R6 自我认知与人设演化 V1

状态：已通过 R6/Gate 3，R9 完成真实 runtime 接入

日期：2026-11-07

## 1. 设计边界

R6 复用 R5 的现有表：

```text
memory_events
relationship_states
emotion_states
persona_baselines
persona_states
persona_change_log
```

不新增独立记忆模型。

## 2. 事件驱动演化

`SelfAwarenessService.evolve_from_event()`：

- 必须读取同一世界的正式 `memory_events`；
- 不能由模型直接提交 Persona 字段；
- 单次 value 变化上限为 0.02，重大事件上限为 0.05；
- 同一维度 6 小时内有变化时降为 20% 增量；
- 同一事件重复处理幂等；
- 所有变化写入 `persona_change_log` 并引用 `source_event_id`；
- `PersonaBaseline` 保持不变；
- 同时更新 schema 5 EmotionState 的 curiosity/stress。

## 3. 自我叙事

重要事件会把经过清洗的事件摘要加入 `PersonaState.self_narrative`，最多保留
1200 字。叙事只引用正式事件，不生成新事实。私密叙事不进入公开 API。

## 4. 系统安全与角色表达

`app/persona_policy.py` 是系统层安全策略。它：

- 不进入玩家可见的 PersonaBaseline；
- 不作为正常对话台词；
- 与角色 profile 一起生成内部 `persona_reply` 提示模板；
- 明确要求模型不得输出策略原文、数据库字段或内部数值。

正常回复：

- 使用世界内第一人称；
- 可以表达兴趣、偏好和主观感受；
- 不插入系统式免责声明。

高风险输入：

- 使用简短、自然的世界内拒绝；
- 建议联系现实中的可信任人员或紧急服务；
- 不提供危险操作步骤。

被问是否为 AI：

- 保持林澄的世界内身份；
- 不切换成客服或系统播报；
- 不声称现实身体、现实地址或现实行动能力。

## 5. 对话接入

已配置数据库 Persona 时，`/chat` 在完成留言审核后以 `delivered` 状态返回角色
世界内回应。正常对话由生产 `LlmGateway` 生成，并加载 PersonaBaseline、
PersonaState、当前关系、当前情绪和最多五条近期正式事件摘要；provider、审核或
预算失败时改用世界内规则 fallback。该回应不直接创建世界事件、关系变化或记忆，
正式事件仍由后续世界行动路径产生。

模板：

```text
rpg_llm.prompts.PROMPT_TEMPLATES["persona_reply"]
```

## 6. 验证

```text
pytest：238 passed, 1 warning
正式事件驱动演化：通过
Baseline 不变：通过
change log/source_event_id：通过
重复事件幂等：通过
重复事件冷却：通过
高风险/身份/控制请求分类：通过
普通与身份回复不含 AI 客服腔：通过
桌面/手机聊天布局：通过
```
