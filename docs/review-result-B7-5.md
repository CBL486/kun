# B7.5 美术资源竖切片评审结果

评审人：Agent A

初评日期：2026-10-30

复审日期：2026-11-01

分支：`codex/bx-b7-5-art`

初评提交：`1b7e4dc7d3283829f0b3107088e275b569e700ca`

修复提交：`bbb70bdbb44f35df14a1f99f6455880c6fe77ad4`

最终交付提交：`448a420b0f71677e9861b51546489c0a004e7e46`

## 1. 结论

复审结论：**通过，允许合并 main，允许进入 B8。**

初评发现的 P0 阻断问题已经修复。实际 Web、Spine Runtime、静态资源路由、Manifest 哈希、自动化测试和视觉证据均已重新提交，并能在当前分支实际运行。

## 2. 初评问题与修复结果

| 初评问题 | 修复结果 |
| --- | --- |
| Web 仍是 B7 旧版 | 已提交完整 Web 集成 |
| 缺少 `web/spine-player.js` | 已提交 |
| 缺少 Spine WebGL Runtime 和许可证 | 已提交 |
| Manifest 中 Spine JSON/Atlas 哈希不一致 | 已重新生成，当前 0 个资源不一致 |
| 测试实际 109 passed / 2 failed | 当前 113 passed |
| 干净目录无法执行正式测试 | 默认测试已不再强制重建私密素材 |
| `/assets` 静态路由缺失 | `app/main.py` 已新增 `/assets -> assets/` |
| 食堂 NPC 身份错误 | 高原已映射到食堂，五名角色映射已补全 |
| 截图不能从提交复现 | 截图记录 source commit/tree，最终提交只追加证据 |

## 3. 自动化证据

### 3.1 Python 测试

实际执行：

```text
113 passed, 1 warning in 11.90s
```

唯一警告为：

```text
Starlette/httpx TestClient deprecation warning
```

不影响 B7.5 功能和安全性验收。

### 3.2 JavaScript 语法

```text
node --check web/app.js          -> 通过
node --check web/spine-player.js -> 通过
```

### 3.3 Manifest 独立审计

独立扫描结果：

```text
assets: 30
source_packs: 6
issues: 0
web/spine-player.js: exists
```

所有资源的文件、字节数和 SHA-256 均与 `assets/manifest.json` 一致。

### 3.4 角色场景映射

```text
林澄 -> 宿舍、教学楼 -> Spine idle/walk
陈岚 -> 青禾书院 -> static
苏晚 -> 教学楼 -> static
高原 -> 食堂 -> static
顾言 -> 河边步道 -> static
```

食堂身份错误已修正。

## 4. 浏览器实测

从最终分支实际启动 `app.main:app`，使用 Edge 无头浏览器检查：

### 桌面 1440×1000

- `.world-map-stage` 存在；
- `window.qingheSpinePlayer` 存在；
- 六个地点标签完整；
- `scrollWidth = innerWidth = 1440`；
- 页面控制台错误为 0；
- 向右移动后角色 x 坐标变化；
- 镜头 transform 从 `translate3d(0px, 0px, 0px)` 变为 `translate3d(-246.335px, 0px, 0px)`；
- Spine 移动时切换为 `walk`；
- 停止后切换为 `idle`；
- 点击宿舍可打开内部场景，图片为 `/assets/interiors/dorm.webp`。

### 手机 390×844

- `.world-map-stage` 存在；
- `window.qingheSpinePlayer` 存在；
- 底部导航 7 项；
- `scrollWidth = innerWidth = 390`；
- 页面控制台错误为 0。

### 静态资源

以下资源均返回 HTTP 200：

```text
/assets/maps/town-map-world.webp
/assets/characters/lin_cheng.webp
/assets/interiors/dorm.webp
/assets/spine/lin_cheng.json
/assets/spine/lin_cheng.atlas
/assets/spine/lin_cheng.png
/assets/icons/map.png
/assets/icons/settings.png
/static/vendor/spine-webgl.min.js
/static/spine-player.js
```

## 5. 视觉证据

截图和机器记录位于：

```text
docs/screenshots/b75-desktop.png
docs/screenshots/b75-mobile.png
docs/screenshots/b75-interior-desktop.png
docs/screenshots/b75-interior-mobile.png
docs/screenshots/b75-spine-walk-desktop.png
docs/screenshots/b75-spine-walk-mobile.png
docs/screenshots/b75-town-east-desktop.png
docs/screenshots/b75-river-walk-desktop.png
docs/screenshots/b75-map-moved-desktop.png
docs/screenshots/b75-map-moved-mobile.png
docs/screenshots/b75-interiors-overview.png
docs/art-budget-b7-5.json
```

`art-budget-b7-5.json` 记录：

```text
source_commit = bbb70bdbb44f35df14a1f99f6455880c6fe77ad4
source_tree   = 9faa892fc553f84c1849ceeb99a4e09cf4f66e3c
worktree_dirty = false
desktop transfer bytes < 250000
mobile transfer bytes < 200000
```

最终提交 `448a420` 相对 `bbb70bd` 只修改文档、截图和验证记录，不修改 Web 运行时。

## 6. 验收入口与依赖说明

B 提供的默认测试入口：

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

该入口默认不再要求 `out/b75-source-extracted`，测试已提交的运行资源。

浏览器视觉脚本依赖 Python Playwright：

```text
requirements-b75-dev.txt
  Pillow>=11,<13
  playwright>=1.50,<2
```

当前 A 环境没有预装 Python Playwright，因此官方包装脚本在视觉阶段停在 `ModuleNotFoundError: playwright`。本轮使用同一 Edge 浏览器和 Playwright 运行时完成了等价的页面交互、截图、资源、镜头和 Spine 检查，结果全部通过。

这不是 B7.5 的代码失败，但 B8 开始前应在 README 或测试脚本中补充安装命令，避免新环境误判：

```powershell
python -m pip install -r requirements-b75-dev.txt
```

## 7. 通过后的允许范围

已通过：

- 横向 2400×900 小镇世界；
- 六地点地图与内部手账；
- 主智能体和四名 NPC 的资源映射；
- 林澄 Spine `idle` / `walk`；
- 本地 UI 图标和状态图标；
- 图片失败回退；
- 桌面和手机布局；
- 素材授权清单和原始素材不入库规则。

接受的有意限制：

- 四名 NPC 目前只有头像和静态场景帧，没有独立 Spine 行走模型；
- 林澄当前只有 `idle` 和 `walk` 两段动作；
- Spine Trial 仅用于本地预览，正式发布前需要正式许可证重导出；
- 购买/授权凭证和最终公开署名仍需在 G2 前补齐。

这些限制不阻断 B7.5，但继续作为 B8/G2 风险登记。

## 8. 合并决定

```text
B7.5 复审：PASS
允许合并 codex/bx-b7-5-art 到 main
下一批：B8 调度、幂等与崩溃恢复
```

B 不操作服务器；服务器部署仍由 A 独占执行。