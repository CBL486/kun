# B7.5 修复版交接

状态：修复完成，等待 A 复审

日期：2026-10-30

分支：`codex/bx-b7-5-art`

修复前提交：`1b7e4dc7d3283829f0b3107088e275b569e700ca`

修复代码提交：`bbb70bdbb44f35df14a1f99f6455880c6fe77ad4`

## 1. P0 修复

### Web 与 Spine Runtime

实际运行所需的 Web 文件均已提交：

```text
web/index.html
web/app.js
web/styles.css
web/spine-player.js
web/vendor/spine-webgl.min.js
web/vendor/SPINE-RUNTIMES-LICENSE.txt
```

页面包含 `.world-map-stage`、`#world-plane`、`#map-player` 和
`#map-player-canvas`。`web/app.js` 初始化 `window.qingheSpinePlayer`，
Spine `idle` 与 `walk` 会随地图移动状态切换。

### 静态资源路由

`app/main.py` 同时提供：

```text
/static -> web/
/assets -> assets/
```

测试已实际请求地图、角色、建筑、室内、头像、Spine 和图标资源，全部返回 200。

### Manifest 与字节一致性

- 构建脚本以 LF 写出 Manifest、Spine JSON 和 Atlas；
- `.gitattributes` 禁止这三个生成文本文件在检出时发生换行转换；
- Manifest 共 30 个资源、51 个导出文件；
- 字节数、SHA-256、Runtime 文件和许可证文件全部匹配；
- 干净检出后重新审计仍为 `all_exports_match=true`。

关键实际文件尺寸：

```text
assets/spine/lin_cheng.json    4921 bytes
assets/spine/lin_cheng.atlas    490 bytes
```

### 测试入口

`scripts/test-b75.ps1` 默认只测试已提交资源和 Web，不再强制重建私密素材。

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

需要重建时，必须显式指向私密素材目录：

```powershell
$env:B75_SOURCE_ROOT = "D:\private\b75-source-extracted"
pwsh -NoProfile -File scripts/build-b75-assets.ps1
pwsh -NoProfile -File scripts/test-b75.ps1 -Rebuild
```

### 回归测试

新增测试检查：

- Web 地图节点、Spine 播放器初始化和本地 Runtime 文件存在；
- `/static/...` 与 `/assets/...` 返回 200；
- Spine JSON/Atlas 哈希与 Manifest 一致；
- NPC 头像、静态帧裁切、场景和动画状态映射一致；
- 视觉报告包含生成提交、源码树、工作树状态和生成命令；
- 室内家具不越界、不重叠，关键窗与地毯使用完整裁切。

## 2. P1 角色映射

| 角色 | 静态帧裁切 | 稳定场景 | 动画 |
| --- | --- | --- | --- |
| 林澄 | `(48, 0, 48, 96)` | 宿舍、教学楼 | Spine `idle` / `walk` |
| 陈岚 | `(192, 0, 48, 96)` | 青禾书院 | 静态 |
| 苏晚 | `(336, 0, 48, 96)` | 教学楼 | 静态 |
| 高原 | `(48, 96, 48, 96)` | 食堂 | 静态 |
| 顾言 | `(336, 192, 48, 96)` | 河边步道 | 静态 |

同一映射写入 `assets/manifest.json` 的 `character_scene_map`，并由
`tests/test_b75_assets.py` 校验。

## 3. 干净目录验证

验证方式：

1. 从修复提交创建新的本地 clone；
2. 确认 clone 中不存在 `out/b75-source-extracted`；
3. 确认 clone 中不存在仓库内 `.b6-deps`；
4. 仅使用外部已安装的 Python/Playwright 依赖运行正式测试；
5. 从 clone 当前提交生成截图。

验证结果：

```text
113 passed, 1 warning in 12.54s
```

唯一警告为 `StarletteDeprecationWarning: Using httpx with starlette.testclient
is deprecated`，不影响测试通过。

其他结果：

- `node --check web/app.js`：通过；
- `node --check web/spine-player.js`：通过；
- 桌面 1440×1000：无横向溢出，控制台错误 0；
- 手机 390×844：无横向溢出，控制台错误 0；
- 地图移动、镜头跟随、室内弹窗正常；
- Spine `idle` / `walk` 正常切换；
- 建筑图片失败回退验证通过。

## 4. 截图证据

截图生成提交：

```text
bbb70bdbb44f35df14a1f99f6455880c6fe77ad4
```

截图生成命令：

```powershell
pwsh -NoProfile -File scripts/check-b75-visual.ps1
```

生成时源码树：

```text
9faa892fc553f84c1849ceeb99a4e09cf4f66e3c
```

生成前工作树：干净

桌面/手机截图：

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
```

机器可读验证记录：

```text
docs/art-budget-b7-5.json
```

最终截图证据提交只追加上述截图、总览和验证记录；Web 与运行时文件保持与
`bbb70bd` 相同。

## 5. 已知限制

- 陈岚、苏晚、高原、顾言目前只有头像和静态场景帧，没有独立 Spine 行走模型。
- 林澄的 Spine Runtime 已完整，但当前骨架只有 `idle` 与 `walk` 两个动作。
- Spine 数据由 Spine 4.3 兼容 JSON 生成；Spine Trial 不允许正式保存工程和导出动画。
- 生产发布前仍需补齐各素材包购买/授权凭证和正式 Spine Editor 许可证。
- `StarletteDeprecationWarning` 属于依赖升级项，不阻塞本轮复审。

## 6. 交接字段

```text
任务 ID：B7.5 修复版
分支：codex/bx-b7-5-art
新提交哈希：bbb70bdbb44f35df14a1f99f6455880c6fe77ad4（修复代码）
改动文件：app/main.py、web/、assets/、spine/、scripts/、tests/、
          README.md、docs/art-pipeline.md、docs/art-budget-b7-5.json、
          docs/screenshots/、docs/handoff-B7-5-interiors.md、.gitattributes
Web 运行文件：web/index.html、web/app.js、web/styles.css
Spine Runtime 文件：web/spine-player.js、web/vendor/spine-webgl.min.js、
                     web/vendor/SPINE-RUNTIMES-LICENSE.txt
Manifest 审计结果：30 个资源 / 51 个导出全部存在，字节和 SHA-256 匹配
测试命令：pwsh -NoProfile -File scripts/test-b75.ps1
测试真实输出：113 passed, 1 warning in 12.54s
原始素材前置条件：正式测试不需要；重建资源才需要 B75_SOURCE_ROOT
截图生成提交：bbb70bdbb44f35df14a1f99f6455880c6fe77ad4
桌面/手机截图路径：docs/screenshots/b75-desktop.png、
                    docs/screenshots/b75-mobile.png
已知风险：四名 NPC 无独立行走模型；Spine Trial 需在发布前替换正式导出
需要 A 在服务器执行的动作：无
```
