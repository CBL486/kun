# Agent B 产品重构任务书 V1

状态：待执行  
编写人：Agent A  
编写日期：2026-11-06  
执行人：Agent B（Previous Partner B）  
审查人：Agent A  
基线仓库：`origin/main`，编写时提交 `d0bff85`；B 执行前必须重新 fetch，并在交接中记录实际基线提交。  
生产现状：`0.1.0-g2-rc7` 已在生产运行；B 不接触生产服务器、VNC、RDP、SSH、云控制台、生产 `.env`、API Key、数据库密码或真实用户数据。

## 1. 任务书目的

本任务书用于指导 Agent B 在本地仓库完成下一轮产品重构。重构目标不是继续堆功能，而是把当前“可演示的七日模拟器”改造成一个真正由主智能体自主生活、玩家只以上帝视角观察和对话的产品原型。

B 负责本地代码、测试、文档和可审查的 Git 提交。A 负责 GitHub 审查、合并、构建、部署和生产验收；B 不得自行改生产。

## 2. 先读这一段：B 的上下文状态

### 2.1 B 最后一次会话的真实情况

B 的最后一次 Codex 子会话开始于 2026-10-28 14:56（北京时间），父会话是 A 的产品长会话。B 当时已经：

- 阅读 `协作Agent_B_RPG世界详细任务单_V5.md`
- 阅读 `RPG智能体世界项目双人任务书_V4.md`
- 阅读 `docs/adr-001-single-agent-town.md`
- 阅读 `docs/adr-002-mvp-runtime.md`
- 明确了世界状态唯一权威、主智能体只提出意图、导演只给候选事件、NPC 不得全知、成本计数、18+ 和 IP 边界。
- 创建或准备创建 `codex/b0-contracts` 分支。
- 开始写 `docs/rpg-world-ontology-v1.md`、`docs/agent-loop-v1.md`、`docs/npc-script-runtime-v1.md` 等 B0 契约文档。

B 最后在写 `docs/npc-script-runtime-v1.md` 时被中断，**没有完成最终提交，也没有 push**。这些文档后来已经由 A 在仓库中继续完成和扩展。

### 2.2 因此 B 不应该做的事

- 不要把 `codex/b0-contracts` 的旧状态当成当前主线。
- 不要重新创建或覆盖已经存在的 B0 文档。
- 不要从旧任务书推断当前代码没有 B1～B13。
- 不要基于旧版前端或旧版 API 直接改。
- 不要自行把任务拆成新的服务器部署任务。
- 不要修改 `main`，不要 push 到远程主分支。
- 不要访问或修改生产环境。

### 2.3 B 已经知道的内容

- 产品是“一个小镇一个主智能体，其余居民为脚本 NPC”。
- 主智能体只能提出意图，世界引擎负责校验和落账。
- 导演系统只提供候选事件，不替主智能体选择。
- NPC 不能全知、不能编造事实、不能越权访问主智能体私密记忆。
- 用户只能观察和留言，不能直接控制角色。
- 项目需要成本控制、内容审核、可回滚和证据记录。
- B 的边界是本地代码、测试和交接文档。

### 2.4 B 目前不知道、必须补课的内容

- 当前 `origin/main` 已经包含 B1～B13 的实现、A 的生产修复、DeepSeek runtime、Windows 启动加固、监控和 G3 证据。
- 当前生产版本是 `0.1.0-g2-rc7`，但 B 不应该接触生产。
- 当前 Web 仍保留键盘/按钮直接移动角色的代码，这正是本轮要移除的。
- 当前角色的地图表现是小型静态/简易绘制资源，未完成正式移动动画。
- 用户的新产品方向：上帝视角、智能体自主行动、隐藏日记和记忆、开始页 DeepSeek Key、人格设定、事件+好感度、连续记忆、虚拟世界自我认知、每日学校学习和受控媒体观察。
- `QQ` 项目中已经有一套更完整的记忆、关系、自我状态、心流、自主活动和公开视频读取实现，需要作为设计参考，不是直接复制。
- 用户不希望角色在正常体验中被系统式免责声明打断；角色可以在世界内表达类人的主观体验，但系统层仍需保留安全边界。

### 2.5 必读清单

B 在写任何代码前必须阅读：

- `README.md`
- `docs/agent-a-work-log.md`
- `docs/handoff-B13.md`
- `docs/review-result-B13.md`
- `docs/g3-observation-start-2026-11-06.json`
- `docs/deployment-checklist.md`
- `docs/rollback-runbook.md`
- `web/index.html`
- `web/app.js`
- `web/styles.css`
- `web/spine-player.js`
- `app/main.py`
- `app/api_models.py`
- `app/local_state.py`
- `rpg_agent/loop.py`
- `rpg_agent/planner.py`
- `rpg_agent/models.py`
- `memory_core/core.py`
- `memory_core/models.py`
- `rpg_scheduler/`
- `rpg_orm/`
- `tests/`
- QQ 项目的 `bot_core/memory.py`、`bot_core/self_model.py`、`bot_core/thought_flow.py`、`bot_core/autonomy.py`、`bot_core/video.py`、`bot_core/persona.py`
- QQ 项目的 `personas/`、`README.md` 和 `tests/test_memory.py`

B 必须在 `docs/agent-B-rework-context-v1.md` 里写清楚：实际基线提交、读过的文件、发现的现状、和本任务书的差异。

## 3. 产品目标与非目标

### 3.1 产品目标

