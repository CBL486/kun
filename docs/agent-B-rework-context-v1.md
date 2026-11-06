# Agent B 产品重构上下文审计 V1

状态：Gate 0 已通过；2026-11-06 补充可复现证据

日期：2026-11-06

任务：B-R0 上下文同步与基线审计

执行边界：只读代码、运行基线测试、写本审计文档并推送独立分支。未修改业务代码，未重做
B0，未访问生产服务器、生产环境文件、API Key、数据库密码或真实用户数据。

## 1. 基线与工作树

执行前已恢复 GitHub 通道并完成 `git fetch origin --prune`。

```text
任务书：docs/agent-B-product-rework-taskbook-v1.md
任务书编写基线：d0bff85
实际 origin/main：46df3780f06b1131f26ba43dfab91889adf8d909
实际基线提交说明：docs: add Agent B product rework taskbook
审计分支：codex/product-r0-context
分支创建点：46df3780f06b1131f26ba43dfab91889adf8d909
执行前工作树：clean
远端 main：未修改
```

复现命令：

```powershell
git fetch origin --prune
git rev-parse origin/main
git status --short --branch
git diff --name-status origin/main...HEAD
git diff --check
```

任务书中的编写时基线 `d0bff85` 已过期；本轮的权威基线是重新 fetch 后取得的
`46df378`。

R0 审查时实际证据：

```text
git rev-parse origin/main
46df3780f06b1131f26ba43dfab91889adf8d909

git diff --name-status origin/main...6b670b937ea7f4bd4506b66a2701dde50bb91094
A docs/agent-B-rework-context-v1.md

git diff --check
无输出

工作树
仅 docs/agent-B-rework-context-v1.md

origin/main
B 未直接修改；A 随后以 848a73ac8efb80c92500b7e7a5d1b004a6aedf65
合并 R0 与 Gate 0 决策
```

## 2. 必读材料与阅读结果

已读取并核对：

```text
README.md
docs/agent-B-product-rework-taskbook-v1.md
docs/agent-a-work-log.md
docs/handoff-B13.md
docs/review-result-B13.md
docs/g3-observation-start-2026-11-06.json
docs/deployment-checklist.md
docs/rollback-runbook.md
docs/adr-memory-core.md
docs/agent-loop-v1.md
docs/openapi-projection.md
docs/rpg-b0-index.md
docs/review-result-B7-5.md
web/index.html
web/app.js
web/styles.css
web/spine-player.js
app/main.py
app/api_models.py
app/local_state.py
app/settings.py
rpg_agent/loop.py
rpg_agent/planner.py
rpg_agent/models.py
rpg_agent/perception.py
memory_core/core.py
memory_core/models.py
memory_core/errors.py
rpg_scheduler/models.py
rpg_scheduler/messages.py
rpg_scheduler/errors.py
rpg_scheduler/locks.py
rpg_scheduler/repository.py
rpg_scheduler/service.py
rpg_scheduler/worker.py
rpg_orm/models.py
rpg_orm/types.py
rpg_orm/repository.py
rpg_orm/migrations.py
tests/ 全量文件索引及主要测试用例
scripts/test-all.ps1
scripts/test-b13.ps1
```

任务书要求阅读的 QQ 参考实现：

```text
bot_core/memory.py
bot_core/self_model.py
bot_core/thought_flow.py
bot_core/autonomy.py
bot_core/video.py
bot_core/persona.py
personas/
README.md
tests/test_memory.py
```

当前执行环境未找到 QQ 项目。A 已在 Gate 0 提供仓库内参考摘要
`docs/qq-memory-reference-v1.md`，并确认后续以该摘要为可用参考，不再把“无法
访问 QQ 源码”作为 R5/R6/R8 的阻塞理由。

已在 Gate 0 后读取该摘要。R5 开始前将另写设计记录，明确采用 QQ 项目的记忆分层、
关系小幅变化、`SelfState`、私有心流和低频自主活动思路，拒绝 QQ 协议端、消息分条、
表情/语音能力、提示词原文和真实用户数据。若后续执行环境可访问 QQ 源码，再按 A
给出的固定项目路径核对实现细节。

## 3. 当前主线已有内容

`origin/main` 已包含 B0～B13、A 的生产修复、DeepSeek runtime、Windows 启动加固、
监控和 G3 证据。B 不应重新创建旧 B0，也不应把 `codex/b0-contracts` 当主线。

