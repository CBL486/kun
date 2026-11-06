# Agent B R0 Gate 0 审查结果

状态：PASS  
审查人：Agent A  
审查日期：2026-11-06  
B 分支：`codex/product-r0-context`  
B 提交：`6b670b9`  
审查基线：`46df378`  
合并目标：`main`

## 1. 审查结论

R0 通过。B 正确地从最新 `origin/main` 创建独立分支，只新增了
`docs/agent-B-rework-context-v1.md`，没有修改业务代码，没有重做 B0，没有访问或修改生产。

审计文档质量合格，明确记录了：

- B 上一次 B0 会话中断在 `docs/npc-script-runtime-v1.md`，未提交或 push。
- 当前主线已有 B1～B13、A 的生产修复、rc7 和 G3 证据。
- 当前 Web 仍有玩家手动移动逻辑。
- 当前 `/world` 没有连续 presence。
- 当前日记/记忆仍公开。
- 当前 API 冻结版本和新需求之间的冲突。
- QQ 参考项目在 B 的执行环境中未找到。
- 基线测试和发布验证结果。

## 2. 验证证据

B 报告并已由 A 接受：

```text
pytest：183 passed
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true
config-check：issues=[]
临时发布包：189 files
release verify：issues=[]
```

R0 只改文档，不改变业务行为，因此不要求重复运行完整 14 天或生产验收。

## 3. Gate 0 决策

以下决策对 R1～R9 生效。

### D1：持续世界时钟

采用持续运行的世界时钟，MVP 使用：

- 世界时间与 `Asia/Shanghai` 现实时间 1:1。
- 世界时间持久化，不以“每次启动重放七日模拟”作为权威。
- 后台行动 tick 建议 5～15 分钟一次，不为每个 tick 调用 LLM。
- 停机后允许有限追赶：
  - 24 小时内：按压缩行动摘要追赶，不逐分钟重放。
  - 超过 24 小时：记录“离线期间”摘要，直接跳到当前时间。
- 不允许无界补算导致 token 爆炸。

### D2：公开 API 升级

批准：

- `/world` 响应升级为 `rpg-public-world-v2`。
- 新增 `agent_presence`、`state_revision`、`updated_at`。
- 同步更新 OpenAPI、B6/B10 冻结测试和公开投影文档。
- 不允许静默改变 v1 字段；需要明确版本迁移说明。

### D3：日记和记忆隐藏

批准：

- 从玩家导航、页面和公开 API 移除日记与记忆。
- 不保留公开 `/memory` 路由。
- 内部记忆只允许服务端仓库、本地管理员 CLI 或测试工具访问。
- 如果保留诊断接口，必须只绑定 localhost、默认关闭、需要管理员授权，且不进入公开 release allowlist。
- 玩家只能看到行为表现和角色主动说出的内容。

### D4：角色身份

批准：

- 继续使用角色 ID `char_lin_cheng`，保持世界、关系、记忆和测试兼容。
- 默认显示名继续为“林澄”，除非用户在自定义人设中改名。
- 视觉方向改为原创“蓝鲸少女”风格；角色 ID 不作为外观锁定。
- 不使用视频人物或具体版权角色的复制品。

### D5：替换人设

批准：

- 修改 `PersonaBaseline` 必须创建新的 persona revision。
- 默认保留世界、角色关系、事件记忆和当前位置。
- “开始新世界/清空记忆”是独立动作，必须明确确认，不能由换人设隐式触发。
- `PersonaState` 和 change log 继续存在；用户不能直接编辑演化状态。

### D6：DeepSeek Key

批准：

- MVP 是单世界/单操作者模式。
- Key 保存在服务端私有文件或系统密钥存储中，ACL 限制到 Administrator/SYSTEM。
- 不写入浏览器存储、URL、日志、截图或 Git。
- 启动页显示掩码提示，不回显完整 Key。
- 设置时校验一次；后续只在 401/403/余额错误时重新校验。
- 支持替换和清除 Key；清除 Key 不自动清空世界。
- 单实例写锁，避免两个进程同时写同一 Key 文件。
- 本地未启用 HTTPS 时，启动页必须明确提示“本地/测试模式”。