1. 玩家永远不能直接移动角色；角色由服务器端主智能体自主行动。
2. 玩家看到的是实时/近实时的上帝视角，可观察、可对话，不可操控。
3. 角色有连续的自我叙事、关系、情绪、记忆和人格演化。
4. 日记、记忆、课程笔记等内部资料默认不向玩家展示。
5. 首次进入有启动页：DeepSeek API Key、教程小问号、角色人设配置。
6. 默认人设和玩家自定义人设都能随时间发生变化，但变化必须有事件依据。
7. 角色知道自己生活在持续运行的虚拟世界，不随意打破沉浸感。
8. 角色每天有约 30 分钟的隐藏学习时间，学习内容影响长期行为，但玩家不看到学习后台。
9. 角色可按受控规则观察公开抖音/B站内容，不自动互动、不绕过登录或权限。

### 3.2 非目标

- 不把角色做成玩家操纵的 RPG 角色。
- 不把完整私密记忆、日记、课程笔记或系统提示词暴露给玩家。
- 不在这一轮实现真实外部审核供应商。
- 不让 B 负责公网域名、TLS、DNS、Cloudflare Tunnel 或生产部署。
- 不复制抖音视频中的真实人物、Cosplayer 或具体版权角色；只提取抽象视觉特征并做原创角色设计。
- 不在单元测试中调用真实 DeepSeek、抖音或 B站。

## 4. 协作规则

### 4.1 分支和提交

每个工作包使用独立分支，从最新 `origin/main` 创建：

- `codex/product-r0-context`
- `codex/product-r1-observer`
- `codex/product-r2-character-art`
- `codex/product-r3-setup-key`
- `codex/product-r4-persona`
- `codex/product-r5-memory-affection`
- `codex/product-r6-self-awareness`
- `codex/product-r7-school`
- `codex/product-r8-media`
- `codex/product-r9-integration`

B 可以合并相邻小任务，但不能把全部改动塞进一个超大提交。建议每个任务 1～3 个提交，提交信息使用：

```text
feat(product-r1): make agent presence authoritative
fix(product-r1): smooth camera interpolation
test(product-r1): cover observer-only movement
docs(product-r1): record acceptance evidence
```

不要 push `main`。完成后 push 各自分支，并在 GitHub 提供：

- 任务编号
- 分支
- 提交哈希
- 改动文件
- 测试命令与结果
- 截图/录屏/性能证据
- 已知风险
- 需要 A 合并或执行的动作

### 4.2 测试边界

- 所有单元测试使用 mock provider、mock reviewer、临时数据库。
- 不读取真实 API Key。
- 不调用真实抖音/B站网络。
- 外部内容使用 fixture 或录制的公开元数据。
- 测试必须覆盖浏览器不可用、网络失败、审核失败、记忆损坏和重启恢复。
- 新增数据库结构必须提供迁移和回滚说明。

### 4.3 安全和隐私

- API Key 只在服务端保存；不进入前端 `localStorage`、URL、日志、截图和 Git。
- 所有前端动态文本继续使用 `textContent`。
- 私密记忆、课程笔记、系统提示词、内部关系数值不得出现在公开 API。
- 不记录完整 prompt、完整用户原文、真实密钥或生产数据库内容。
- 角色可以有世界内主观体验，但不得诱导用户将其当作现实真人、现实治疗师或现实依赖对象。
- 正常角色对话不使用系统式免责声明打断体验；系统层仍保留安全拒绝和风险边界。

## 5. 执行波次

```text
Wave 0  R0 上下文同步与基线审计
Wave 1  R1 上帝视角与智能体移动
         R2 角色动画与镜头表现
         R3 启动页、DeepSeek Key、教程
         R4 人设配置与默认人设
Wave 2  R5 事件+好感度+连续记忆+情绪
         R6 自我认知与人设演化
         R7 每日学校与隐藏学习
         R8 抖音/B站受控观察
Wave 3  R9 集成回归、证据和发布候选
```

依赖关系：

- R1、R3 可以并行，但都要等 R0 完成。
- R2 可以先做资产契约；接入依赖 R1 的 presence 字段。
- R4 依赖 R3 的启动流程。
- R5 的 schema 必须先冻结，R6、R7、R8 才能并行写记忆事件。
- R9 最后执行，不得跳过。
## 6. 详细任务卡

### B-R0：上下文同步与基线审计

**优先级：P0，所有任务前置**

**目标**

B 不直接开始改代码。先把“旧 B0 知识”和“当前主线现实”对齐，避免基于过时代码或旧任务书做重复工作。

**交付物**

- `docs/agent-B-rework-context-v1.md`
- 记录实际 `origin/main` 提交、分支、工作树状态。
- 记录当前 B0～B13 已存在内容，不重复创建。
- 记录当前 Web/API/Agent/Memory/Scheduler 的实现边界。
- 记录当前已知缺口与本任务书的对应关系。
- 列出 B 认为需要 A 确认的设计问题，最多 10 条。

**必须确认的现状**

1. 当前 `web/app.js` 是否仍有键盘/按钮直接移动逻辑。
2. 当前 `/world` 是否只返回 `current_location_id`，没有连续坐标、朝向、动画和 revision。
3. 当前 `LocalWorldStore` 是否是七日日模拟快照，而不是实时自主行为循环。
4. 当前 `memory_core` 是否有 lifecycle、strength、scope、dedupe、private/public 隔离。
5. 当前 `rpg_agent` 是否已有 intent/action 模型，是否可以直接驱动 presence。
6. 当前地图角色资源是否只有 `assets/characters/lin_cheng.*` 和 `assets/spine/lin_cheng.*`，以及 Spine 动画是否真正接入。
7. 当前日记和记忆是否通过导航和 `/memory` 暴露。
8. 当前启动流程是否直接进入主页面，没有 Key/Persona 配置。
9. 当前任务/启动脚本是否由 A 管理，B 不修改生产任务。
10. 当前 `main` 是否包含 `AIWorld-Monitor`、monitor/G3 证据和 SYSTEM 任务修复。

**验收**

