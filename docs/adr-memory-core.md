# ADR：单镇 RPG 主智能体记忆核心

状态：G1 已冻结（2026-10-28）

日期：2026-10-28

适用版本：`rpg-world-ontology-v1` 与 `rpg-agent-loop-v1`

## 1. 决策

单镇 MVP 使用一个按完整作用域隔离的记忆核心，只服务主智能体。脚本 NPC 使用世界状态内最多 8 个有限记忆槽，不使用全量记忆库，也不调用 LLM。

本 ADR 取代仓库中旧版“QQ companion 与 AI School 共用”的描述作为当前实现依据。Git 历史仍保留旧文档，但旧描述不再是本项目的 G1 冻结契约。

## 2. 当前作用域语义

每条主智能体记忆必须携带以下六个维度：

```text
tenant_id
world_id
user_id
character_id
surface
conversation_id
```

当前单镇 MVP 的固定含义：

| 字段 | 当前语义 | 规则 |
| --- | --- | --- |
| `tenant_id` | 产品世界租户，固定为 `rpg-world` | 不得使用 QQ 或旧学校租户 |
| `world_id` | 当前小镇实例，例如 `world_qinghe_v1` | 不得跨镇召回 |
| `user_id` | 世界外观察者账户 | 测试只使用合成 ID |
| `character_id` | 记忆所属的主智能体，例如 `char_lin_cheng` | 一个镇只有一个主智能体记忆所有者 |
| `surface` | 当前固定为 `school`，表示现有 `memory_core` 可用的世界界面通道 | 必须与 `world_id` 同时出现；后续重命名需要迁移 |
| `conversation_id` | 当天事件或对话为 `day-YYYY-MM-DD`；跨日召回为 `null` | 禁止通配和隐式回退 |

`surface="school"` 是现有存储实现的兼容值，不表示产品是学校养成，也不恢复旧 QQ/AI School 共租户设计。G1 如果要求改成 `world`，必须先定义枚举迁移，不能直接混用。

## 3. 所有权

- 主智能体通过记忆核心读写 `event`、`reflection`、`summary` 和必要的 `relationship` 记忆。
- 观察者留言只有在世界引擎提交并完成作用域投影后才进入主智能体记忆。
- 脚本 NPC 的 `memory_slots` 属于世界状态，不是记忆核心记录。
- NPC 槽不得通过主智能体查询接口读取，也不得混入主智能体召回结果。
- 导演、审核器和界面不能直接写记忆核心。

## 4. 记忆类型

MVP 至少支持：

| 类型 | 来源示例 | 用途 |
| --- | --- | --- |
| `event` | 正式学校/小镇事件 | 保留经历事实 |
| `reflection` | 主智能体复盘或日记 | 保留经过审核的个人理解 |
| `summary` | 放学分享 | 保留压缩后的一日经历 |
| `relationship` | 有事件依据的互动 | 保留关系变化线索 |
| `preference` | 用户明确表达且审核通过的偏好 | 不替代世界状态 |

所有内容必须可追溯到明确来源。没有来源的记忆写入失败。

## 5. 记忆字段

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
  "content": "林澄在公告栏看到截稿日期提前。",
  "importance": 0.66,
  "emotional_weight": 0.42,
  "confidence": 0.98,
  "strength": 0.73,
  "scene_tags": ["library", "deadline"],
  "created_at": "2026-11-04T10:24:00+08:00",
  "last_accessed_at": null,
  "last_strength_update": "2026-11-04T10:24:00+08:00",
  "access_count": 0,
  "restated_count": 0,
  "locked": false,
  "state": "active",
  "source_event_id": "evt_7a4f05ce8b8093d1",
  "dedupe_key": "rpg:evt_7a4f05ce8b8093d1:char_lin_cheng:0",
  "metadata": {
    "visibility": "user_visible"
  }
}
```

所有数值权重在 `[0,1]`。内部时间使用 UTC；示例展示为北京时间。

## 6. 身份和幂等

- `memory_id` 为不可复用 UUID 或确定性映射 ID。
- `(scope, dedupe_key)` 唯一。
- 事件投影使用：

```text
rpg:{event_id}:{character_id}:{candidate_index}
```

- 同一去重键重放返回原记录。
- 相同去重键但语义内容不同返回 `ConflictError`。
- 强化操作使用独立 `operation_id`，不依赖时间戳猜测。
- 重试不得重复写入记忆或重复增加强度。

## 7. 生命周期

| 强度 | 状态 | 默认召回 |
| --- | --- | --- |
| `strength >= 0.3` | `active` | 是 |
| `0.1 <= strength < 0.3` | `fuzzy` | 是，排序降低 |
| `strength < 0.1` | `archived` | 否 |

- 锁定记忆不衰减，并保持 `active`。
- 解锁后从解锁时刻恢复正常衰减。
- 归档不删除数据。
- 强化可以把归档记录重新激活。
- 衰减依据 `last_strength_update` 的经过时间计算，不能每次任务重复扣同一段时间。
- 初值、半衰期和下限由 B4 配置，G1 只冻结语义。

## 8. 强化

允许理由：

```text
share
restatement
scene_trigger
flow
manual
```

- 强化必须引用来源事件或明确的手动操作。
- 主模型不能直接输出强度变化。
- `flow` 加成只由世界引擎配置添加。
- 单次加成有上限，总分不超过 `1.0`。
- 分享成功后只强化确实进入分享的 3 至 5 个事件。
- 日记和分享分开保存。

## 9. 召回

默认分数：

```text
score =
  relevance * 0.40
  + strength * 0.20
  + importance * 0.15
  + emotional_weight * 0.10
  + recency * 0.10
  + access_bonus * 0.05
