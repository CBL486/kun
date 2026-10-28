# AI World

一个单主智能体、脚本 NPC 和导演事件构成的小镇 RPG。

## 当前状态

- 产品方向已确定为“一个小镇一个主智能体”。
- 服务器 Python 运行时、PostgreSQL、独立账号、开机任务与每日备份已完成。
- PostgreSQL 备份恢复演练已通过。
- 最小 FastAPI 服务已部署，`/health` 与 `/ready` 已在服务器验证。
- B0 契约已完成 G1 冻结。
- B1 确定性七日模拟已完成，17 项测试通过，两次运行业务哈希一致。
- B2 主智能体核心已完成，29 项 B1+B2 测试通过。
- 详细计划见 `RPG智能体世界项目双人任务书_V4.md`。
- Agent B 当前执行版任务书见 `协作Agent_B_RPG世界详细任务单_V6.md`。
- B0 契约索引见 `docs/rpg-b0-index.md`。
- G1 评审结果见 `docs/review-result-B0.md`。

## B1 模拟

```powershell
pwsh -NoProfile -File scripts/test-b1.ps1
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1
```

B1 输出完整报告、前后快照、重放清单、检查点和终端摘要；暂停与恢复说明见 `docs/handoff-B1.md`。

## B2 主智能体演示

```powershell
pwsh -NoProfile -File scripts/test-b2.ps1
pwsh -NoProfile -File scripts/run-b2-demo.ps1
```

B2 演示输出最小感知包、候选决策轨迹、双层意图和世界引擎提交结果。详见 `docs/handoff-B2.md`。

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