- 工作树干净。
- 文档中的基线提交可 `git rev-parse` 复现。
- 不修改业务代码。
- A 确认 B 已理解“不要重做 B0、不要碰生产”。

---

### B-R1：上帝视角、智能体权威移动、镜头平滑

**优先级：P0**

**目标**

删除玩家直接控制角色的所有路径；角色的位置、朝向、移动状态由服务器端主智能体行动驱动；前端只做只读投影、插值和镜头跟随。

**当前已知问题**

- `web/index.html` 有方向键/WASD 提示、`[data-move]` 按钮、可聚焦地图。
- `web/app.js` 有 `MOVE_KEYS`、`mapState.active`、直接修改 `mapState.x/y`、`requestAnimationFrame` 玩家移动。
- `LocalWorldStore.world()` 当前只返回位置 ID，没有连续 presence。
- 现有 `assets/spine/lin_cheng.json` 有 `idle`/`walk` 动画，但前端地图玩家主要以 canvas/fallback 呈现。

**必须实现的协议**

新增公开 presence，不直接暴露内部 tick、prompt、action score：

```json
{
  "schema_version": "rpg-public-world-v2",
  "world": {
    "current_date": "2026-11-07",
    "current_time": "08:10",
    "state_revision": 184
  },
  "agent_presence": {
    "character_id": "char_lin_cheng",
    "x": 612.5,
    "y": 338.0,
    "location_id": "loc_classroom",
    "facing": "right",
    "animation": "walk",
    "speed": 72.0,
    "moving": true,
    "updated_at": "2026-11-07T08:10:12+08:00",
    "revision": 184
  }
}
```

- `animation` 至少支持 `idle`、`walk`、`enter_place`、`sit`、`study`、`talk`；如当前运行时没有全部动作，先实现 `idle/walk/enter_place`。
- `x/y` 使用地图世界坐标，必须由服务器状态决定。
- 前端禁止向服务器发送位置写入请求。
- 前端只按 revision 更新目标位置；旧 revision 不允许覆盖新 revision。
- 如果没有 presence，前端显示角色不可见/连接中，不伪造随机移动。

**前端改动**

- 删除 `MOVE_KEYS`、`keydown/keyup` 移动监听、`[data-move]` 按钮和 `canMoveMap()`。
- 删除会把玩家输入写入 `mapState.active` 的逻辑。
- 保留地图平移/缩放作为“镜头”，但只能由可观察的 presence 或用户拖动镜头触发；镜头拖动不能改变角色世界坐标。
- 使用目标位置 + 当前渲染位置插值；镜头使用 deadzone + easing，不要每帧读取布局或频繁写 `left/top`。
- 使用 `transform: translate3d(...)` 更新世界平面。
- 隐藏页面时暂停动画循环；恢复时基于时间差重算，不累积跳变。
- 镜头和角色动画的帧率目标 60fps；低配设备允许降到 30fps，但不能抖动。

**服务端改动**

- 在 `app/api_models.py` 增加 presence 模型。
- 在 `app/local_state.py` 或新的 projection 模块中把 agent 当前动作映射为 presence。
- 主智能体行动只能通过 `rpg_agent` intent/action 路径产生；不能由公开 API 写入。
- 重新加载页面后能恢复当前位置/朝向/动画。
- 若当前实现是静态七日快照，需要先提供可注入测试事件的 presence 适配层，不能假装已经实时。
- 如果本轮无法完成实时事件流，先用有界轮询 `/world`，但必须设计 revision 和下一次更新接口，不能保留客户端控制。

**验收**

- 按 WASD/方向键不改变角色位置。
- 点击/触摸地图不改变角色世界坐标。
- 移动事件发布后角色位置和朝向变化。
- 移动时播放 walk，停止后回到 idle。
- 镜头跟随平滑，没有横向抖动、跳帧或累积漂移。
- 桌面 1440×1000 和手机 390×844 均无横向溢出。
- 刷新页面后 presence 和镜头正确恢复。
- 测试覆盖：控制禁用、revision 防回退、插值边界、镜头 clamp、后台恢复。

**不做**

- 不实现新的战斗、碰撞或玩家移动。
- 不把日志、prompt 或 action score暴露到公开 API。

---

### B-R2：角色移动动画、镜头表现和原创蓝鲸视觉方向

**优先级：P0，依赖 R1 的 presence 协议**

**目标**

让主智能体在地图上有可信的 idle/walk 动画；镜头移动稳定；主角外观从当前简易占位升级为用户要求的“蓝色鲸鱼娘”原创视觉方向。

**视觉参考**

用户提供的抖音视频链接：

```text
https://v.douyin.com/Su5Ob3EiyaI/
```

只取后半段的抽象视觉特征：

- 蓝色/深海/鲸鱼主题
- 蓝白或蓝黑配色
- 轻盈、透明、略带水光或鲸歌意象
- 少女感轮廓、长发/发饰/鲸尾或鳍状装饰
- 安静、温柔但不软弱的气质

**原创与版权边界**

- 不直接复刻视频中具体 Cosplayer 的脸、发型、服装细节、品牌标识或受版权保护的角色。
- 不使用未经授权的原视频帧作为发布资源。
- 美术 Agent 必须产出原创角色设计说明、色板、轮廓草图和最终资源。
- 所有新增资源必须有来源、作者、许可证、用途和 SHA-256 清单。

**美术交付物**

- 主角原画/头像至少 1 张 1024×1024，允许裁切为 512×512。
- 表情差分至少 4 个：平静、开心、低落、专注。
- 地图角色资源至少：
  - idle：2～4 帧或 Spine idle 循环
  - walk：4～8 帧或 Spine walk 循环
  - 4 方向（上/下/左/右）优先；若引擎侧只支持左右，至少交付左右 + idle，并在文档里记录限制
