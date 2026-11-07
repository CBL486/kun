# Gate 3 产品重构审查结果

状态：PASS（R9 最终集成前有必改项）  
审查人：Agent A  
审查日期：2026-11-07  
集成分支：`codex/gate3-review`

## 1. 审查范围

本轮审查并集成：

- R6：`origin/codex/product-r6-self-awareness`
  - 功能提交：`5169bc4`
  - 交接提交：`8c71822`
- R7：`origin/codex/product-r7-school-autonomy`
  - 功能提交：`23e3663`
  - 交接提交：`6f1ede0`
- R8：`origin/codex/product-r8-media-observation`
  - 功能提交：`da842ae`
  - 交接提交：`d56dfc5`

三路合并时处理了 README、`app/main.py`、`app/local_state.py`、`rpg_llm/prompts.py`、`rpg_llm/fallback.py` 和 `rpg_orm/product_repository.py` 的冲突。集成后三套状态共用 schema 5，没有新增第二套记忆或关系模型。

## 2. R6 验收结果

已确认：

- 事件驱动 PersonaState 演化；
- PersonaBaseline 不被模型覆盖；
- 单次变化上限、6 小时冷却和 change log；
- EmotionState 联动；
- 系统安全策略与角色 profile 分离；
- `/chat` 使用世界内角色回应；
- API 身份问题保持林澄人格，不切换成客服播报；
- 高风险场景有自然拒绝路径；
- 聊天不创建伪造的 MemoryEvent。

## 3. R7 验收结果

已确认：

- schema 5 每日 `study_sessions` 状态机；
- 09:00 后触发，5 分钟走到教室，30 分钟现实时间学习；
- `scheduled/running/completed/missed` 状态；
- presence 显示 `enter_place`、`study`、`idle`；
- 每会话最多一次学习反思；
- 默认 1200 token 预算与静态回退；
- 学习笔记和 ReflectionEvent 只存在私有侧；
- 跨日不补播；
- `AIWorld-WorldTick` 已接入 `app.world_tick`；
- R2 资源新增四方向 study 动画。

## 4. R8 验收结果

已确认：

- 受控 MediaObservationService；
- B站/抖音公开 URL 白名单和跳转后复验；
- 公开元数据解析、审核和短摘要；
- 默认每日 2 次、600 token 预算；
- URL hash 去重；
- B站公开热门列表；
- 审核通过的摘要写一条私有 memory event；
- 媒体接口纳入 setup gate；
- 不自动点赞、评论、关注、私信或投币；
- CI 使用 fixture/fake，无真实网络请求。

## 5. 验证结果

集成后运行：

```text
pytest：256 passed, 1 warning
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true
config-check：issues=[]
release build：231 files
release verify：issues=[]
```

已查看浏览器证据：

- `docs/screenshots/r6-in-world-chat-desktop.png`
- `docs/screenshots/r6-in-world-chat-mobile.png`
- `docs/screenshots/r7-study-desktop.png`
- `docs/screenshots/r7-study-mobile.png`

## 6. R9 必改项

### C1：聊天排队文案与实际立即回复不一致

当前聊天页仍显示：

- “留言只会进入待处理队列”
- “不会立即回应”
- “已排队”

但 R6 已经会立即返回并显示林澄回复。

R9 必须选择并统一一种语义：

方案 A：真正的异步留言
- 立即回复隐藏；
- 角色在世界内稍后处理；
- UI 显示排队状态。

方案 B：即时对话
- 修改页面文案为“留言已送达，林澄会按自己的节奏回应”；
- 区分“已送达”和“已排队”；
- 若仍保留审核队列，说明何时进入对话。

不能继续同时显示“已排队”和“立即回复”。

### C2：R6 仍是 deterministic responder

R6 的 `/chat` 目前使用确定性 in-world responder，真实 LLM 生成还没有接入。R9 必须：

- 使用 DeepSeek 生产 runtime；
- 保留 PersonaPolicy/PersonaProfile；
- 通过正式 moderation 和 budget；
- 失败时用安全 fallback；
- 不在日志输出完整 prompt 或 Key。

### C3：R7 学习只有一次模型调用，不能持续烧 token

R7 的实现方向正确：

- 每日一次；
- 前段生成反思；
- 剩余时间是低 token 学习状态；
- 失败使用静态反思。

A 在 staging 必须验证：
- 一天只有一个 session；
- 重启不重复扣费；
- 跨日 missed；
- WorldTick 10 分钟节奏；
- 公开页面不显示课程摘要或记忆 ID。

### C4：R8 只处理公开 OG 元数据

当前 R8 不下载完整视频、不做 ASR、不自动互动。可以接受为本轮 P1 边界；R9 只需保证：

- 真实公开链接 smoke 不绕过限制；
- 页面结构变化时安全失败；
- 媒体摘要不进公开记忆页面；
- 每日上限和 token 预算生效。

### C5：R2 美术仍是第一版

R7 已补 study 动画，但整体角色美术仍是轻量像素风第一版。R9 不阻塞该质量水平，后续仍需单独美术迭代。

### C6：生产动作由 A 完成

R9/生产候选前仍需 A：

- 注册 `AIWorld-WorldTick`；
- 执行 schema 5 迁移和 JSON 导入；
- 验证代理保护设置；
- 验证真实 DeepSeek smoke；
- 验证媒体真实公开链接 smoke；
- 复核 release 不包含 data/logs/backups。

## 7. 合并决定

```text
Gate 3：PASS
R6/R7/R8：允许合并到 main
下一步：R9 最终集成与生产候选准备
R9 必须先修正聊天语义，再接入真实 DeepSeek chat
```

## 8. R9 最小验收清单

1. 聊天排队文案和实际行为一致。
2. 真实 DeepSeek 对话通过，失败可 fallback。
3. 世界内主观体验不暴露系统策略。
4. PersonaState 变化有事件依据。
5. 学校每日 30 分钟和 token 上限通过。
6. 媒体公开链接 smoke 和审核拒绝通过。
7. 设置路由外部拒绝。
8. schema 5 迁移/回滚演练通过。
9. 桌面和手机完整流程通过。
10. release verify 和最终证据齐全。