| 范围 | 当前实现 |
| --- | --- |
| B0 | G1 冻结的世界本体、主循环、NPC、导演、动作、场景和记忆 ADR |
| B1 | 固定 seed 的七日规则模拟、快照、暂停恢复和报告 |
| B2 | 候选、决策轨迹、`IntentProposal`、`ActionIntent` 与世界引擎校验 |
| B3 | 四名脚本 NPC、有限记忆槽、知识边界和反应去重 |
| B4 | SQLite/PostgreSQL 世界、事件、动作、记忆与幂等投影 |
| B5 | schema 契约、迁移和回滚，当前 `LATEST_SCHEMA_VERSION = 4` |
| B6 | FastAPI、公开投影、OpenAPI 和冻结的 v1 响应模型 |
| B7/B7.5 | 观察者 Web、六地点、室内图、Spine、桌面/手机布局和资源清单 |
| B8 | 持久任务队列、operation 幂等、租约、退避、死信和留言持久化 |
| B9 | LLM 网关、审核、预算、熔断、规则降级、usage 去重和 DeepSeek 适配 |
| B10 | 七日 E2E、穿帮/越权/隐私门禁、Python 与 JavaScript 统一 CI |
| B11 | 成本压力、失败矩阵、账单归因和限流 |
| B12 | allowlist 发布包、代理/监控模板、Windows 任务、健康检查和回滚 |
| B13 | SQLite/PostgreSQL 备份恢复、发布证据、版本冻结和总交接 |

A 侧生产证据显示：

```text
生产版本：0.1.0-g2-rc7
G3 观察开始：2026-11-06T09:48:10Z
AIWorld-API：SYSTEM / Running
AIWorld-Scheduler：SYSTEM / Running
AIWorld-Monitor：SYSTEM / Ready
AIWorld-Backup：SYSTEM / Ready
AIWorld-LogRotation：SYSTEM / Ready
legacy AIWorldAPI：Disabled
schema：4
```

这些只是 A 提供的生产证据。B 未连接、未修改、未验收生产。

## 4. 当前实现边界

### 4.1 Web 与角色观察

`web/index.html` 仍有四个 `[data-move]` 方向按钮、WASD 提示和可聚焦地图。
`web/app.js` 仍包含：

```text
MOVE_KEYS
canMoveMap()
keydown / keyup 移动监听
pointerdown / pointerup 移动按钮监听
mapState.active
每帧直接修改 mapState.x / mapState.y
按键盘状态切换 walk / idle
```

因此玩家目前可以直接移动角色，违反新产品“只能观察和对话”的要求。

地图资源只有主智能体 `assets/characters/lin_cheng.*` 和
`assets/spine/lin_cheng.*` 的行走资产；另有过场用的五名角色头像。Spine runtime
已经实际接入 `web/spine-player.js`，当前支持 `idle`、`walk` 和左右翻转，
没有上下方向、坐下、学习或对话动作。

### 4.2 公开 API 与世界推进

`WorldResponse` 仍是 `rpg-public-world-v1`。`WorldInfo` 只有
`current_location_id` 和 `current_location_name`，没有连续坐标、朝向、动画、
移动速度、presence revision 或更新时间和 `state_revision`。

`LocalWorldStore.reset()` 会新建 `SevenDaySimulator` 并一次运行完七日场景，
随后 API 只读取模拟结束后的固定快照。它不是持续运行的自主生活循环，也没有
实时 presence 事件流。

`POST /chat` 只执行审核、把留言写入待处理队列并返回 mock 确认，不直接生成角色
动作、世界事件、关系变化或记忆。

当前公开端点：

```text
GET  /health
GET  /ready
GET  /world
GET  /agent
GET  /timeline
GET  /memory
POST /chat
```

不存在 `/api/setup/*`、Persona、学习任务或媒体观察接口。

### 4.3 主智能体

`rpg_agent` 已有完整的 `IntentProposal`、`ActionIntent`、候选过滤、规则规划、
决策轨迹、状态过期恢复和世界引擎提交路径。模型或规则只能提出意图，不能直接改
世界状态。

但 `LocalWorldStore` 没有使用 `AgentLoop`；`SevenDaySimulator` 按冻结的每日路线
自行构造 intent。`AgentLoop` 目前主要用于命令演示和单元测试，没有接管 API
的持续行为、presence 或聊天响应。

### 4.4 记忆、关系与情绪

`memory_core` 已具备：