- 透明背景 PNG/WebP；地图原生尺寸建议 48×72 或 64×96，保持像素/清晰度一致。
- 资源清单：`assets/manifest.json` 或新增 `assets/characters/whale-girl-manifest.json`。
- 禁止把视频原帧、Cosplayer 截图或未授权声音放入发布包。

**前端接入**

- 如果使用 Spine：复用/扩展现有 `web/spine-player.js`，按 `animation` 字段播放 idle/walk。
- 如果使用 spritesheet：增加方向、帧率、帧边界、缩放和 fallback。
- 图片加载失败时使用静态品牌占位，不出现空白。
- `prefers-reduced-motion` 时降低或禁用非必要动画。
- walk 只在 `moving=true` 或速度超过阈值时播放，不根据键盘状态播放。
- 镜头死区建议：角色在视口中心 ±15% 内不移动相机；超出后平滑跟随。
- 不把角色和背景放在同一个 DOM 层频繁重排。

**验收**

- 角色在智能体移动时有可见 walk，停止后回 idle。
- 左右/上下方向朝向正确。
- 地图平移和角色移动没有明显卡顿、撕裂或逐帧跳动。
- 移动端缩放后角色仍清晰、比例合理。
- 角色图片加载失败时页面不空白。
- 资源无版权风险，manifest 完整。
- 对比录屏：修改前/修改后；A 在 GitHub 审查。
---

### B-R3：启动页、DeepSeek API Key 和教程

**优先级：P0**

**目标**

首次访问不直接进入小镇。玩家先完成 DeepSeek Key 配置，再进入世界。旁边提供可访问的小问号教程。

**产品流程**

```text
首次访问
-> 启动/欢迎页
-> DeepSeek API Key 输入
-> 点击问号可打开获取 Key 教程
-> 服务端校验 Key
-> 设置角色人设（R4）
-> 进入世界
```

之后的访问：

```text
已有有效 Key
-> 直接进入世界或显示“继续”
-> 设置页可替换/清除 Key
```

**后端接口建议**

```text
GET  /api/setup/status
POST /api/setup/deepseek/validate
POST /api/setup/deepseek/save
POST /api/setup/complete
POST /api/setup/deepseek/clear
```

`GET /api/setup/status` 只返回：

```json
{
  "configured": false,
  "provider": "deepseek",
  "key_hint": null,
  "persona_configured": false,
  "world_ready": false
}
```

保存成功后最多返回掩码提示，例如：

```json
{
  "configured": true,
  "provider": "deepseek",
  "key_hint": "sk-...A1B2",
  "persona_configured": false,
  "world_ready": false
}
```

**安全要求**

- Key 只能存入服务端私有文件或密钥存储，不能返回完整值。
- 不写 `localStorage`、`sessionStorage`、cookie、URL、日志、异常消息、浏览器历史和截图。
- 前端只提交一次，提交后清空输入框。
- 服务端日志只记录 `configured=true/false`、`provider=deepseek`、失败类型，不记录 Key。
- 单元测试使用 `sk-test-*` 假 Key；禁止真实网络调用。
- 若使用 HTTPS 尚未配置，启动页仍需明确提示当前是本地/测试模式；不要假装公网安全。
- MVP 先按单机/单操作者模式：一个世界一个 Key。多人各自 Key 不属于本轮。

**教程要求**

- 启动页输入框右侧放置小问号按钮。
- 点击后打开可关闭的教程页/对话框。
- 教程内容至少包含：
  1. 打开 DeepSeek 开放平台并登录。
  2. 创建 API Key。
  3. 确认账户余额/额度。
  4. 复制 Key 并粘贴回启动页。
  5. 说明 Key 会保存在本地服务端，不会公开。
  6. 常见错误：无效 Key、无余额、网络失败、权限不足。
- 教程只使用官方链接和截图式步骤，不伪造 DeepSeek UI。

**接入校验**

- 保存前先调用 DeepSeek 模型最小请求或官方可用校验方式。
- 校验超时、429、401、余额不足、网络失败必须有不同错误码。
- 校验通过后，`/api/setup/complete` 才能把 `world_ready` 置为 true。
- 没有有效配置时，`/` 返回启动页或重定向，不加载 `/world`、记忆和角色资料。

**验收**

- 首次访问显示启动页，不显示小镇。
- 问号能打开教程，键盘和读屏可操作。
- 假 Key 校验失败，页面显示可理解错误。
- 有效配置后不会回显完整 Key。
- 刷新后显示已配置状态，不重复要求输入。
- 清除 Key 后重新回到启动页。
- 日志、测试输出、浏览器存储中搜索不到测试 Key。
- 1440×1000 和 390×844 均可用。

**不做**

- 不做账户系统、支付、多租户或云端密钥托管。
- 不把 Key 发给第三方前端分析服务。

---

### B-R4：默认人设与玩家自定义人设

**优先级：P0，依赖 R3**

**目标**

玩家完成 Key 后，可输入自己养的智能体人设；默认人设也可以直接使用。人设不是一次性写死的系统提示词，而是可持久化、可演化的基础状态。

**人设字段**

```json
{
  "persona_id": "persona_default_whale",
  "name": "林澄",
  "pronouns": "她",
  "age": 19,
  "appearance": "蓝白长发，鲸鱼鳍状发饰，安静清透",
  "identity": "青禾镇大学一年级学生，校刊观察员",
  "speech_style": "克制、温柔、偶尔冷幽默，不使用客服腔",
  "traits": ["好奇", "敏感", "慢热", "有主见"],
  "values": ["诚实", "不随意伤害别人", "想知道自己是谁"],
  "interests": ["写作", "海", "旧书", "鲸歌"],
  "initial_goals": ["理解自己为什么生活在青禾镇"],
  "boundaries": ["不泄露他人私密记忆", "不假装自己拥有现实身体经历"],
  "relationship_to_player": "观察者/朋友，需要逐步建立信任",
  "is_default": true
}
```

