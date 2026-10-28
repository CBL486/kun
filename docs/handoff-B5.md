# B5 PostgreSQL Schema、迁移与契约矩阵交接

状态：本地实现完成，等待 A 验收

批次：B5

日期：2026-10-28

分支：`codex/bx-b5-postgres-contract`

## 1. 实现范围

B5 提供：

- SQLAlchemy 2 声明式模型；
- SQLite 与 PostgreSQL 通用仓库；
- JSON/JSONB 映射；
- UTC `DATETIME` / `TIMESTAMPTZ` 映射；
- 字符串 CHECK 枚举；
- 空值、唯一约束和索引；
- 幂等迁移和显式回滚；
- SQLite 本地集成测试；
- 通过 `pgserver` 启动的临时 PostgreSQL 集成测试；
- 同一世界/事件/记忆夹具双后端对比；
- 投影失败核对的双后端验证；
- PostgreSQL 契约矩阵；
- A 的生产迁移与回滚清单。

B5 未连接任何生产数据库或生产账号。

## 2. 代码结构

```text
rpg_orm/
  models.py       SQLAlchemy 表模型
  types.py        UTC 时间类型
  migrations.py   迁移和回滚
  repository.py   跨 SQLite/PostgreSQL 仓库
  __main__.py     migrate/rollback/version CLI
requirements-b5.txt
requirements-b5-dev.txt
tests/
  test_b5_postgres_contract.py
scripts/
  migrate-b5.ps1
  test-b5.ps1
docs/
  postgres-contract-matrix.md
  postgres-migration-runbook.md
```

## 3. 双后端结论

同一 B2 动作、B1 事件和记忆候选在 SQLite 与临时 PostgreSQL 上产生：

- 相同最终世界 JSON；
- 相同动作/事件日志；
- 相同 outbox 状态；
- 相同记忆字段和去重键；
- 相同业务摘要哈希。

本次实连结果：

```text
SQLite   = 7dd8a4b34eb72b64c2766165ca7e589238f0fc4b6516886522f8cfb162a81f74
Postgres = 7dd8a4b34eb72b64c2766165ca7e589238f0fc4b6516886522f8cfb162a81f74
```

实连 PostgreSQL 使用本机临时数据目录，退出后删除，不是生产或共享测试实例。

## 4. 迁移

B5 schema 版本为 1。迁移可重复调用，回滚会删除 B5 表。

本地 SQLite：

```powershell
pwsh -NoProfile -File scripts/migrate-b5.ps1 -Url "sqlite:///out/b5/world.db" -Command migrate
pwsh -NoProfile -File scripts/migrate-b5.ps1 -Url "sqlite:///out/b5/world.db" -Command version
```

生产 PostgreSQL 只由 A 按 [postgres-migration-runbook.md](postgres-migration-runbook.md) 执行。

## 5. 测试

安装开发依赖：

```powershell
python -m pip install -r requirements-b5-dev.txt
```

统一测试：

```powershell
pwsh -NoProfile -File scripts/test-b5.ps1
```

当前结果：

```text
B1 17 项通过
B2 12 项通过
B3 21 项通过
B4 16 项通过
B5 9 项通过
合计 75 项通过
```

B5 新增覆盖：

- SQLite 迁移重复执行与回滚；
- PostgreSQL 迁移重复执行与回滚；
- JSONB 与 timestamp with timezone；
- 可空 conversation_id；
- 索引和 CHECK 约束；
- 双后端表名一致；
- 同夹具业务摘要一致；
- PostgreSQL operation 重放；
- PostgreSQL 投影失败和核对恢复。

## 6. 已知限制

- 当前只有 schema 版本 1，后续变更必须增加编号迁移；
- `drop_all` 回滚适合当前首版和隔离测试，生产回滚须由 A 结合备份执行；
- PostgreSQL 实连测试使用临时 `pgserver`，不等同于生产参数、权限和网络验证；
- B5 不包含 API、调度器或生产部署；
- 未执行生产数据库、备份或恢复。

## 7. 交接字段

```text
任务 ID：B5 PostgreSQL Schema、迁移与契约矩阵
分支：codex/bx-b5-postgres-contract
提交哈希：9983e0f
改动文件：rpg_orm/、tests/test_b5_postgres_contract.py、scripts/test-b5.ps1、scripts/migrate-b5.ps1、requirements-b5*.txt、docs/postgres-contract-matrix.md、docs/postgres-migration-runbook.md、README.md、docs/handoff-B5.md
实现摘要：SQLAlchemy 双后端模型、迁移回滚、同夹具对比和 A 执行清单。
测试命令：pwsh -NoProfile -File scripts/test-b5.ps1
测试结果：B1 17、B2 12、B3 21、B4 16、B5 9，共 75 项通过
seed / mock：20261028；SQLite；临时 PostgreSQL；无生产密钥
已知风险：生产 PostgreSQL 权限、网络、备份和锁等待需 A 在维护窗口验证。
需要 A 合并的文件：本分支 B5 文件和交接记录
需要 A 在服务器执行的动作：审批后按迁移清单执行生产迁移；B 不执行
```
