# B7.5 修复任务单

日期：2026-10-30

当前分支：`codex/bx-b7-5-art`

当前提交：`1b7e4dc7d3283829f0b3107088e275b569e700ca`

结论：**BLOCKED，不合并 main，等待 B 修复后复审。**

## 一、问题总览

| 优先级 | 问题 | 当前影响 |
| --- | --- | --- |
| P0 | 实际 Web 没有提交 | 截图中的页面无法从提交运行出来 |
| P0 | Spine 播放器和 Runtime 缺失 | 角色动画无法加载，测试直接失败 |
| P0 | 测试实际失败 | 2 项失败，不是交接中声称的 112 项全通过 |
| P0 | Manifest 哈希不一致 | Spine JSON/Atlas 与清单记录不匹配 |
| P0 | 干净目录无法运行正式测试 | 资产构建依赖未提供的原始素材目录 |
| P0 | `/assets` 静态路由未验证 | 新素材可能无法被浏览器加载 |
| P1 | NPC 身份映射错误 | 食堂使用苏晚，但设定角色是高原 |
| P1 | 截图不是从已提交页面生成 | 视觉证据不可复现 |

## 二、P0：必须修复

### 1. 提交真正的 Web 集成

当前提交没有修改以下实际运行文件：

```text
web/index.html
web/app.js
web/styles.css
web/spine-player.js
web/vendor/spine-webgl.min.js
web/vendor/SPINE-RUNTIMES-LICENSE.txt
```

从提交 `1b7e4dc` 启动页面后实测：

```text
.world-map-stage       不存在
window.qingheSpinePlayer 不存在
```

页面仍然是 B7 的旧占位地图。

B 必须把截图所依赖的全部 Web 代码提交，并保证从提交运行出的页面与截图一致。

### 2. 补齐 Spine 运行时

必须提交：

```text
web/spine-player.js
web/vendor/spine-webgl.min.js
web/vendor/SPINE-RUNTIMES-LICENSE.txt
```

验收时会检查：

```powershell
node --check web/spine-player.js
```

以及浏览器中的：

```javascript
window.qingheSpinePlayer.getState()
```

### 3. 修正 Manifest 与资产哈希

独立扫描发现 30 个资源中至少有 2 个导出记录不匹配：

```text
assets/spine/lin_cheng.json
  实际 4921 bytes / 清单 5185 bytes
assets/spine/lin_cheng.atlas
  实际 490 bytes / 清单 523 bytes
```

另外 Spine Runtime 记录指向两个不存在的文件。

B 必须重新生成并一起提交：

```text
assets/spine/lin_cheng.json
assets/spine/lin_cheng.atlas
assets/spine/lin_cheng.png
assets/manifest.json
```

要求：

- 所有资源文件存在；
- 文件字节数匹配；
- SHA-256 匹配；
- Runtime 文件存在；
- 不允许 manifest 使用旧构建的统计数据。

### 4. 修正测试结果和测试入口

当前实际运行 `pytest`：

```text
109 passed, 2 failed, 1 warning
```

交接写的是 112 项通过，但 `tests/test_b75_assets.py` 实际只有 10 个 B7.5 测试函数，按当前基线累计应为 111 项。

B 需要：

- 修复两项失败；
- 重新运行完整测试；
- 在交接中写真实 output；
- 不复制旧测试结果；
- 如果新增测试，再说明新增数量和文件名。

当前正式入口：

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

在干净目录第一步就因缺少 `out/b75-source-extracted` 失败。

B 需要把构建和测试拆开，或提供可执行的私密素材前置条件。建议：

```text
scripts/build-b75-assets.ps1
  只在 B/A 设置 B75_SOURCE_ROOT 时执行，用于重建资源

scripts/test-b75.ps1
  默认只测试已提交资源、Web、Spine 和截图

私密源素材
  仍不进入公开仓库
```

这样 A 可以在干净仓库验收，B 也可以在私有环境重建。

### 5. 增加 `/assets/...` 静态服务

新运行资源位于项目根目录 `assets/`，但当前 `app/main.py` 只提供：

```text
/static -> web/
```

B 必须选择并验证一种方式：

- 在 FastAPI 中增加根 `assets/` 的静态挂载；或
- 把运行资源放到 `web/` 已挂载目录下，并同步修改 manifest 路径。

浏览器实际访问以下资源时必须返回 200，而不是 404：

```text
/assets/maps/town-map-world.webp
/assets/characters/lin_cheng.webp
/assets/interiors/dorm.webp
/assets/spine/lin_cheng.json
/assets/spine/lin_cheng.atlas
/assets/spine/lin_cheng.png
```

### 6. 增加“Web 真的接入了”的回归测试

新增测试至少检查：

- `web/index.html` 存在 `.world-map-stage` 或等价实际地图节点；
- `web/app.js` 包含 `qingheSpinePlayer` 初始化路径；
- `web/vendor` 中两个 Spine 文件存在；
- `/assets/...` 返回 200；
- 页面不是 B7 的纯占位地图；
- 截图生成入口使用的页面和提交一致。

## 三、P1：质量修复

### 1. 修正 NPC 身份映射

B 的交接已承认：

- 食堂使用了“苏晚”的角色帧，但设定角色是高原；
- 顾言尚无稳定室内出场位置；
- 四名 NPC 没有独立行走模型。

本轮至少要求：

- 食堂角色改为高原；
- 苏晚只出现在符合设定的地点；
- 为顾言指定稳定出场地点；
- 在 manifest 或角色映射文档中列出：
  `character_id -> portrait -> static frame -> scene -> animation state`。

四名 NPC 的独立 Spine 可以在后续批次完成，但身份不能错。

### 2. 重新生成截图

截图必须从修复后的精确提交生成，并在交接中写明：

```text
截图生成提交：
截图生成命令：
桌面视口：1440×1000
手机视口：390×844
浏览器控制台错误：0
```

不能继续使用未提交工作树中的截图。

## 四、复审前必须提交的交接格式

```text
任务 ID：B7.5 修复版
分支：
新提交哈希：
改动文件：
Web 运行文件：
Spine Runtime 文件：
Manifest 审计结果：
测试命令：
测试真实输出：
原始素材前置条件：
截图生成提交：
桌面/手机截图路径：
已知风险：
需要 A 在服务器执行的动作：无
```

## 五、A 的复审判定标准

只有全部满足才可变为“通过”：

- [ ] 实际 Web 文件已提交
- [ ] `web/spine-player.js` 存在
- [ ] `web/vendor/spine-webgl.min.js` 存在
- [ ] `web/vendor/SPINE-RUNTIMES-LICENSE.txt` 存在
- [ ] `node --check web/app.js`
- [ ] `node --check web/spine-player.js`
- [ ] `pytest` 无失败
- [ ] Manifest 30/30 文件和哈希一致
- [ ] `/assets/...` 全部返回 200
- [ ] 页面实际出现 `.world-map-stage`
- [ ] 页面实际出现 `window.qingheSpinePlayer`
- [ ] 桌面 1440×1000 无横向溢出
- [ ] 手机 390×844 无横向溢出
- [ ] 地图移动、镜头跟随、室内弹窗正常
- [ ] Spine `idle` / `walk` 正常切换
- [ ] 食堂 NPC 身份正确
- [ ] 截图来自当前提交
- [ ] 公开仓库没有原始付费素材包、密钥或真实数据

## 六、边界

- B 不能登录服务器、VNC、RDP、SSH 或生产数据库。
- B 只提交代码、资产、测试、截图和交接文档。
- A 负责最终合并、生产资源和部署。
- 本次修复不需要 A 操作服务器。