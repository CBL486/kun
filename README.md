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
- B8 调度、任务幂等、租约恢复和观察者留言持久化已通过 A 复审，提交 `de451a4`。
- B9 LLM 网关、审核与成本核心已通过 A 复审，最终提交 `338cbaa`。
- B10 七天 E2E、统一 CI 和穿帮/越权质量门禁已通过 A 复审，最终提交 `5fd7249`。
- B11 五类成本压力、失败矩阵、归因账单和滑动限流已通过 A 复审，最终提交 `c8e89c1`。
- B12 发布包、代理/监控模板、健康检查和回滚配置已通过 A 复审，最终提交 `3643d83`。
- B13 SQLite/PostgreSQL 备份恢复、发布证据、版本冻结和总交接已通过 A 复审，最终提交 `219ce66`。
- A 侧隔离 staging 已通过：179 项测试、SQLite、PostgreSQL、备份恢复、API 烟测
  和 junction 回滚演练；产品重构当前 schema 已升级为 5。
- DeepSeek `deepseek-flash` live smoke 已通过：112/81 tokens，成本 0.00094176 CNY，审核通过；生产环境文件已准备但服务未重启。
- R9 最终集成已接入生产 DeepSeek runtime；完整回归为 262 项测试通过，七日 E2E、
  成本对账、config-check 和 release verify 均通过。
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
```

启动配置：

```text
GET  /api/setup/status
POST /api/setup/deepseek/validate
POST /api/setup/deepseek/save
POST /api/setup/complete
POST /api/setup/deepseek/clear
GET  /api/persona/status
GET  /api/persona
POST /api/persona/default
PUT  /api/persona/baseline
```

首次进入时 `/` 返回启动设置页。Key 只写入服务端私有目录，浏览器不保存完整 Key。
默认或自定义 PersonaBaseline 保存在服务端独立目录，人物基础 revision 更新不会
重置世界、关系、记忆或位置。详细契约见 `docs/setup-deepseek-v1.md` 和
`docs/persona-v1.md`。

公开投影字段见 `docs/openapi-projection.md`，静态契约见 `docs/openapi-v2.json`。
R1 使用 `rpg-public-world-v2` 的只读 `agent_presence`，公开 API 不提供位置写入。

## B7 最小 RPG Web

```powershell
pwsh -NoProfile -File scripts/run-b7-web.ps1
```

浏览器打开 `http://127.0.0.1:8080/`。页面包含小镇地图、角色卡、时间线和观察留言。
玩家只能观察服务端 presence，不能使用键盘、按钮或点击地图移动角色。日记、记忆和
学习笔记不属于公开 UI/API。

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

## R2 原创蓝鲸少女

- 主视觉 1024×1024，表情差分 4 张；
- 地图角色为 64×96 四方向精灵表；
- idle 4 帧、walk 6 帧、turn 4 帧、stop 3 帧、study 4 帧；
- presence 的 `facing`、`moving`、`animation` 决定播放状态；
- 资源清单见 `assets/characters/whale-girl/whale-girl-manifest.json`；
- 设计与版权边界见 `docs/character-design-r2-v1.md`。

## R6 自我认知与人设演化

- 正式事件驱动 PersonaState 小幅变化；
- Baseline 保持不可被模型覆盖；
- 单次变化上限、6 小时冷却和 change log；
- 系统安全策略独立于角色设定；
- `/chat` 公开语义为“审核后送达”，即时返回世界内角色回应；
- 正常回应加载 PersonaBaseline、PersonaState、关系、情绪和有限近期记忆；
- 模型审核、预算或 provider 失败时使用世界内安全 fallback，不插入系统式免责声明。

## R7 学校与自主行动

- 每天 09:00 后触发一次学校学习；
- 角色先走到教学楼，再持续 30 分钟现实时间 `study` 状态；
- 每会话最多一次学习反思，默认 1200 token 预算；
- 学习笔记和 ReflectionEvent 只保存在私有侧；
- 后台 `AIWorld-WorldTick` 接管时钟和学校状态推进；
- R2 资源新增四方向 study 精灵动画。

## R8 受控媒体观察

- 只处理 B站/抖音公开视频链接；
- URL 跳转后再次校验平台和白名单；
- 默认每天 2 个视频、最多 600 token；
- 只保存公开元数据摘要和私有低强度事件，不保存完整视频；
- 媒体内容不绕过会员/地区/DRM 限制，不自动点赞/评论/关注/私信。

## R9 最终集成

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
python scripts/run_r9_chat_smoke.py --output docs/r9-chat-smoke.json
python scripts/run_r9_schema_evidence.py
python scripts/run_r9_public_media_smoke.py
```

R9 统一聊天“已送达 + 即时回应”语义，并让 `/chat` 通过既有 `LlmGateway` 使用
生产 DeepSeek runtime、输出审核、每日预算、成本归集、重试和熔断。聊天不创建世界
事件、关系变化或记忆；模型失败只返回安全规则文本。桌面和手机证据见
`docs/screenshots/r9-chat-delivered-desktop.png` 与
`docs/screenshots/r9-chat-delivered-mobile.png`。

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
