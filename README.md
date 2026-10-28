# AI World

一个单主智能体、脚本 NPC 和导演事件构成的小镇 RPG。

## 当前状态

- 产品方向已确定为“一个小镇一个主智能体”。
- 服务器 Python 运行时、PostgreSQL、独立账号、开机任务与每日备份已完成。
- PostgreSQL 备份恢复演练已通过。
- 最小 FastAPI 服务已部署，`/health` 与 `/ready` 已在服务器验证。
- B0 契约已完成 G1 冻结，下一步进入 B1 单镇模拟器。
- 详细计划见 `RPG智能体世界项目双人任务书_V4.md`。
- Agent B 当前执行版任务书见 `协作Agent_B_RPG世界详细任务单_V5.md`。
- B0 契约索引见 `docs/rpg-b0-index.md`。
- G1 评审结果见 `docs/review-result-B0.md`。

## 本地运行

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