```

规则：

- 六个作用域维度必须全部匹配。
- 跨日查询显式使用 `conversation_id=null`。
- 每次召回有 `max_items` 和 `max_tokens`。
- 默认排除 `archived`。
- 结果包含分数分解、状态和命中原因，供本地诊断。
- 公开界面只能显示故事化摘要，不显示分数、权重或 SQL。
- 召回是读取，不静默增加 importance。

## 10. 与世界事件的一致性

首选同一事务提交：

```text
state changes
  + formal event
  + memory candidates
  + memory projection
```

无法单事务时：

1. 事件事务内写入一条待投影记录；
2. 使用稳定去重键幂等投影；
3. 完成前返回 `RECONCILIATION_REQUIRED` 或 `projection_failed`；
4. 恢复任务只能补缺失投影，不能重建或重复事件；
5. 不允许事件已提交而记忆静默丢失。

## 11. SQLite 与 PostgreSQL

- SQLite 用于本地单进程测试。
- PostgreSQL 用于 B8 隔离测试和 A 的生产集成。
- 两者必须实现同一字段、作用域、去重和业务语义。
- JSON 数组和 metadata JSON 使用各后端等价表示。
- 时间统一为 UTC `timestamptz` 或等价的 UTC ISO-8601。
- 枚举、空值、索引和回滚差异由 B8 契约矩阵验证。
- B0 不连接生产数据库。

## 12. 错误语义

至少保留以下类型：

```text
ScopeError
ValidationError
NotFoundError
ConflictError
BackendUnavailable
```

对外 API 使用稳定错误码。错误响应不得包含原始用户内容、SQL 参数、凭据、模型提示或文件路径。

## 13. 隐私和内容边界

- `tenant_id`、`world_id` 和 `character_id` 三重匹配防止跨镇、跨角色泄漏。
- 用户必须是 18 岁以上成年人，测试只使用合成数据。
- 不允许涉及未成年角色的性内容。
- NPC 不得读取主智能体私密日记或思考记忆。
- 日志只记录记忆 ID、作用域哈希和诊断码，不记录完整私密内容。
- 记忆删除由 A 的生产策略决定；B0 只定义归档、锁定和恢复语义。

## 14. B4 验收

1. 六个作用域维度任一不同都不能召回。
2. 主智能体私密日记不能进入 NPC 槽或其他角色召回。
3. 同一事件重放不重复写记忆或强化。
4. `active`、`fuzzy`、`archived` 边界在 `0.3`、`0.1` 稳定。
5. 锁定记忆不衰减，解锁后从解锁时刻恢复。
6. 召回预算得到遵守，解释字段可复算。
7. 事件已提交而投影失败可以幂等恢复。
8. SQLite 与 PostgreSQL 对同一业务夹具产生一致结果。

## 15. 未决事项

- G1 是否保留兼容值 `surface="school"`，还是迁移为 `surface="world"`。
- B4 的初始强度、半衰期、模糊和归档阈值最终参数。
- SQLite 与 PostgreSQL 的首选事务与降级细节。
- A 负责的 PostgreSQL 隔离实例和生产价格不影响本 ADR 的概念语义，但会决定 B8/B11 的实施参数。
