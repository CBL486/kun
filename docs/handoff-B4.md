# B4 世界状态、记忆与 SQLite 交接

状态：本地实现完成，等待 A 验收

批次：B4

日期：2026-10-28

分支：`codex/bx-b4-state-memory`

## 1. 实现范围

B4 提供：

- 世界当前头和版本化世界快照；
- 动作日志和正式事件日志；
- 单步世界版本校验；
- 操作幂等和事件事务；
- 待投影记忆 outbox；
- 主智能体六维作用域记忆；
- 事件记忆幂等投影；
- 召回、衰减、锁定、模糊、归档和强化；
- 可解释召回分数；
- NPC 有限记忆槽持久化；
- SQLite schema、迁移、回滚和本地 CLI；
- 投影失败后的幂等核对恢复。

B4 不连接服务器、生产 SQLite/PostgreSQL、真实模型或真实用户数据。

## 2. 代码结构

```text
memory_core/
  core.py       记忆写入、召回、衰减、锁定、强化和投影
  models.py     Scope、MemoryRecord、RecallResult
  errors.py     类型化错误
rpg_storage/
  migrations.py 迁移管理
  repository.py 世界/动作/事件/outbox/NPC 槽仓库
  migrations/
    001_apply.sql
    001_rollback.sql
tests/
  test_b4_persistence.py
scripts/
  migrate-b4.ps1
  test-b4.ps1
```

## 3. 事务和一致性

世界更新和事件提交优先在单个 SQLite 事务内完成：

```text
action log
  + formal event
  + world version
  + world head
  + memory projection outbox
```

任一 SQL 约束失败会整体回滚，调用方收到 `event_conflict` 或 `backend_unavailable`，不会得到成功确认。

记忆投影使用 outbox 降级路径：

1. 事件事务先提交 outbox；
2. 投影在独立事务写入记忆并标记 `projected`；
3. 投影失败时事件保留，返回 `reconciliation_required`；
4. `reconcile()` 只补缺失投影，不重建事件。

## 4. 作用域

每条主智能体记忆精确匹配：

```text
tenant_id
world_id
user_id
character_id
surface
conversation_id
```

不允许通配或隐式回退。当天事件使用 `day-YYYY-MM-DD`，日记等跨日记忆使用 `conversation_id=null`。

NPC 记忆槽存放在独立表，不进入主智能体召回，也不能跨 NPC 查询。

## 5. 生命周期

```text
strength >= 0.3           active
0.1 <= strength < 0.3     fuzzy
strength < 0.1            archived
```

- 默认召回 active 和 fuzzy，不召回 archived；
- 锁定记忆不衰减，保持 active；
- 解锁后从解锁时间重新计算衰减；
- 强化 operation 幂等，单次最多 `0.2`；
- 强化可将 archived 重新激活；
- 分享和强化不重复加分。

当前衰减半衰期为 14 天，配置常量位于 `memory_core/core.py`。

## 6. 召回

召回分数严格按 ADR：

```text
relevance * 0.40
+ strength * 0.20
+ importance * 0.15
+ emotional_weight * 0.10
+ recency * 0.10
+ access_bonus * 0.05
```

每次召回限制 `max_items` 和 `max_tokens`，返回分数分解、状态和命中原因。召回更新访问时间与次数，不静默修改 importance。

## 7. 迁移和回滚

```powershell
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command migrate
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command version
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command rollback -TargetVersion 0
```

迁移可重复执行。回滚脚本只作用于显式传入的本地数据库。

## 8. 测试

统一命令：

```powershell
pwsh -NoProfile -File scripts/test-b4.ps1
```

当前结果：

```text
B1 17 项通过
B2 12 项通过
B3 21 项通过
B4 16 项通过
合计 66 项通过
```

B4 覆盖：

- schema 连续迁移和回滚；
- 世界、动作和事件日志持久化；
- 单步状态版本校验；
- operation 重放不重复事件或记忆；
- SQL 约束失败整体回滚；
- 投影失败保留事件和 outbox；
- 幂等核对恢复记忆；
- 六维作用域任一不同均不能召回；
- 私密记忆不进入 NPC 槽；
- active/fuzzy/archived 边界；
- 锁定不衰减、解锁后恢复衰减；
- 召回预算和分数分解；
- 强化 operation 幂等和内容冲突；
- 归档记忆强化后重新激活；
- NPC 记忆槽最多 8 条。

## 9. 已知限制

- B4 只实现 SQLite；PostgreSQL 字段矩阵和隔离实例测试属于 B5。
- 世界引擎目前仍在内存中执行，仓库负责持久化已裁决结果。
- outbox 核对目前由本地调用或后续调度器触发，自动任务属于 B8。
- SQLite 单进程适合 B4 验收，不声称适合多实例生产并发。
- 未执行服务器、生产数据库、备份或恢复操作。

## 10. 交接字段

```text
任务 ID：B4 世界状态、记忆与 SQLite
分支：codex/bx-b4-state-memory
提交哈希：待提交后回填
改动文件：memory_core/、rpg_storage/、tests/test_b4_persistence.py、scripts/migrate-b4.ps1、scripts/test-b4.ps1、README.md、docs/handoff-B4.md
实现摘要：SQLite 世界/动作/事件事务、六维记忆核心、召回生命周期、NPC 槽和投影核对。
测试命令：pwsh -NoProfile -File scripts/test-b4.ps1
测试结果：B1 17、B2 12、B3 21、B4 16，共 66 项通过
seed / mock：20261028；rule_only；本地 SQLite；无真实供应商
已知风险：PostgreSQL 差异、自动对账调度和多实例并发留给 B5/B8。
需要 A 合并的文件：本分支 B4 文件和交接记录
需要 A 在服务器执行的动作：无
```
