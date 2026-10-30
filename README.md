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
- B7.5 美术修复版已完成自测：横向大世界、Spine 镜头跟随移动、六地点内部手账、五角色头像和 UI 图标已接入 Web。
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

## 边界

- 世界状态由世界引擎裁决。
- 模型不能直接修改世界状态。
- NPC 是脚本运行时，不拥有全量大模型。
- 生产服务器只由 Agent A 管理。