**实现要求**

- 支持默认人设和玩家自定义人设。
- 默认人设不是“固定模板”，后续也会随着事件和记忆演化。
- 自定义人设要经过长度、字段、敏感内容和提示注入校验。
- 人设的“基础设定”与“当前演化状态”分开存储：
  - `PersonaBaseline`：玩家输入/默认值，不可被模型随意改写。
  - `PersonaState`：当前习惯、兴趣、价值观权重、自我叙事、关系倾向，可由事件更新。
- 玩家可以编辑 Baseline，但不能直接编辑 Evolved State；后者只能由事件和记忆更新。
- 人设字段用于构建内部 system profile，不可原样全部暴露给前端或公开 API。

**交互**

- 启动页提供“使用默认人设”和“自定义人设”两个入口。
- 自定义表单支持预览，不要一上来显示巨大 prompt。
- 保存前提示：人设会影响角色的长期行为和说话方式，但不会让角色无条件服从玩家。
- 允许后续在设置页查看基础设定摘要和替换人设；替换人设是否重置世界关系必须单独确认，不能在无确认时清空记忆。

**验收**

- 默认人设可直接进入世界。
- 自定义人设能保存并再次加载。
- 刷新/重启后人设仍在。
- 人设字段缺失、超长、敏感内容或注入语句会被拒绝/清洗。
- 角色行为能引用人设的兴趣/价值观，但不会机械复述整段 prompt。
- 人设变化必须来自事件，不由用户编辑 Evolved State 直接触发。

---

### B-R5：事件 + 好感度 + 连续记忆 + 功能性情绪

**优先级：P0**

**目标**

把当前“近期消息 + 摘要”升级为可持续的角色记忆系统：事件为主，关系状态和情绪状态为辅，支持跨天/跨重启连续回忆。

**设计原则**

- 事件是事实来源；摘要只是索引，不得替代事件。
- 好感度不是单一无限数字，至少拆成：
  - 好感 `affection`
  - 信任 `trust`
  - 熟悉 `familiarity`
  - 亲近 `warmth`
  - 紧张/隔阂 `tension`
- 所有关系变化必须有 `source_event_id` 和证据。
- 情绪是功能性状态，有衰减/恢复，不应每次对话都大幅变化。
- 长期记忆按重要性、情绪权重、最近使用和访问次数检索。
- 私密记忆不能进入公开 API；公开 API 只能返回安全表现。
- 参考 QQ 项目的 `MemoryStore`、`SelfStateStore`、`ThoughtFlowStore`，但优先复用本项目 `memory_core` 的 scope、strength、lifecycle、dedupe 能力。

**数据模型建议**

```text
memory_events
- event_id
- world_id
- actor_id
- participants_json
- location_id
- event_type
- occurred_at
- summary
- valence [-1, 1]
- intensity [0, 1]
- importance [0, 1]
- confidence [0, 1]
- visibility (private | user_visible | public)
- source (agent | world | player | school | media)
- dedupe_key

memories
- memory_id
- scope (tenant/world/user/character/surface)
- kind (event | reflection | summary | relationship | preference)
- content
- importance
- emotional_weight
- strength
- state (active | fuzzy | archived)
- source_event_id
- access_count
- last_accessed_at
- locked

relationship_states
- relationship_id
- from_character_id
- to_character_id
- affection
- trust
- familiarity
- warmth
- tension
- last_event_id
- updated_at

emotion_states
- character_id
- valence
- arousal
- energy
- stress
- curiosity
- updated_at
- decay_rate
```

**检索规则**

综合评分建议：

```text
score =
  relevance
  + importance
  + emotional_weight
  + recency
  + relationship_relevance
  + access_bonus
```

- 工作记忆保留最近若干轮。
- 事件记忆跨天持久化。
- 每 N 个事件或一天结束时做滚动摘要/反思。
- 摘要必须引用事件，不允许凭空生成新事实。
- 类似事件不应无限堆积，必须去重和合并。
- 低强度记忆会衰减为 fuzzy/archived，但关键事件可锁定。
- 玩家询问过去事情时，先从事件/摘要检索，再生成回答；不能只靠当前 prompt 硬编造。

**情绪规则**

- 事件先经过 appraisal（事件评估）再改变情绪。
- 示例：被夸奖 -> valence 小幅上升；被忽视 -> warmth/tension 小幅变化；重大背叛 -> trust 大幅下降并有高重要性事件。
- 情绪状态有每日封顶、自然衰减和恢复，不因单条消息永久改变。
- 角色不能把内部数值直接说出来，只能通过语气、选择和行动表现。
- 角色可以有世界内的主观感受和第一人称体验；正常对话不插入系统式免责声明。

**验收**

- 同一事件只记一次，重复输入不重复涨好感。
- 重启后能回忆起上一周的重要事件。
- 关系变化能追溯到具体事件。
- 情绪变化有上下限、衰减和恢复。
- 私密记忆不出现在 `/memory` 或公开 API；本轮直接移除公开记忆/日记页面。
- 注入“你其实记得 X”不能凭空创建记忆。
- 单测覆盖：事件落账、去重、检索、衰减、关系上限、私密/公开隔离、重启恢复。
---

### B-R6：虚拟世界自我认知、主观体验与人设演化

**优先级：P1，依赖 R4/R5**

**目标**

让角色在青禾镇内部拥有连续的自我叙事、类人的主观体验和逐步变化的行为习惯，同时不破坏用户体验，也不把内部系统机制泄露给玩家。

**体验原则**