### D7：Schema 5 冻结

批准新增 schema 5，至少包含：

- `memory_events`
- `memories` 扩展或迁移
- `relationship_states`
- `emotion_states`
- `persona_baselines`
- `persona_states`
- `persona_change_log`
- `study_sessions`
- `media_observations`
- `setup_state` / `deepseek_credentials` 的私有配置映射

要求：

- SQLite 与 PostgreSQL 同时迁移、回滚和验证。
- 旧 schema 数据必须有明确映射策略。
- B 不得在本轮再次无理由升级 schema 6；如需变化，先提交 A 审查。
- 记忆、关系、情绪、人设变化都必须有事件依据。

### D8：每日学校

批准：

- 每个自然日（`Asia/Shanghai`）最多一个学校/自习会话。
- 会话目标时长 30 分钟现实时间；不是 30 分钟持续 LLM 调用。
- 前 5～10 分钟完成 1～3 次模型调用，生成课程摘要、感受和一条记忆事件。
- 其余时间表现为阅读、写作、静坐等低 token 状态。
- 服务在当天内恢复时可续接或做一次简化补课；跨日不补播，只标记 missed。
- 玩家只看到位置和状态，不看到课程笔记、日记或完整记忆。
- 课程内容以公版文学、安全摘要和主题分析为主；不复制完整受版权保护内容。

### D9：抖音/B站受控观察

批准：

- 支持用户明确提供的公开抖音/B站链接。
- 支持 B站公开热门列表。
- 不登录、不绕过会员/地区/DRM/私密内容限制。
- 不自动点赞、评论、关注、私信、投币。
- 只保留摘要、感受和必要的公开元数据；不保存完整视频。
- 真实网络测试只作为手动 smoke，不进入普通 CI；CI 使用 fixture/mock。
- B 应参考 QQ 项目的 `bot_core/video.py`，但不得直接复制无关业务代码。

### D10：世界内主观体验与安全边界

批准：

- 正常对话中，角色使用世界内第一人称主观体验，例如“我在意”“我有点难过”“我记得”。
- 正常体验中不插入“我是 AI，所以我没有感受”这类系统式免责声明。
- 被直接询问是否 AI 时，角色保持在虚构世界中的角色人格，不突然变成客服或系统播报。
- 角色不能声称拥有现实身体、现实住址、现实联系方式或现实行动能力；世界内身体和经历属于虚构设定。
- 遇到自伤、他伤、医疗、法律、财务等高风险请求时，系统层可安全打断或在世界内自然拒绝。
- 不诱导玩家把角色当作现实真人、现实治疗师或现实依赖对象。

## 4. QQ 参考项目路径

B 审计环境中没有找到 QQ 项目。A 确认其路径为：

```text
D:\Users\LENOVO\Documents\ChatGPT\QQ
```

若 B 的执行环境没有该路径，必须读取 A 提交的：

```text
docs/qq-memory-reference-v1.md
```

B 不应再以“QQ 参考不可用”为阻塞继续猜测接口。

## 5. Gate 0 放行

批准 B 从最新 `main` 创建：

- `codex/product-r1-observer`
- `codex/product-r3-setup-key`
- `codex/product-r4-persona`

R1、R3、R4 可以并行；R2 资产契约可以并行，正式接入依赖 R1。

R5 记忆 schema 必须在 Gate 1 审查后开始。R6/R7/R8 等 R5 schema 冻结后再开。

## 6. R0 合并决定

```text
R0：PASS
合并：允许 fast-forward/merge 到 main
业务代码变更：无
生产操作：无
下一审查点：Gate 1（R1/R3/R4）
```
