# R8 受控媒体观察交接

状态：待审查

日期：2026-11-07

分支：`codex/product-r8-media-observation`

基线：`0f936d9c3cb636e15c10f5af28bc4a495730b97b`

## 1. 交付

- `MediaObservationService`；
- B站/抖音公开 URL 白名单与跳转后复验；
- 公开元数据解析、审核和短摘要；
- 每日 2 次上限、600 token 预算；
- URL hash 去重；
- B站公开热门列表选择；
- schema 5 `media_observations`；
- 审核通过的摘要写一条私有 `memory_events`；
- 小幅度 curiosity 变化；
- `POST /api/media/observe` 和 `/api/media/bilibili/hot`；
- 媒体接口纳入 setup gate。

## 2. 测试

```text
pytest：239 passed, 1 warning
fake provider / fake fetcher / fixture
公开观察、去重、每日上限：通过
URL 白名单、重定向和登录入口拒绝：通过
无 Authorization/Cookie 请求头：通过
审核/网络/摘要失败不写事件：通过
超预算静态回退：通过
B站热门选择：通过
```

## 3. 已知风险

- 当前只抽取公开 OG 元数据，不做完整视频或 ASR；
- 真实页面结构变化时解析失败，按 failed 处理，不影响世界；
- 真实网络 smoke 只由 A 手动验证，CI 全为 fixture/fake；
- 生产每日上限和 token 预算由 A 在环境文件确认。

## 4. 需要 A 做

1. 审查链接白名单和社交互动禁令；
2. 用真实公开链接做一次手动 smoke；
3. 确认每日上限、token 预算和审核策略；
4. 验证媒体事件不进入玩家公开记忆页面。
