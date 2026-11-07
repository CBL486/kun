# Gate 1 产品重构审查结果

状态：PASS（带部署条件和 R5 前置项）  
审查人：Agent A  
审查日期：2026-11-06  
集成分支：`codex/gate1-review`  
集成提交：`3d28b60`

## 1. 审查范围

本轮审查并集成：

- R1：`origin/codex/product-r1-observer`，提交 `e61b931`
- R3：`origin/codex/product-r3-setup-key`，提交 `8740f36`
- R4：`origin/codex/product-r4-persona`，提交 `b1c1597`

R4 已包含 R3；R1 与 R4/R3 在本地集成时解决了 README、`app/main.py`、OpenAPI 文档和静态契约冲突。

## 2. 已完成并确认

### R1 观察者模式

- 玩家方向键、WASD、地图按钮不再改变角色位置。
- `/world` 使用 `rpg-public-world-v2`，返回只读 `agent_presence` 和 `state_revision`。
- 前端按 revision 插值 presence，使用 deadzone、easing 和 `translate3d`。
- 公开导航只剩小镇、角色、时间线、留言、设置五项。
- 日记、记忆导航、页面和公开 `/memory` 路由已移除。
- `/memory` 不在 OpenAPI 中。

### R3 启动页与 Key

- 首次访问 `/` 进入启动设置页。
- `/api/setup/*` 覆盖状态、校验、保存、完成和清除。
- Key 只在服务端私有目录保存，浏览器不写入存储、URL、cookie 或日志。
- Windows ACL 失败会阻断保存。
- 问号教程可见，桌面和手机布局通过浏览器证据。
- 未完成设置时 `/world`、`/agent`、`/timeline`、`/chat` 返回 `setup_required`，浏览器门禁之外也有 API 门禁。
- 真实 DeepSeek 网络校验不在 CI 中，使用 fake client。

### R4 Persona

- 默认原创蓝鲸少女 PersonaBaseline 已提供。
- 自定义 PersonaBaseline 持久化，生成 revision。
- PersonaBaseline 与 PersonaState 分离，玩家不能直接写 PersonaState。
- 年龄限制、长度限制、控制字符和明显提示注入校验存在。
- 修改人设不会清空世界、关系、记忆或位置。
- 角色 ID 保持 `char_lin_cheng`，自定义名称和身份可投影到公开角色卡。

## 3. 验证结果

集成后从 `codex/gate1-review` 运行：

```text
pytest：206 passed, 1 warning
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true
config-check：issues=[]
release build：194 files
release verify：issues=[]
python py_compile：通过
node --check：R1 setup JS 通过
```

浏览器证据已人工查看：

- R1 桌面 1440×1000：观察者模式、五项导航、无移动控件。
- R1 手机 390×844：底部五项导航，无横向溢出。
- R3 桌面/手机：启动页和教程正常。
- R4 桌面/手机：Persona 表单和完成摘要正常。

截图位于：

```text
docs/screenshots/r1-observer-desktop.png
docs/screenshots/r1-observer-mobile.png
docs/screenshots/r3-setup-desktop.png
docs/screenshots/r3-setup-mobile.png
docs/screenshots/r3-setup-tutorial.png
docs/screenshots/r4-persona-form-desktop.png
docs/screenshots/r4-persona-form-mobile.png
docs/screenshots/r4-persona-summary-desktop.png
```

## 4. Gate 1 条件

以下条件不阻塞本轮代码合并，但必须在部署和 R5/R6 前完成。

### C1：生产配置必须使用 release 外部路径

当前 `.env.example` 默认使用：

```text
AIWORLD_SETUP_DIRECTORY=./data/setup
AIWORLD_PERSONA_DIRECTORY=./data/persona
```

生产任务的工作目录是 `C:\AIWorld\current`。如果直接使用默认值，Key 和人设会写进 release 目录，导致：

- release 切换时 Key/人设可能丢失；
- release verifier 看到未列出的运行文件；
- 私有数据可能被错误地打包或备份。

生产环境文件必须明确设置：

```text
AIWORLD_SETUP_DIRECTORY=C:\AIWorld\data\setup
AIWORLD_PERSONA_DIRECTORY=C:\AIWorld\data\persona
```

并在部署前验证目录 ACL、release verify 和切换后持久化。

### C2：公开入口必须保护设置路由

`/setup`、`/api/setup/*`、`/api/persona/*` 属于单机/管理员设置面。

在公网反向代理或部署层必须：

- 仅允许管理员/本机访问；
- 不允许普通观察者读取或提交 Key；
- 不允许公开缓存；
- 不允许把 Key 输入页暴露给任意访客。

### C3：默认人设的安全边界不要变成角色台词

R4 默认人设里有系统安全性质的边界文本。R6 接入人格提示词时必须把这些内容放在系统层，不要让角色在正常聊天中机械复述或主动出戏。

正常体验坚持 Gate 0 D10：

- 角色可以使用世界内第一人称主观体验；
- 不插入系统式免责声明；
- 高风险场景才做安全打断或自然拒绝；
- 不声称拥有现实身体、现实联系方式或现实行动能力。

### C4：连续世界时钟尚未完成

R1 仍是冻结七日快照的 presence 适配层。Gate 1 接受这一点作为观察者模式的最小实现，但 R5/R7 必须按 D1 替换为持续世界时钟和有界停机追赶。

### C5：Persona 持久化后续迁移到 schema 5

R4 当前使用 JSON 持久化 Persona baseline/state/revision。R5 应按 D7 将 Persona 数据迁移到 schema 5，并提供：

- SQLite/PostgreSQL 双后端迁移；
- 旧 JSON 数据迁移或不丢数据策略；
- 回滚说明；
- revision 与 change log 一致性测试。

### C6：真实 DeepSeek 校验需要 A 手动 smoke

CI 全部使用 fake client。A 在部署候选前必须用隔离的真实 Key 验证：

- 启动页校验；
- 保存后重启；
- 清除 Key 后重新门禁；
- 日志、浏览器存储和响应中无完整 Key。

## 5. 合并决定

```text
Gate 1：PASS
R1/R3/R4：允许合并到 main
集成提交：3d28b60
下一步：R2 可开始；R5 schema 可开始
R6/R7/R8：等 R5 schema Gate 2 审查后再开
```

## 6. 给 B 的下一步指令

从最新 main 创建：

- `codex/product-r2-character-art`（如美术资源已就绪）
- `codex/product-r5-memory-affection`（schema 5 设计/实现）

R5 完成后必须停下来等 Gate 2，不要直接开始 R6/R7/R8。