```text
六维 scope
dedupe_key 与 conflict
importance / emotional_weight / confidence / strength
active / fuzzy / archived 生命周期
半衰期衰减、锁定和强化幂等
按 relevance、strength、importance、情绪、时效和访问次数召回
max_items / max_tokens 预算
```

当前没有独立的玩家关系表、情绪状态表、PersonaBaseline、PersonaState、
亲密度变更日志、学习会话表或媒体观察表。七日世界状态里存在 NPC 关系数值和
关系变化日志，但它们不是新产品要求的观察者关系系统。

公开 `/memory` 仍返回安全记忆摘要和 `diary_summaries`；桌面与手机导航也都有
“日记”和“记忆”。这与任务书“内部资料默认不向玩家展示”直接冲突。

### 4.5 调度与持久化

`rpg_scheduler` 已提供持久任务、operation 幂等、优先级、租约、超时、退避、
死信、过期恢复、积压指标、PostgreSQL advisory lock 和 SQLite 回退。

`rpg_orm` 当前 schema 为 4，已有世界头/版本、动作、事件、记忆投影、
主智能体记忆、NPC 记忆槽、调度任务、观察者留言、LLM operation/usage 和成本
归因表。尚无 presence、Persona、玩家关系、情绪、学校或媒体相关表。

调度器能承载未来的后台任务，但没有证据表明它已经驱动持续世界推进、每日学校、
角色自主活动或聊天回应。

### 4.6 启动、Key 与人设

首页直接加载 `/world`、`/agent`、`/timeline` 和 `/memory`。没有欢迎页、Key
输入、问号教程、Key 校验、清除流程或 Persona 配置。

仓库已有服务端 DeepSeek runtime，默认模型为 `deepseek-flash`，生产 Key 由 A
管理的服务器私有环境提供。它不是面向世界所有者的启动配置流程，且 B 不读取或
修改真实 Key。

## 5. 与任务书的逐项差异

| 任务 | 当前状态 | R0 结论 |
| --- | --- | --- |
| R1 上帝视角与权威 presence | Web 仍允许直接移动；API 无 presence/revision | 需新增服务端 presence，并删除所有客户端位置写入 |
| R2 角色动画与原创蓝鲸视觉 | 只有林澄的静态地图图和 Spine `idle/walk`、左右翻转 | 现有动画不能表达坐下、学习、对话和四方向 |
| R3 启动页与 DeepSeek Key | 无启动页、无 `/api/setup/*`、无用户 Key 流程 | 需新建安全的服务端配置状态 |
| R4 默认/自定义 Persona | 无 PersonaBaseline/PersonaState 或持久化接口 | 需先冻结字段和替换人设语义 |
| R5 事件、好感度、连续记忆、情绪 | `memory_core` 可复用；无玩家关系/情绪 schema | 需在现有记忆核心上扩展，不能恢复旧 QQ/学校共租户 |
| R6 自我认知与人设演化 | 无自我叙事、习惯、价值观权重或变化日志 | 依赖 R4/R5，不能由 LLM 直接改写 baseline |
| R7 每日学校与隐藏学习 | 七日剧情含课堂/学习动作，但没有每日 30 分钟会话与持久预算 | 需定义虚拟时间、任务幂等和成本上限 |
| R8 受控媒体观察 | 无媒体接口、审核后记忆或频率控制 | 依据 `docs/qq-memory-reference-v1.md` 的边界设计，不复制 QQ 业务代码 |
| R9 集成与证据 | 现有 183 项基线与发布门禁通过 | Gate 0 通过后才能设计新 E2E，不能把旧门禁当新验收 |

## 6. 已知风险与契约冲突

1. `rpg-public-world-v1`、`rpg-public-memory-v1` 和 checked-in OpenAPI 已被 B6/B10
   测试冻结。新增 presence、移除日记/记忆页面或修改字段都需要明确升级版本并
   同步更新测试，不能静默漂移。
2. 当前 API 每次重启会重放相同的七日模拟结果。它没有“当前世界时钟”，所以
   停机补课、聊天回应和 presence 恢复都缺少权威语义。
3. 当前 `surface="school"` 是项目已冻结的兼容值，不代表恢复旧 QQ/学校记忆租户。
   R5 若改为 `world` 必须提供枚举迁移和兼容策略。
4. B7/B7.5 的“玩家可移动、只有 idle/walk、日记/记忆公开”限制已由 Gate 0 明确
   作废。后续以玩家只读观察、公开 API 不含日记/记忆、presence 权威移动和正式
   动画为验收依据。
