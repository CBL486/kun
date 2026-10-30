# B7.5 美术资源竖切片评审结果

评审人：Agent A

评审日期：2026-10-30

分支：`codex/bx-b7-5-art`

提交：`1b7e4dc7d3283829f0b3107088e275b569e700ca`

基线：`bd56080218ecb653b5b62ea3b08daedd15c303d2`

结论：**不通过，暂不合并 main，等待 B 修复后复审。**

可执行修复清单：[7-5-fix-request.md](b7-5-fix-request.md)

## 1. 结论说明

B7.5 的美术素材方向已经有明显进展：横向小镇地图、六处室内场景、角色头像、UI 图标、Spine 演示资源和授权清单都已出现。视觉截图本身也具备可用的基础风格。

但当前提交不能作为可运行交付验收，原因是：

- 实际 Web 没有接入本批美术；
- 截图对应的工作树状态没有提交；
- 自动化测试实际失败；
- Spine 运行文件和清单记录不完整；
- 在干净目录中无法按提供的测试入口复现。

因此本轮既不能合并，也不能声称 B7.5 已完成。

## 2. 阻断问题

### 2.1 实际网页仍是 B7 旧版

提交 `1b7e4dc` 的变更文件不包含任何 `web/` 文件。`web/index.html`、`web/app.js`、`web/styles.css` 仍然是 B7 的旧观察站页面。

从该提交启动 `app.main:app` 后实测：

```text
world-map-stage = false
qingheSpinePlayer = false
页面仍显示 B7 占位地图和占位头像
```

因此，`docs/screenshots/b75-desktop.png` 和 `docs/screenshots/b75-mobile.png` 展示的页面，不是当前提交能够运行出来的页面。

B7.5 的截图不能替代已提交的 Web 集成。B 需要把截图所依赖的页面代码、脚本和资源引用一并提交。

### 2.2 缺少 Spine 运行时和播放器

当前提交缺少：

```text
web/spine-player.js
web/vendor/spine-webgl.min.js
web/vendor/SPINE-RUNTIMES-LICENSE.txt
```

其中 `web/spine-player.js` 被 `scripts/test-b75.ps1` 和 `scripts/check_b75_visual.py` 直接引用，但文件不存在。`web/vendor` 目录也不存在。

这说明 Spine 动画截图同样不能从当前提交复现。

### 2.3 测试结果与交接记录不一致

B 的交接文档声称：

```text
112 项通过
```

实际执行 `pytest`：

```text
109 passed, 2 failed, 1 warning
```

失败项：

1. `test_manifest_checksums_and_files_match`
   - `assets/spine/lin_cheng.json` 实际 4921 字节，清单记录 5185 字节；
   - SHA-256 也不一致。
2. `test_spine_assets_and_runtime_are_complete`
   - 缺少 `web/vendor/spine-webgl.min.js`。

`tests/test_b75_assets.py` 实际只有 10 个 B7.5 测试函数；若没有遗漏测试文件，累计应为 111 项，而不是 112 项。B 必须给出真实测试输出和修正后的计数。

### 2.4 正式测试入口不能在干净目录复现

执行：

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

第一步构建资产即失败：

```text
FileNotFoundError: 缺少原始素材文件
out/b75-source-extracted/modern_exteriors/...
```

原始素材不进入公开仓库本身是正确规则，但交付必须提供至少一种可复现路径：

- A/B 私有目录中存在明确的 `B75_SOURCE_ROOT`；或
- 提供一个只验证已提交运行资源的测试入口；或
- 将构建与测试分开，并记录原始素材的私密前置条件。

目前文档虽然提到了 `B75_SOURCE_ROOT`，但没有让 A 在干净仓库中验证 B7.5 的完整方式。

### 2.5 Manifest 仍未自洽

独立审计 `assets/manifest.json` 后，30 个 asset 中有以下记录不一致：

