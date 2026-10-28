# SQLite / PostgreSQL 契约矩阵

状态：B5 本地验证完成，等待 A 验收

日期：2026-10-28

## 1. 通用约定

- 业务标识使用字符串，不使用数据库自增主键。
- 时间字段在 Python 中转换为 UTC 后绑定。
- SQLite 返回的无时区 `DATETIME` 由 `UTCDateTime` 补为 UTC。
- PostgreSQL 使用 `TIMESTAMP WITH TIME ZONE`。
- JSON 对象与数组必须双后端可逆。
- 枚举值使用字符串列加 `CHECK` 约束，避免 PostgreSQL 原生 enum 迁移锁定。
- 逻辑删除使用状态和归档，不执行业务数据物理删除。
- 业务摘要比较忽略数据库内部连接和物理存储差异。

## 2. 表和字段

| 表 | SQLite | PostgreSQL | 空值 | 唯一性 / 索引 |
| --- | --- | --- | --- | --- |
| `schema_versions` | INTEGER 主键 | INTEGER 主键 | 否 | 版本唯一 |
| `world_heads` | JSON 文本 | JSONB | 否 | `world_id` 主键 |
| `world_versions` | JSON 文本 | JSONB | `event_id` 可空 | `(world_id, state_version)` |
| `actions` | JSON 文本 | JSONB | `event_id` 可空 | `operation_id`、`action_id` 唯一 |
| `events` | JSON 文本 | JSONB | 否 | `event_id`、`action_id` 唯一；日期序号唯一 |
| `memory_projection_outbox` | JSON 文本 | JSONB | `last_error` 可空 | `(event_id, candidate_index)` 唯一 |
| `memories` | JSON 文本 | JSONB | `conversation_id`、`last_accessed_at` 可空 | `(scope_hash, dedupe_key)` 唯一 |
| `memory_mutations` | REAL / JSON | FLOAT / JSONB | 否 | `operation_id` 主键 |
| `npc_memory_slots` | JSON 文本 | JSONB | 来源和过期时间可空 | `(npc_id, slot_id)` 主键 |

## 3. 核心映射

| 逻辑类型 | Python | SQLite | PostgreSQL | 差异处理 |
| --- | --- | --- | --- | --- |
| 标识 | `str` | `TEXT/VARCHAR` | `VARCHAR` | 不依赖大小写排序 |
| 整数 | `int` | `INTEGER` | `INTEGER` | 无 |
| 权重/金额比例 | `float` | `REAL` | `DOUBLE PRECISION` | 边界使用显式 CHECK |
| 布尔 | `bool` | `INTEGER 0/1` | `BOOLEAN` | SQLAlchemy Boolean 适配 |
| UTC 时间 | `datetime` aware | `DATETIME` 文本 | `TIMESTAMPTZ` | `UTCDateTime` 统一为 UTC |
| JSON | `dict/list` | `JSON` 文本 | `JSONB` | 业务投影反序列化后比较 |
| 状态枚举 | `str` | `TEXT + CHECK` | `VARCHAR + CHECK` | 不创建原生 enum |
| 可空作用域 | `None` | `NULL` | `NULL` | `conversation_key` 保存 `__null__` 供唯一约束 |

## 4. 时间

输入中的北京时间例如：

```text
2026-11-02T08:00:00+08:00
```

数据库绑定为 UTC：

```text
2026-11-02T00:00:00Z
```

SQLite 与 PostgreSQL 都经过 `UTCDateTime`；两者业务导出均使用 `Z` 结尾的 UTC ISO-8601。

## 5. 索引

| 索引 | 列 |
| --- | --- |
| `idx_memories_scope_state` | `scope_hash, state` |
| `idx_memories_source_event` | `source_event_id` |
| `idx_outbox_status` | `status` |
| `idx_events_world_time` | `world_id, world_date, sequence` |
| `idx_actions_world_time` | `world_id, committed_at` |

## 6. 检查约束

- 世界版本 `state_version >= 0`；
- 记忆状态只能为 `active`、`fuzzy`、`archived`；
- 投影状态只能为 `pending`、`projected`、`failed`；
- importance 和 strength 在 `[0,1]`；
- NPC memory 重要标记只能为布尔值。

## 7. 同夹具对比

测试使用同一个 B2 动作、B1 事件和记忆候选分别提交到 SQLite 与 PostgreSQL，比较：

- 最终世界 JSON；
- 动作日志；
- 事件日志；
- 投影 outbox；
- 记忆记录；
- 整体业务摘要哈希。

当前结果：业务摘要完全一致。

```text
SQLite   = 7dd8a4b34eb72b64c2766165ca7e589238f0fc4b6516886522f8cfb162a81f74
Postgres = 7dd8a4b34eb72b64c2766165ca7e589238f0fc4b6516886522f8cfb162a81f74
```

## 8. 运行限制

- SQLite 仅用于本地单进程验证；
- PostgreSQL 实连使用 `pgserver` 启动的临时隔离实例；
- 不连接生产库，不读取生产账号；
- 当前 schema 版本为 1，未来字段变化必须新增编号迁移和对应回滚脚本。
