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
- B6 本地 FastAPI、OpenAPI 和公开投影已完成，B1-B6 共 92 项测试通过。
- B7 最小 RPG Web 已通过 A 验收，B1-B7 共 101 项测试通过。
- B7.5 已通过 A 复审，最终提交 `448a420`；横向大世界、六处室内、Spine 动画和素材清单已通过验收。
- B8 调度、任务幂等、租约恢复和观察者留言持久化已完成本地自测，等待 A 复审。
- B9 LLM 网关复审修复完成：provider 异常边界、重试去重计费和锁竞争行为已通过回归。
- B10 七天 E2E、统一 CI 和穿帮/越权质量门禁已完成本地验证。
- B11 五类成本压力、归因账单、滑动限流和人工确认门禁已完成本地验证。
- B12 发布包、代理/监控模板、Windows 任务、健康检查和回滚配置已完成本地验证。
- B13 SQLite/PostgreSQL 备份恢复、发布证据、版本冻结和总交接已完成本地验证。
- Agent B 当前执行版任务书见 `协作Agent_B_RPG世界详细任务单_V6.md`。
- B6 至 G3 执行计划见 `B6至G3执行计划书_V1.md`。
- A 侧当前工作日志与续接手册见 `docs/agent-a-work-log.md`。
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
pwsh -NoProfile -File scripts/test-b6.ps1
pwsh -NoProfile -File scripts/run-b6-api.ps1
pwsh -NoProfile -File scripts/export-openapi.ps1
```

健康检查：

```text
GET /health
GET /ready
GET /world
GET /agent
GET /timeline
POST /chat
GET /memory
```

公开投影字段见 `docs/openapi-projection.md`，静态契约见 `docs/openapi-v1.json`。B6 只使用本地冻结场景和 mock，不连接生产环境。

## B7 最小 RPG Web

```powershell
pwsh -NoProfile -File scripts/run-b7-web.ps1
```

浏览器打开 `http://127.0.0.1:8080/`。页面包含小镇地图、角色卡、时间线、留言、日记摘要、记忆摘要和设置占位页。

```powershell
pwsh -NoProfile -File scripts/test-b7.ps1
```

UX 与 B7.5 资源接口见 `docs/web-ux-spec.md`。

## B7.5 美术资源

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

正式测试只验证已提交资源、Web、Spine 和截图，不要求私密源素材。需要重建资源时，
先在私有素材环境设置 `B75_SOURCE_ROOT`：

```powershell
$env:B75_SOURCE_ROOT = "D:\private\b75-source-extracted"
pwsh -NoProfile -File scripts/build-b75-assets.ps1
pwsh -NoProfile -File scripts/test-b75.ps1 -Rebuild
```

正式接入资源位于 `assets/`。素材来源、授权状态、哈希与用途见 `assets/manifest.json`；构图和生成说明见 `docs/art-pipeline.md`，授权审计见 `docs/asset-license-audit.md`。

当前 B7.5 使用 2400×900 的横向大世界，镜头随林澄移动；六处地点均可进入
960×540 的内部场景。河面、步道与栈桥直接绘入世界底层；六处室内统一使用
Modern Interiors 的 Room Builder 墙面与地板，并以 AppleDog 免费商用素材
补充宿舍和书院细节。原始压缩包均不入库。

## B8 调度与恢复

```powershell
pwsh -NoProfile -File scripts/test-b8.ps1
pwsh -NoProfile -File scripts/run-b8-api.ps1
pwsh -NoProfile -File scripts/run-b8-scheduler.ps1 -Command status
```

B8 使用持久任务队列、`operation_id` 幂等、worker 租约和 PostgreSQL advisory
lock。任务支持超时、指数退避、死信和崩溃后恢复扫描；观察者留言通过同一 schema
持久化。恢复流程见 `docs/scheduler-recovery-v1.md`。

## B9 LLM 网关

```powershell
pwsh -NoProfile -File scripts/test-b9.ps1
pwsh -NoProfile -File scripts/run-b9-audit.ps1 -BudgetDate "2026-11-01"
```

B9 提供 provider-neutral 调用接口、mock 与真实适配骨架、审核失败关闭、
`operation_id` 业务缓存、`provider_request_id` 计费去重、每日硬预算、熔断和
规则降级。真实 API Key 只从 `AIWORLD_LLM_API_KEY` 读取，不进入仓库、日志或测试输出。
详细契约见 `docs/llm-gateway-v1.md`。

## B10 集成与质量门禁

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
pwsh -NoProfile -File scripts/run-b10-e2e.ps1
```

B10 提供可复现的七日 E2E、统一 Python/JavaScript 测试入口、GitHub Actions CI，
以及 NPC 知识越界、私密字段泄漏、事实冲突、重复台词、导演越权、主智能体直接写
世界、prompt injection、资源缺失和移动布局检查。规范见
`docs/e2e-quality-gates-v1.md`。

## B11 安全与成本压力

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
pwsh -NoProfile -File scripts/run-b11-stress.ps1
```

B11 覆盖正常日、异常日、长对话、连续重试和并发五类成本模型，按日期、事件、角色
和接口聚合账单，并与 mock bill 对账。高风险动作支持人工确认门禁，运行时提供
线程安全滑动窗口限流。失败矩阵见 `docs/security-failure-matrix-v1.md`。

## B12 部署配置

```powershell
pwsh -NoProfile -File scripts/test-b12.ps1
pwsh -NoProfile -File scripts/build-release.ps1 -Output "out/b12/release"
pwsh -NoProfile -File scripts/verify-release.ps1 -Release "out/b12/release"
```

B12 提供 allowlist 发布包、SHA-256 manifest、Nginx/Caddy 模板、Prometheus 指标与
告警、Windows 任务、API/scheduler 健康检查、日志轮转和 release junction 回滚。
A 执行服务器配置的步骤见 `docs/deployment-checklist.md` 和
`docs/rollback-runbook.md`。

## B13 备份与总交接

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
pwsh -NoProfile -File scripts/backup-database.ps1 -Url "sqlite:///./data/local.sqlite3" -Output "backups/local.sqlite3"
pwsh -NoProfile -File scripts/create-release-evidence.ps1
```

B13 提供 SQLite/PostgreSQL 备份恢复、SHA-256 和关键行数校验、备份新鲜度指标、
最终 7 天 E2E 证据、版本冻结清单和生产动作清单。总交接见
`docs/handoff-B13.md`，A 侧动作见 `docs/production-actions-checklist.md`。

## 边界

- 世界状态由世界引擎裁决。
- 模型不能直接修改世界状态。
- NPC 是脚本运行时，不拥有全量大模型。
- 生产服务器只由 Agent A 管理。