```text
assets/spine/lin_cheng.json
  实际 4921 bytes / 清单 5185 bytes
assets/spine/lin_cheng.atlas
  实际 490 bytes / 清单 523 bytes
```

另外，Spine runtime 记录指向两个不存在的文件：

```text
web/vendor/spine-webgl.min.js
web/vendor/SPINE-RUNTIMES-LICENSE.txt
```

B 需要重新运行 Spine 资产生成步骤，把生成的 JSON、Atlas、纹理和 manifest 一起提交，确保 30/30 资源的大小和 SHA-256 全部匹配。

### 2.6 资产服务路径没有完成验证

当前 `app/main.py` 只挂载：

```text
/static -> web/
```

而本批运行资源位于项目根目录 `assets/`。如果新页面使用 `/assets/...`，还需要明确增加同源静态资源挂载，或者把所有运行资源放到已挂载目录下。现有提交既没有 Web 接入，也没有对应的服务端静态路由修改。

### 2.7 已知角色映射问题仍未关闭

B 的交接文档承认：

- 食堂当前使用“苏晚”对应角色帧，但设定角色是高原；
- 顾言还没有稳定室内出场位置；
- 四名 NPC 没有独立行走模型。

其中角色身份映射属于可见的事实错误，不应带着“已知问题”直接进入 B7.5 通过状态。至少应修正食堂人物映射，并在 manifest 或角色映射文档中逐项核对五名角色。

## 3. 已通过或可保留的部分

以下工作并非全部无效，可以保留并在修复后复审：

- `assets/manifest.json` 已建立 30 个资源记录；
- 记录了 6 个来源包及来源哈希；
- 地图、六处室内场景、五名角色头像和 UI 图标资源存在；
- 素材授权审计文档说明了来源、署名和原始素材不入库规则；
- B7.5 截图的视觉风格比 B7 更好，可以作为后续正式实现的方向参考；
- 室内场景总览和室内弹窗截图具备可继续打磨的基础。

这些是可保留的资产成果，但不等同于可运行、可复现、可合并的 Web 交付。

## 4. B 必须完成的修复

### 必须修复

1. 提交实际 Web 集成：
   - `web/index.html`
   - `web/app.js`
   - `web/styles.css`
   - `web/spine-player.js`
   - `web/vendor/spine-webgl.min.js`
   - `web/vendor/SPINE-RUNTIMES-LICENSE.txt`
2. 增加 `/assets` 或等价静态资源路由，并验证浏览器实际返回 200。
3. 重新生成并提交 Spine JSON、Atlas、纹理和 manifest，保证大小与 SHA-256 全部一致。
4. 让 `scripts/test-b75.ps1` 在干净目录中给出明确可执行的验证路径，或拆成“预构建测试”和“带私有源素材重建测试”两个入口。
5. 修正食堂等场景的 NPC 身份映射，并补上五名角色与场景的映射表。
6. 用修复后的精确提交重新生成桌面和手机截图，不可继续使用未提交工作树截图。

### 复审门槛

B 修复后必须提供：

```text
任务 ID：
分支：
提交哈希：
改动文件：
测试命令：
测试结果：
原始素材前置条件：
实际页面 URL：
截图生成提交：
已知风险：
```

复审时 A 将重新验证：

- `pytest` 真实通过数；
- `node --check web/app.js`；
- `node --check web/spine-player.js`；
- manifest 30/30 文件、大小和 SHA-256；
- `/assets/...` 图片 HTTP 200；
- 桌面 1440×1000；
- 手机 390×844；
- 地图、室内、角色移动、Spine `idle`/`walk`；
- 截图与分支提交一致；
- 公开仓库中不包含原始付费素材包、密钥和真实数据。

## 5. 当前处理

- **暂不合并 `codex/bx-b7-5-art` 到 main。**
- B7.5 资源可作为草稿保留在同一分支。
- B7.5 不作为生产部署输入。
- B 修复并推送新提交后，A 从新提交重新验收。

```text
评审结论：BLOCKED
下一状态：等待 B 提交修复版
```