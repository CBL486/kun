# Gate 2 产品重构审查结果

状态：PASS（带后续美术和生产验证条件）  
审查人：Agent A  
审查日期：2026-11-07  
集成分支：`codex/gate2-review`

## 1. 审查范围

本轮审查并集成：

- R2：`origin/codex/product-r2-character-art`
  - 功能提交：`dbb48a2`
  - 交接提交：`f30c4be`
- R5：`origin/codex/product-r5-memory-affection`
  - schema/世界时钟：`7734fa3`
  - 外部数据和代理保护：`e1475a1`

R2、R5 均基于最新 Gate 1 main。集成时无业务代码冲突，R5 与 R2 的合并结果已通过回归。

## 2. R2 验收结果

已确认：

- 原创蓝鲸少女主视觉 1024×1024。
- 平静、开心、低落、专注 4 张 512×512 表情。
- 64×96 四方向地图角色。
- idle、walk、turn、stop 四组精灵表。
- presence 驱动行走、转向、停止和 idle。
- 减少动态时固定 idle 首帧。
- 玩家移动控件和死 CSS 已移除。
- 资源清单、尺寸、Alpha 和 SHA-256 测试通过。
- 桌面和手机截图正常，没有横向溢出。

美术定位：这是可用的轻量原创像素风第一版，不是最终高预算美术。资源结构、动画接口和版权边界已通过 Gate 2；后续可以继续提升角色细节和表情质量。

## 3. R5 验收结果

已确认：

- 数据库 schema 从 4 升级到 5。
- 新增 memory_events、relationship_states、emotion_states、Persona baseline/state/change log、study_sessions、media_observations、setup/credential reference、world_clock_states。
- 事件、关系、情绪和记忆变化都有事件依据和去重语义。
- Persona JSON 可导入 schema 5，重复导入幂等。
- 默认 Persona 的安全边界已移动到系统策略，不进入玩家基础人设。
- 世界时钟使用 Asia/Shanghai，10 分钟 tick，24 小时内压缩追赶，超过 24 小时摘要跳转。
- 生产数据目录已在示例配置中移到 release 外部：
  - C:\AIWorld\data\setup
  - C:\AIWorld\data\persona
  - C:\AIWorld\data\world
- Nginx/Caddy 模板已加入 `/setup`、`/api/setup/*`、`/api/persona/*` 的保护规则。
- Windows ACL 分支使用 SID。
- `AIWorld-WorldTick` 已加入任务模板。

## 4. 验证结果

集成后运行：

```text
pytest：228 passed, 1 warning
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true
config-check：issues=[]
release build：223 files
release verify：issues=[]
```

浏览器证据：

- `docs/screenshots/r2-idle-desktop.png`
- `docs/screenshots/r2-walk-desktop.png`
- `docs/screenshots/r2-walk-mobile.png`
- `docs/screenshots/r3-setup-desktop.png`
- `docs/screenshots/r3-setup-mobile.png`
- `docs/screenshots/r3-setup-tutorial.png`
- `docs/screenshots/r4-persona-form-desktop.png`
- `docs/screenshots/r4-persona-form-mobile.png`
- `docs/screenshots/r4-persona-summary-desktop.png`

## 5. Gate 2 条件

### C1：美术仍是第一版

R2 已满足工程和动画接口要求，但：

- 角色细节、轮廓辨识度和表情表现仍是轻量像素风第一版；
- sit/study/talk 专用动作尚未实现；
- 后续可以在不改变资产接口的情况下继续提升美术质量。

这不阻塞 R5 schema 和 R6/R7 开发，但 R7 学校学习状态需要补充 `study` 动作，或明确使用 idle 回退。

### C2：生产任务注册由 A 完成

B 已交付 `AIWorld-WorldTick` 任务模板，但 B 不注册生产任务。

A 在 staging/生产必须验证：

- 每 10 分钟 tick；
- 持久化世界时钟；
- 24 小时内压缩追赶；
- 超过 24 小时摘要跳转；
- 不产生 LLM 调用；
- API/scheduler/monitor 不受影响。

### C3：生产 schema 5 迁移由 A 执行

R5 已有 SQLite/PostgreSQL 迁移和 JSON 导入测试，但生产迁移仍未执行。

A 在维护窗口必须：

1. 备份；
2. 在隔离库迁移 schema 5；
3. 导入 Persona JSON；
4. 验证重复导入幂等；
5. 验证关系/情绪/记忆事件约束；
6. 验证回滚和目标 schema；
7. 切换前再次 verify release。

### C4：真实 DeepSeek 和代理规则手动 smoke

CI 使用 fake client。A 还需手动验证：

- 真实 DeepSeek Key 保存、重启、清除；
- `/setup`、`/api/setup/*`、`/api/persona/*` 的代理拒绝规则；
- `/world`、`/agent`、`/timeline`、`/chat` 在 setup 未完成时返回 `setup_required`。

### C5：世界时钟不等于自主决策

R5 完成的是持久时钟和有界追赶；主智能体仍然需要 R7 的自主行动调度。

R7 必须把 clock tick、行动决策、课堂/学校状态和 token 预算接起来。

## 6. 合并决定

```text
Gate 2：PASS
R2/R5：允许合并到 main
下一步：R6 自我认知/人设演化、R7 学校与自主行动、R8 受控媒体观察可开始
R9 集成回归必须在 R6/R7/R8 完成后执行
```

## 7. 给 B 的下一步

从最新 main 创建：

- `codex/product-r6-self-awareness`
- `codex/product-r7-school-autonomy`
- `codex/product-r8-media-observation`

R6/R7/R8 可以并行，但必须共享 R5 的事件/关系/情绪/PersonaPolicy schema，不得各自另建一套记忆模型。

R6 的关键约束：

- 世界内第一人称主观体验；
- 正常对话不插入系统式免责声明；
- PersonaBaseline 不可被模型直接覆盖；
- 变化必须有事件和 change log；
- 安全策略保持在系统层。

R7 的关键约束：

- 每自然日最多一次 30 分钟学习；
- 1～3 次模型调用；
- 其余是低 token 阅读/写作状态；
- 玩家只看位置和状态，不看课程笔记/日记/记忆；
- 跨日不补播。

R8 的关键约束：

- 只处理公开链接或白名单；
- 不登录、不绕过 DRM/地区/会员限制；
- 不自动点赞/评论/关注/私信/投币；
- 审核失败不写记忆；
- CI 只用 fixture/mock。
