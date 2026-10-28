# AI World

一个单主智能体、脚本 NPC 和导演事件构成的小镇 RPG。

## 当前状态

- 产品方向已确定为“一个小镇一个主智能体”。
- B0 契约已完成 G1 冻结。
- B1 确定性七日模拟已完成，17 项测试通过。
- B2 主智能体核心已完成，29 项 B1+B2 测试通过。
- B3 NPC 脚本运行时已完成，50 项 B1+B2+B3 测试通过。
- B4 SQLite 世界状态与记忆持久化已完成，66 项 B1-B4 测试通过。
- B5 SQLite/PostgreSQL 契约与迁移已完成，75 项 B1-B5 测试通过。
- Agent B 当前执行版任务书见 `协作Agent_B_RPG世界详细任务单_V6.md`。
- B0 契约索引见 `docs/rpg-b0-index.md`。
- G1 评审结果见 `docs/review-result-B0.md`。

## 快速验证

```powershell
pwsh -NoProfile -File scripts/test-b5.ps1
```

## B1 模拟

```powershell
pwsh -NoProfile -File scripts/test-b1.ps1
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1
```

## B2 主智能体演示

```powershell
pwsh -NoProfile -File scripts/test-b2.ps1
pwsh -NoProfile -File scripts/run-b2-demo.ps1
```

## B3 NPC 运行时

```powershell
pwsh -NoProfile -File scripts/test-b3.ps1
pwsh -NoProfile -File scripts/run-b3-demo.ps1
```

## B4 SQLite 持久化

```powershell
pwsh -NoProfile -File scripts/test-b4.ps1
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command migrate
pwsh -NoProfile -File scripts/migrate-b4.ps1 -Database out/b4/world.db -Command version
```

## B5 SQLite/PostgreSQL 契约

```powershell
python -m pip install --target .b5-deps -r requirements-b5-dev.txt
pwsh -NoProfile -File scripts/test-b5.ps1
pwsh -NoProfile -File scripts/migrate-b5.ps1 -Url "sqlite:///out/b5/world.db" -Command migrate
```

B5 契约矩阵见 `docs/postgres-contract-matrix.md`，生产迁移清单见 `docs/postgres-migration-runbook.md`。B5 使用本地或隔离 PostgreSQL，不连接生产数据库。

## 本地 API

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

健康检查：

```text
GET /health
GET /ready
```

## 边界

- 世界状态由世界引擎裁决。
- 模型不能直接修改世界状态。
- NPC 是脚本运行时，不拥有全量大模型。
- 生产服务器只由 Agent A 管理。