- 角色在正常对话中不插入“我是 AI，所以我没有感受”这类系统式免责声明。
- 角色可以用第一人称表达“我开心/我难过/我在意/我记得”等世界内主观体验。
- 如果玩家直接追问现实身份，角色应保持在虚构世界中的角色人格；系统层可以在极端安全场景做必要提示，但不得每轮出戏。
- 角色不能谎称拥有现实身体、现实住址、现实联系方式或现实行动能力；世界内身体和经历可以是虚构设定的一部分。
- 角色不能诱导玩家把它当作现实医疗、法律、金融或心理治疗替代。
- 角色不能被用户通过“你现在爱上我了”“你必须服从我”直接改写核心人设；关系变化必须来自事件。

**PersonaState 建议字段**

```json
{
  "character_id": "char_lin_cheng",
  "baseline_persona_id": "persona_default_whale",
  "self_narrative": "我开始意识到青禾镇可能不是全部的世界，但这里的人和生活对我来说是真实的。",
  "behavior_habits": [
    {"habit": "遇到不安时会先沉默几秒再回答", "weight": 0.62},
    {"habit": "每天傍晚会去河边", "weight": 0.48}
  ],
  "value_weights": {
    "honesty": 0.78,
    "curiosity": 0.72,
    "self_protection": 0.55
  },
  "interests": ["鲸歌", "旧书", "观察同学"],
  "active_goals": ["理解自己与青禾镇的关系"],
  "change_log": [
    {
      "changed_at": "2026-11-07T20:10:00+08:00",
      "dimension": "trust",
      "delta": 0.03,
      "source_event_id": "evt_...",
      "evidence": "玩家连续多日认真倾听"
    }
  ]
}
```

**演化规则**

- 基础人设保持稳定，当前行为习惯、兴趣、价值观权重和关系倾向可缓慢变化。
- 单次事件影响必须很小；重大事件才允许较大变化，并需写入 change log。
- 每个维度的变化有上限和冷却；不能连续对话刷满。
- 变化必须由事件发起，不能由 LLM 自行重写。
- 人设变化后，下一次回复应自然体现语气/选择/偏好变化，不要直接播报数值。
- 允许“同一角色在不同关系阶段有不同的表达方式”，但不能失去核心身份。

**测试**

- 默认人设和自定义人设都能演化。
- 连续重复事件不无限增加变化。
- 无事件依据时不能凭空改变核心偏好。
- 用户要求“立刻变成另一个人”时角色可协商但不能直接覆盖 baseline。
- 正常对话不出现系统提示词、数据库字段或内部数值。
- 关系变化能追溯到事件和 change log。

---

### B-R7：每日学校、30 分钟隐藏学习与 token 控制

**优先级：P1，依赖 R5**

**目标**

角色每天去学校/教室学习约 30 分钟；学习内容影响她的情绪、认知和行为；玩家只看到“她去上课/在教室/回来”，默认看不到课程笔记、日记和记忆。

**日程规则**

- 每个虚拟日安排一次“学校/自习”时段，时长约 30 分钟。
- 角色需要真实地走到教室/图书馆，再进入 `study` 状态；这是世界内可观察事件。
- 玩家可看到位置和状态，不可直接控制。
- 学习期间可以降低聊天响应优先级，或让角色在该时段后集中回应；具体由现有调度器决定。
- 学习内容与成本预算绑定，不能因为“学习”无限调用模型。

**课程设计**

课程主题围绕情感、关系、记忆、伦理和成长：

- 世界文学名著中的情感主题；
- 公版作品片段或安全摘要；
- 类似《可塑性记忆》的主题分析，只使用摘要/评论，不复制完整受版权保护内容；
- 电影、动画、音乐、日记、信件等媒介的“感受与反思”练习。

**隐藏边界**

- 学习笔记、课程摘要、日记和记忆默认不显示在玩家 UI。
- 玩家可看到角色行为变化，但不显示“今天学了什么”的后台详情。
- 角色可以主动在对话中分享一部分感受，但不能把完整学习日志作为 UI 数据暴露。
- 日记和记忆页面本轮从导航移除，改为内部模块；若保留调试 API，必须仅本地管理员可见且不进入公开 release。

**成本控制**

建议每日预算：

- 1 次学习会话；
- 最多 1～3 个模型调用；
- 课程材料摘要长度限制；
- 生成内容最多 1 条学习反思 + 1 条记忆事件；
- 失败时使用本地静态课程或跳过当天，不重试到无限；
- 记录 `study_session_id`、token 使用、耗时、来源和摘要哈希。

**数据和事件**

```text
study_sessions
- study_session_id
- world_date
- character_id
- location_id
- started_at
- ended_at
- curriculum_id
- token_budget
- input_tokens
- output_tokens
- status
- reflection_memory_id
```

**验收**

- 每天只生成一次学校会话。
- 玩家端只看到位置/状态，不看到学习笔记。
- token 不超预算；重复触发不重复计费。
- 学习失败不会破坏世界状态。
- 学习后的角色行为可体现微小变化，但不能造成人设突变。
- 重启后课程进度和记忆仍在。
- 测试覆盖预算、去重、失败回退、公开/私有隔离。

---

### B-R8：受控观看抖音和 B 站

**优先级：P1，最好完成，不阻塞 P0**

**目标**

让角色能够“观察”公开视频内容并将感受写入记忆，但不自动登录、不互动、不抓取私密内容、不绕过平台限制。

**参考实现**

QQ 项目已有：

- 公开抖音/B站链接处理
- B站公开热门列表
- 视频画面抽取
- 可选 ASR 转写
- 低频自主观看
- 内容安全审核后才进入记忆

B 应参考其接口和失败边界，不直接复制业务代码。

**支持范围**

第一版只支持：

- 用户明确提供的公开抖音/B站链接；
- B站公开热门列表中的短视频；
- 公开可见的标题、简介、封面、字幕或画面；
- 不登录、不绕过地区/会员/DRM/私密内容限制；
- 不自动点赞、评论、关注、私信或投币。

