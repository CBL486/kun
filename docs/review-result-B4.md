# B4 评审结果

评审人：Agent A

评审日期：2026-10-28

结论：**通过，允许进入 B5**

## 1. 审查基线

- B4 实现分支：`codex/bx-b4-state-memory`
- B4 实现提交：`b249fd9`
- 交接回填提交：`251e3b7`
- A 整合分支：`codex/g2-b4-integration`

## 2. 验收证据

```text
B1 unittest：17 项通过
B2 unittest：12 项通过
B3 unittest：21 项通过
B4 unittest：16 项通过
B1+B2+B3+B4 合计：66 项通过
项目 pytest：69 项通过
```

B4 迁移验证：

```text
migrate -> {"schema_version": 1}
version -> {"schema_version": 1}
rollback -> {"schema_version": 0}
version -> {"schema_version": 0}
```

## 3. 已确认通过的能力

- 世界头、世界版本、动作日志和事件日志持久化。
- 单步状态版本校验有效。
- operation 重放不会重复写动作、事件或记忆。
- 世界更新和事件提交在单个 SQLite 事务内回滚。
- 投影失败保留事件和 outbox，并可幂等核对恢复。
- 主智能体六维作用域任一字段不同都不能召回。
- 私密记忆不会进入 NPC 记忆槽。
- active/fuzzy/archived 生命周期边界稳定。
- 锁定记忆不衰减，解锁后恢复衰减。
- 召回有预算限制和分数分解。
- 强化 operation 幂等，归档记忆可被强化重新激活。
- NPC 记忆槽独立存储且最多 8 条。
- 迁移和回滚均可重复执行。

## 4. 接受的有意限制

- B4 只实现 SQLite；PostgreSQL 字段矩阵和隔离实例测试由 B5 完成。
- 世界引擎仍在内存中执行，仓库负责持久化已裁决结果。
- outbox 自动对账调度留给 B8。
- SQLite 单进程行为不代表多实例生产并发能力。
- 未执行服务器、生产数据库、备份或恢复操作。

## 5. 流程问题

B4 实现基于 B3 分支而不是 A 的最新 `main`。A 已将 B4 文件单独 graft 到当前 B3 主线上，没有覆盖 README 安全边界、服务器配置或 B1-B3 集成文件。

B5 开始前必须：

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/bx-b5-postgres-contract
```

## 6. 允许的下一批

允许 B 开始 **B5 PostgreSQL Schema、迁移与契约矩阵**。

B5 继续遵守：

- 不登录服务器；
- 不连接生产 PostgreSQL；
- 只使用本地或隔离测试 PostgreSQL；
- 完成 SQLite/PostgreSQL 字段、时区、JSON、空值、枚举和索引差异测试；
- 提供迁移、回滚和同一业务夹具对比结果；
- 完成后提交独立分支和交接记录，等待 A 评审。