5. `memory_core` 的锁定和强化属于记忆强度语义，不可直接当作好感度或情绪值使用。
6. SQLite 与 PostgreSQL 双后端必须同时迁移、回滚并验证；新增 schema 不能只做
   SQLite 本地实现。
7. 当前使用 A 提交的 QQ 参考摘要；R5 前必须记录采用和拒绝的具体模式，R6/R8
   仍需在各自设计文档中沿用同一边界。
8. 当前系统消息仍可能把“队列确认”呈现成角色回复，R1/R5 集成时需要明确区分
   observer 留言、世界事件与角色实际回应。

## 7. 需要 A 在 Gate 0 决策的问题

1. 是否确认把七日固定快照替换为持续运行的权威世界循环？现实时间、虚拟时间倍率、
   暂停、停机恢复和补推进规则需要冻结。
2. 是否批准公开 API 升级为 `rpg-public-world-v2`，以新增 presence 和
   `state_revision`，并允许更新 B6/B10 的 v1 冻结测试？
3. `/memory`、日记和记忆导航是完全移除，还是保留仅本地管理员可见的诊断接口？
   若保留，鉴权、路由和发布包 allowlist 必须明确。
4. 主角是否继续使用“林澄”和 `char_lin_cheng`，还是迁移为原创“蓝鲸少女”品牌名？
   若是后者，角色 ID 是否保持兼容？
5. 自定义 Persona 允许修改哪些字段？“替换人设”是否保留世界、关系、记忆和位置，
   还是由玩家明确选择开始新世界？
6. DeepSeek Key 的私有保存路径、单世界归属、校验频率、清除行为和多实例冲突规则
   由哪一层执行？启动页如何在未配置 TLS 的本地模式中准确提示风险？
7. R5 是否把 schema 5 冻结为事件、玩家关系、情绪、Persona baseline/state 和变化
   日志的统一迁移版本？需确认字段、索引、回滚和旧数据策略。
8. “每日学校 30 分钟”是虚拟分钟还是现实分钟？停机期间是补课、顺延还是跳过？
   每日模型调用和 token 上限是否沿用 B9/B11 的预算？
9. R8 是否只接受用户明确提供的公开链接，还是允许读取 B 站公开热门列表？QQ 项目
   的仓库地址或固定提交、审核规则、缓存期限和真实网络测试边界也需提供。
10. 角色世界内主观体验与系统安全边界的可执行话术规范是什么？尤其需要冻结
    “被问是否 AI”“被要求无条件服从/改人设”和极端安全场景的处理方式。

以上问题已由 A 在 `docs/review-result-R0-product-rework.md` 的 D1～D10 决策冻结；
本节保留为 R0 历史记录。

## 8. 基线测试结果

有效命令：

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
```

实际结果：

```text
pytest：183 passed, 1 warning, 36.14s
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true，cost_cny=0.36320000，blocked=38
config-check：issues=[]
临时发布包：version=0.1.0，files=189
发布包 SHA-256：921f5ed46b94d08edda510846d3b7a32738c94319630b2e2a0d87aade410dc7e
release verify：issues=[]
```

唯一警告是 `.b6-deps` 中 Starlette/httpx TestClient 的上游弃用警告，不影响当前
测试通过。

环境备注：

```text
Python：.venv\Scripts\python.exe，3.15.1
Node：v22.18.0
PowerShell：pwsh 7.6.5
```

用 `powershell.exe` 5.1 执行统一脚本会在解析无 BOM 的 UTF-8 中文
`scripts/resolve-b1-python.ps1` 时失败。应使用 `pwsh`，或另行修复脚本编码兼容性；
本轮不修改该业务外脚本。

测试完成后工作树仍只有本审计文档的预期改动；`out/` 产物为忽略文件。

## 9. Gate 0 停止点

本分支只完成 B-R0。A 审查并确认以下事项后，才可开始 R1/R3：

- 接受实际基线 `46df378` 和独立分支 `codex/product-r0-context`；
- 确认 B 没有重做 B0、没有修改生产；
- 回答或接受第 7 节的契约决策；
- 使用 `docs/qq-memory-reference-v1.md` 作为 QQ 设计参考；
- 旧 B6/B7 验收限制已作废，不再作为新需求的阻断理由。

本轮未实现 presence、启动页、Persona、新记忆 schema、学校、媒体观察或发布候选，
也未开始 R1。
