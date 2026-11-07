# R5 连续记忆、关系、情绪与 Schema 5

状态：待 Gate 2 审查

日期：2026-11-07

## 1. QQ 参考模式

已读取 `docs/qq-memory-reference-v1.md`。采用：

- 事件优先、摘要作为索引；
- 重要性、情绪权重、时间衰减和访问次数参与召回；
- 关系采用多维度小幅变化；
- `SelfState` 拆分到 `PersonaState` 和 `EmotionState`；
- 私有心流只影响内部状态，不直接展示；
- 低频自主活动、媒体观察受频率和审核限制。

拒绝：

- QQ 消息分条、表情、语音、NapCat 或协议端代码；
- QQ/AI School 共用记忆租户；
- 长期系统提示词原文；
- 真实 QQ 用户数据、Key 或数据库；
- 自动点赞、评论、关注、私信或投币。

## 2. Schema 5

新增：

```text
memory_events
relationship_states
emotion_states
persona_baselines
persona_states
persona_change_log
study_sessions
media_observations
setup_state
deepseek_credentials
world_clock_states
```

关系、情绪和记忆事件必须引用正式事件。`deepseek_credentials` 只保存
`key_ref` 和掩码，不保存完整 Key。

## 3. Persona JSON 迁移

```powershell
python -m rpg_orm import-persona-json `
  --url <database-url> `
  --path <persona.json> `
  --world-id world_qinghe_v1 `
  --character-id char_lin_cheng
```

导入保持当前 baseline revision、active baseline、PersonaState、change log 和
`baseline_persona_id`/revision 一致性。重复导入幂等；旧 JSON 不删除，验证通过后
由 A 决定归档。

## 4. 事件、关系和情绪

- `memory_events` 使用 `(world_id, dedupe_key)` 唯一；
- valence 为 `[-1,1]`，intensity/importance/confidence 为 `[0,1]`；
- 关系包含 affection/trust/familiarity/warmth/tension；
- 同一 `last_event_id` 重放不会重复增长；
- 情绪包含 valence/arousal/energy/stress/curiosity 和 decay_rate；
- 状态变化不得绕开正式事件依据。

## 5. 连续世界时钟

- `Asia/Shanghai` 现实时间 1:1；
- 默认 10 分钟 tick；
- 24 小时内按最多 144 个压缩 tick 追赶；
- 超过 24 小时记录离线摘要并直接跳到当前时间；
- tick 不调用 LLM；
- 文件时钟使用原子写入，数据库预留 `world_clock_states`；
- Windows 任务 `AIWorld-WorldTick` 每 10 分钟运行。

## 6. 部署边界

生产数据目录固定在 release 外部：

```text
C:\AIWorld\data\setup
C:\AIWorld\data\persona
C:\AIWorld\data\world
```

`/setup`、`/api/setup/*`、`/api/persona/*` 只能由本机或管理员网段访问，
禁止公开缓存，普通观察者返回 403。

## 7. 安全和沉浸

默认 Persona 只保留玩家可读的角色边界。现实身份、不可声称现实身体/联系方式、
高风险安全打断等系统策略移动到 `app/persona_policy.py`，R6 接入提示词时不得把
这些文本变成正常台词。

## 8. 验证

```text
SQLite schema 5 migration：通过
PostgreSQL schema 5 migration：通过
Persona JSON 导入和重复导入：通过
关系/情绪未引用事件被拒绝：通过
旧 JSON Key 不进入数据库明文字段：通过
持久世界时钟和有界追赶：通过
release 不含 data/logs/backups：通过
```
