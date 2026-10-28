# 青禾镇 RPG 世界 MVP

当前完成 B1 确定性七日规则模拟、B2 主智能体核心、B3 NPC 脚本运行时、B4 SQLite 世界/记忆存储和 B5 双数据库契约。代码不连接服务器、真实模型或生产数据。

## 运行

在仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1
```

如果已经安装 Python，也可以直接运行：

```powershell
python -m rpg_sim seven-day --scenario slice-seven-day-v1 --seed 20261028 --mode rule_only --frozen-clock --output out/b1
```

输出包括：

- `run.json`：完整结构化报告和必需证据字段；
- `snapshot-before.json`、`snapshot-after.json`：初始与最终世界快照；
- `replay-manifest.json`：业务快照与重放哈希；
- `checkpoint.json`：可在重启后继续的原子检查点；
- `summary.md`：终端摘要副本。

暂停与继续：

```powershell
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1-checkpoint -PauseAfter 12
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1-checkpoint -Resume
```

首次验证暂停链路时，从新的输出目录开始执行第一条；恢复完成后，`business_result` 应与不中断运行一致。

## 测试

```powershell
pwsh -NoProfile -File scripts/test-b1.ps1
```

B1 契约说明见 [docs/handoff-B1.md](docs/handoff-B1.md)。

## B2 主智能体

运行单步演示：

```powershell
pwsh -NoProfile -File scripts/run-b2-demo.ps1
```

运行 B1 与 B2 的全部测试：

```powershell
pwsh -NoProfile -File scripts/test-b2.ps1
```

B2 提供最小感知包、确定性候选、可解释决策轨迹、模型意图和世界 ActionIntent 双层结构、状态过期恢复以及幂等重放。B2 契约说明见 [docs/handoff-B2.md](docs/handoff-B2.md)。

## B3 NPC 运行时

查看四名 NPC 的七日切片日程：

```powershell
pwsh -NoProfile -File scripts/run-b3-demo.ps1 -Date 2026-11-04
```

运行 B1 至 B3 的全部测试：

```powershell
pwsh -NoProfile -File scripts/test-b3.ps1
```

B3 提供四名 NPC 的离线日程状态机、知识隔离、审核台词模板、事件反应、48 小时重复控制、最多 8 个有限记忆槽、课程包和事件包。B3 契约说明见 [docs/handoff-B3.md](docs/handoff-B3.md)。

## B4 SQLite 世界与记忆

创建或升级本地数据库：

```powershell
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command migrate
```

查看与回滚 schema：

```powershell
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command version
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command rollback -TargetVersion 0
```

运行 B1 至 B4 的全部测试：

```powershell
pwsh -NoProfile -File scripts/test-b4.ps1
```

B4 提供世界版本、动作/事件日志、SQLite 迁移与回滚、六维记忆作用域、召回、衰减、锁定、模糊、归档、强化、NPC 有限记忆和投影失败核对。B4 契约说明见 [docs/handoff-B4.md](docs/handoff-B4.md)。

## B5 SQLite/PostgreSQL 契约

安装 B5 本地依赖：

```powershell
python -m pip install -r requirements-b5-dev.txt
```

运行 B1 至 B5 全量测试，包括隔离 PostgreSQL：

```powershell
pwsh -NoProfile -File scripts/test-b5.ps1
```

查询、迁移或回滚显式指定的本地测试数据库：

```powershell
pwsh -NoProfile -File scripts/migrate-b5.ps1 -Url "sqlite:///out/b5/world.db" -Command migrate
pwsh -NoProfile -File scripts/migrate-b5.ps1 -Url "sqlite:///out/b5/world.db" -Command version
```

B5 提供 SQLAlchemy 模型、SQLite/PostgreSQL JSON/时区/空值/索引/约束映射、同夹具业务摘要对比、迁移回滚、契约矩阵和生产执行清单。详见 [postgres-contract-matrix.md](docs/postgres-contract-matrix.md) 与 [postgres-migration-runbook.md](docs/postgres-migration-runbook.md)。