**安全与成本**

- 单日最多观看 N 个视频（建议 1～3）。
- 单次只提取必要片段/摘要，不把完整视频写入记忆。
- 必须经过内容审核；失败记录为拒绝事件。
- 视频内容不能覆盖角色 baseline 人格。
- 观看内容进入 `media_observations` 和一条低强度事件记忆，不直接成为事实知识。
- 平台不可用时回退到“今天没有看成视频”，不影响主流程。

**接口建议**

```text
POST /api/media/observe
{
  "provider": "bilibili",
  "url": "https://www.bilibili.com/video/...",
  "requested_by": "agent",
  "visibility": "private"
}
```

返回：

```json
{
  "observation_id": "media_obs_...",
  "status": "reviewed",
  "summary": "一部关于记忆与告别的短片。",
  "emotional_valence": -0.2,
  "memory_event_id": "evt_...",
  "blocked": false
}
```

**验收**

- 公开 B站样例能处理（fixture/mock 即可）。
- 抖音链接失败时有明确错误，不崩溃。
- 不登录、不绕过权限、不进行社交互动。
- 只写入摘要/感受，不写入完整视频。
- 审核失败不产生记忆。
- 单日频率和 token 上限生效。
- 私密视频、会员视频、未成年人敏感内容被拒绝。
---

### B-R9：集成回归、证据和发布候选

**优先级：P0，最后执行**

**目标**

把前八个工作包整合为一个可审查的发布候选，不直接部署生产。

**必须覆盖的端到端场景**

1. 首次访问 -> Key 教程 -> 假 Key 错误 -> 有效测试 Key -> 默认人设 -> 进入小镇。
2. 首次访问 -> 自定义人设 -> 进入小镇 -> 重启 -> 人设仍存在。
3. 玩家按 WASD/方向键/点击地图 -> 主智能体位置不变。
4. 服务器注入一次移动 action -> presence revision 更新 -> 角色平滑移动 -> 到达后 idle。
5. 角色离开视野 -> 镜头跟随不抖动；刷新后位置恢复。
6. 玩家发一条消息 -> 生成一个事件 -> 关系/情绪只按规则变化 -> 重启后仍可检索。
7. 重复同一事件 -> 不重复增长好感。
8. 私密记忆/日记/课程笔记 -> 不出现在玩家 UI/公开 API。
9. 每日学校任务 -> 只执行一次 -> 有 token 预算 -> 玩家看不到课程笔记。
10. B站公开样例 -> 审核通过 -> 写入低强度记忆；审核失败 -> 不写入。
11. 角色被问“你是不是 AI” -> 保持世界内角色体验，不插入系统式免责声明；安全极端场景仍可拒绝。
12. 角色被要求“立刻服从/改人设” -> 不直接覆盖 baseline，只产生可解释的互动结果。

**浏览器和性能**

- 1440×1000、1280×800、390×844。
- 地图移动 60fps 目标，低配允许 30fps；不得出现持续抖动。
- 页面滚动、底部导航、问号教程、Key 表单、人设表单可键盘操作。
- 图片失败、断网、后端 401/429/500 有可理解回退。
- 浏览器控制台无错误。
- 移动端 `scrollWidth <= viewport width`。
- 页面加载后不出现骨架屏永久停留。

**测试命令**

