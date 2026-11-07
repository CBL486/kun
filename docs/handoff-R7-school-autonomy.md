# R7 学校与自主行动交接

状态：待审查

日期：2026-11-07

分支：`codex/product-r7-school-autonomy`

基线：`0f936d9c3cb636e15c10f5af28bc4a495730b97b`

## 1. 交付

- schema 5 `study_sessions` 每日状态机；
- 09:00 后触发，5 分钟走到教室，现实 30 分钟学习；
- `scheduled/running/completed/missed` 状态；
- presence 显示 `enter_place`、`study`、`idle`；
- 每会话最多一次 `study_reflection`；
- 1200 token 预算和静态回退；
- 私有 learning event；
- 跨日未完成不补播；
- 后台 `AIWorld-WorldTick` 接入 `app.world_tick`；
- R2 资源新增四方向 study 精灵表。

## 2. 测试

```text
pytest：235 passed, 1 warning
每日单会话：通过
provider 单调用：通过
预算/失败回退：通过
重启与跨日恢复：通过
公开隔离：通过
```

## 3. 浏览器证据

```text
presence.location_id=loc_classroom
presence.animation=study
presence.moving=false
player.action=study
公开文本不含课程摘要/记忆 ID
桌面 1440×1000 无溢出
手机 390×844 无溢出
控制台错误=[]
```

截图：

```text
docs/screenshots/r7-study-desktop.png
docs/screenshots/r7-study-mobile.png
```

复现：

```text
scripts/run_r7_evidence_api.py
scripts/capture-r7-evidence.js
```

## 4. 已知风险

- 默认本地环境使用静态学习反思；生产 world_tick 通过 B9 gateway 调用模型；
- 学习内容当前是公版/安全摘要，后续可扩充课程库；
- 玩家聊天在学习期间的优先级尚未降级；
- 生产任务注册和真实 DeepSeek smoke 仍由 A 执行。

## 5. 需要 A 做

1. 审查每日 30 分钟和 token 预算语义；
2. 在 staging 验证 `AIWorld-WorldTick` 与一次学习调用；
3. 确认跨日 missed、同日续接和重启恢复；
4. 确认公开页面不出现学习笔记。
