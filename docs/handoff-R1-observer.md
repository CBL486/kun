# R1 观察者模式与权威 presence 交接

状态：待 Gate 1 审查

日期：2026-11-06

分支：`codex/product-r1-observer`

基线：`848a73ac8efb80c92500b7e7a5d1b004a6aedf65`

## 1. 交付范围

- `/world` 升级为 `rpg-public-world-v2`；
- 新增只读 `agent_presence`、`world.state_revision` 和 `updated_at`；
- 玩家键盘、按钮、地图点击均不能改变角色位置；
- 删除日记、记忆导航、页面和公开 `/memory` 路由；
- 前端按 presence revision 更新目标位置；
- 角色位置使用时间差插值，镜头使用 15% deadzone 和 easing；
- 后台标签页暂停动画循环，恢复时重置时间差并重新获取 presence；
- 图片失败、无 presence、减少动态效果均有回退。

## 2. 数据契约

`GET /world` 返回：

```json
{
  "schema_version": "rpg-public-world-v2",
  "world": {
    "state_revision": 49,
    "updated_at": "2026-11-08T21:30:00+08:00"
  },
  "agent_presence": {
    "character_id": "char_lin_cheng",
    "x": 430.0,
    "y": 338.0,
    "location_id": "loc_dorm",
    "facing": "right",
    "animation": "idle",
    "speed": 0.0,
    "moving": false,
    "updated_at": "2026-11-08T21:30:00+08:00",
    "revision": 49
  }
}
```

公开 API 没有位置写入端点。`LocalWorldStore.update_agent_presence()` 是服务端
行动路径和测试使用的内部适配器；revision 回退返回 `stale_presence_revision`。

`/memory` 已删除。内部记忆数据与 `LocalWorldStore.memory()` 保留给服务端工具和
测试，不进入公开 UI、OpenAPI 或发布投影。

## 3. 测试结果

```text
pwsh -NoProfile -File scripts/test-all.ps1
188 passed, 1 warning
七日 E2E：passed, 49 events, 0 errors, 1 warning
成本对账：bill_matches=true
config-check：issues=[]
release build：189 files
release verify：issues=[]
```

新增 `tests/test_r1_observer.py` 覆盖：

- presence 权威更新和单调 revision；
- 拒绝 revision 回退；
- `/world` 只读；
- 前端无移动键盘/按钮；
- presence、deadzone、translate3d 和后台恢复路径；
- `/memory` 从 OpenAPI 移除。

## 4. 浏览器证据

使用 Edge 无头浏览器访问真实本地 API：

```text
桌面 1440×1000：scrollWidth=1440
手机 390×844：scrollWidth=390
presence revision=world.state_revision=49
移动控件数量=0
移动端导航=5 项
方向键输入后 targetX/targetY 不变
控制台错误=[]
```

截图：

```text
docs/screenshots/r1-observer-desktop.png
docs/screenshots/r1-observer-mobile.png
```

复现脚本：

```powershell
pwsh -NoProfile -File scripts/run-b6-api.ps1
# 将当前 Codex 运行时的 node_modules 加入 NODE_PATH
node scripts/capture-r1-evidence.js
```

## 5. 已知风险

- 当前 presence 初始值来自冻结七日快照，尚未由持续后台时钟推进；
- 现有 Spine 只有 `idle/walk` 和左右翻转，上下朝向与坐下/学习动作属于 R2；
- `/world` 暂用 5 秒有界轮询，实时事件流留给后续集成；
- 浏览器证据使用本机 Edge，CI 尚未安装 Playwright 浏览器依赖。

## 6. 需要 A 做

1. 审查 presence 字段、v2 迁移和公开记忆移除；
2. 合并 `codex/product-r1-observer` 后再让 R2 基于此 presence 接入正式动画；
3. 确认冻结七日快照适配层可在 R5/R7 前替换为持续世界时钟。