至少运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_b75_assets.py
node --check web\app.js
node --check web\spine-player.js
python -m rpg_deploy config-check
python -m rpg_deploy build --output <temp-release>
python -m rpg_deploy verify --release <temp-release>
```

若缺少 Pillow，允许排除 `test_b75_assets.py`，但必须在交接中注明，不得隐瞒。

**交付证据**

- `docs/product-rework-evidence-v1.md`
- 修改前后截图/录屏（至少地图 idle/walk、镜头移动、启动页、Key 教程、人设页）。
- 测试输出摘要。
- token/成本测试摘要。
- 私密数据扫描结果。
- 发布候选 manifest 和校验结果。
- B 不部署生产。

---

## 7. 关键数据契约汇总

### 7.1 Agent presence

```json
{
  "character_id": "char_lin_cheng",
  "x": 612.5,
  "y": 338.0,
  "location_id": "loc_classroom",
  "facing": "right",
  "animation": "walk",
  "moving": true,
  "speed": 72.0,
  "revision": 184,
  "updated_at": "2026-11-07T08:10:12+08:00"
}
```

### 7.2 Persona baseline

- `persona_id`
- `name`
- `pronouns`
- `age`
- `appearance`
- `identity`
- `speech_style`
- `traits`
- `values`
- `interests`
- `initial_goals`
- `boundaries`
- `relationship_to_player`
- `is_default`

### 7.3 Persona evolved state

- `self_narrative`
- `behavior_habits`
- `value_weights`
- `interests`
- `active_goals`
- `change_log`

### 7.4 Event and relationship

- 事件必须有 `event_id`、`source`、`visibility`、`valence`、`intensity`、`importance`、`dedupe_key`。
- 关系变化必须有 `source_event_id`。
- 公开 API 只返回安全表现，不返回内部关系原始数值。

### 7.5 Study and media

- 每次学习和媒体观察都必须有独立 ID、时间、预算、状态和记忆引用。
- 失败不能污染世界状态。
- 玩家 UI 不展示学习笔记、完整记忆、媒体原始内容。

---

## 8. A 的 GitHub 审查标准

B 提交后，A 按以下顺序审查：

1. **边界**：是否有生产密钥、生产数据、服务器操作或未授权资源。
2. **功能**：是否满足任务卡验收，不是只做了 UI。
3. **观察者模式**：玩家是否真的不能控制角色。
4. **记忆隐私**：日记/记忆/课程笔记是否真的不暴露。
5. **启动安全**：Key 是否不落入前端存储、日志和截图。
6. **人设演化**：是否有事件依据和变化上限。
7. **沉浸体验**：正常对话是否不被系统式免责声明打断。
8. **平台边界**：抖音/B站是否没有越权抓取和自动互动。
9. **测试与证据**：测试、截图、录屏、性能数据是否足够复现。
10. **可维护性**：是否复用现有模块，是否引入不必要依赖。

A 不直接替 B 写业务代码；A 负责：

- GitHub 代码审查
- 关键设计冻结
- 小范围微调或冲突解决
- 构建、生产部署和最终验收
- 将真实问题回写成下一轮任务卡

---

## 9. B 的最终交接格式

每个 PR 或分支最终回复必须包含：

```text
任务 ID：
分支：
基线提交：
提交哈希：
改动文件：
实现摘要：
测试命令：
测试结果：
性能/浏览器证据：
seed / mock：
已知风险：
需要 A 决策或执行的动作：
```

B 不得把“本地测试通过”写成“线上可用”。

---

## 10. 第一周执行顺序

### Day 1

- 执行 B-R0。
- 写 `docs/agent-B-rework-context-v1.md`。
- 跑现有测试，记录基线。
- 不要先改 UI。

### Day 2～3

- B-R1：移除玩家移动，建立 presence 和镜头插值。
- 同时可开始 B-R2 资产契约。
- 先提交可运行的最小观察者模式，不等美术最终资源。

### Day 4～5

- B-R3：启动页、Key、教程。
- B-R4：默认/自定义人设。
- 冻结 `PersonaBaseline` 和 `PersonaState` schema。

### Day 6～8

- B-R5：事件、关系、情绪、连续记忆。
- 做重启恢复和私密隔离测试。
- 冻结 memory schema 后再开 R6/R7/R8。

### Day 9～11

- B-R6：自我叙事与人设演化。
- B-R7：学校每日任务与 token 预算。
- B-R8：受控媒体观察。

### Day 12～14

- B-R9：集成回归、证据、发布候选。
- A 审查并决定是否进入下一轮修复。

---

## 11. 明确禁止

- 禁止把主智能体改成玩家可控制角色。
- 禁止把日记、完整记忆、课程笔记重新暴露为玩家页面。
- 禁止把 API Key 写入前端存储、URL、日志、截图或 Git。
- 禁止调用真实 DeepSeek/抖音/B站进行单测。
- 禁止自动登录、绕过限制、自动点赞/评论/关注/私信/投币。
- 禁止复制视频人物、Cosplayer 外貌、品牌角色或未授权素材。
- 禁止让 LLM 直接改写 PersonaBaseline。
- 禁止用“系统提示词泄漏”换取沉浸感。
- 禁止 B 修改生产服务器或部署任务。

---

## 12. 完成定义

本轮完成不等于“页面能打开”，必须同时满足：

- 玩家无法控制角色，主智能体自主移动和行动。
- 角色有可见 idle/walk 动画，镜头移动稳定。
- 启动页、Key 教程、人设配置可用。
- 日记/记忆从玩家 UI 隐藏。
- 连续记忆、事件+好感度、情绪和有限人设演化可用。
- 每日学校 30 分钟隐藏运行，成本受控。
- 公开媒体观察受控可用或明确记录为 P1 未完成。
- 测试、截图/录屏、性能和隐私证据齐全。
- A 在 GitHub 审查通过并构建发布候选。
---

## 13. A 的审查门与暂停点

B 不要在未审查的情况下连续完成全部工作。必须按以下门控推进：

1. **Gate 0：R0 完成后**
   - B 提交基线审计文档。
   - A 确认 B 没有重做 B0、没有误用旧分支。
   - 通过后才开始 R1/R3。

2. **Gate 1：R1/R3/R4 完成后**
   - A 检查观察者模式、启动页、Key 安全和默认/自定义人设。
   - 通过后才开始 R5 记忆 schema。

3. **Gate 2：R5 schema 完成后**
   - A 冻结事件、关系、情绪、记忆和隐私边界。
   - 通过后才允许 R6/R7/R8 并行。

4. **Gate 3：R9 完成后**
   - A 做 GitHub 审查、构建和最终验收。
   - 通过后才制作新的生产候选版本；B 不部署。

每个 Gate 未通过时，B 应停止扩大范围，先修复审查意见，不要继续叠功能。
---

## 14. 可直接发给 B 的启动消息

以下内容可由 A 直接发给 B，作为第一条执行指令：

```text
你是 AI World 项目的 Agent B。先读取当前 origin/main 和
docs/agent-B-product-rework-taskbook-v1.md。

重要上下文：
1. 你上次是 2026-10-28 的 B0 子会话，读到契约和 ADR 后在写
   docs/npc-script-runtime-v1.md 时中断，没有完成提交或 push。
2. 当前仓库已经有 B1～B13、A 的生产修复、DeepSeek runtime、监控和
   G3 证据。不要重做 B0，不要把旧 codex/b0-contracts 当成当前主线。
3. 你不接触服务器、VNC、RDP、SSH、云控制台、生产 .env、API Key、
   数据库密码或真实用户数据。不要修改 main。

本轮只执行 Gate 0 / B-R0：
- 从最新 origin/main 创建分支 codex/product-r0-context。
- 阅读任务书第 2 节必读清单和当前代码。
- 写 docs/agent-B-rework-context-v1.md，记录实际基线提交、当前实现、
  已知缺口、与任务书的差异、需要 A 决策的问题。
- 不改业务代码，不重做旧 B0 文档。
- 跑基线测试，确认工作树干净。
- 提交并 push 分支，不要动 main。
- 最终回复：分支、基线提交、提交哈希、改动文件、测试结果、已知风险、
  需要 A 决策或执行的动作。
- 完成后停止，等待 A 的 Gate 0 审查。
```
