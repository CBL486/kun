# ART-V2 Gate A R1 自检与交接

状态：待 Agent A 审查

执行日期：2026-11-09

分支：`codex/character-art-v2-r1`

基线：`6a6a3c9065da1c116a9940e7cc69c0da0e79527c`

审查门：只到 Gate A R1，不进入 Gate B

## 1. 本轮结论

三个方向都提交了可直接进入游戏地图的 64×96 四方向原生像素证明。角色在真实
`web/index.html` 中按 48×72 运行时尺寸显示。1024 图只作为参考，不作为 Gate A
通过证据。

本文件不宣布 Gate A 通过；由 Agent A 在 48×72 地图尺寸和 4× 最近邻预览中选择
唯一方向。

## 2. 交付矩阵

| 方向 | 风格 | 唯一 RGBA 色数 | 半透明像素 | 四方向 | 桌面/手机 |
| --- | --- | ---: | ---: | --- | --- |
| A | 深海童话：长发型与分层衣摆 | 23（含透明） | 0 | down/left/right/up | 1440×1000 / 390×844 |
| B | 海玻璃学院：肩长发、大鳍饰、简洁轮廓 | 22（含透明） | 0 | down/left/right/up | 1440×1000 / 390×844 |
| C | 潮汐海报：角色骨点硬朗、2 px 外轮廓 | 23（含透明） | 0 | down/left/right/up | 1440×1000 / 390×844 |

三套共同硬指标：

```text
精灵表：256×96 RGBA
单帧：64×96
运行时显示：48×72
Alpha：仅 0/255
脚底基线：88
渲染：最近邻
半透明/抗锯齿像素：0
角色总宽：39～40 px
角色总高：64～72 px
```

每个方向目录都包含任务书要求的：

```text
hero-reference.png
sprite-4dir.png
sprite-down-1x.png
sprite-preview-4x.png
palette.png
metrics.json
map-desktop.png
map-mobile.png
```

另外保留 `map-{desktop|mobile}-{down|left|right|up}.png`，让审查者可以逐方向核对，
不把四方向拼在一张角色表里冒充地图证据。

## 3. 真实游戏页证据

截图不是把立绘贴在地图下方，也不是用 CSS 缩放 1024 图。采集流程是：

1. 使用隔离临时目录、fake validator 和默认 Persona 启动本地 API；
2. 打开真实 `web/index.html`；
3. 在地图内找到 `#map-player-sprite`；
4. 只在浏览器内存中替换候选帧；
5. 保持实际地图层的 `.map-player` 尺寸为 48×72；
6. 对 down、left、right、up 分别截取桌面和手机页面；
7. 校验角色矩形位于真实地图舞台内且控制台错误为 0。

复现命令：

```powershell
$py = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = (Resolve-Path .b6-deps).Path
& $py scripts/capture_character_gate_a_r1_maps.py
```

证据索引：

```text
docs/character-art-v2/gate-a-r1-map-evidence.json
```

## 4. 参考图边界

三张 `hero-reference.png` 均为 1024×1024 RGB 原生像素参考板。参考板直接使用
同方向 64×96 四方向源图排版，不再是另一套 AI 插画，因此不会出现“参考图与
游戏小人不是同一个角色”的问题。参考板只用于查看服装、配色和四方向关系，
不进入运行时。

旧版带 AIGC 角标的候选已从最终资源树替换。四方向精灵、参考板、色板、预览和
地图截图均来自本机原生像素代码或真实浏览器采集。

## 5. 自动化自检

新增：

```text
tests/test_character_gate_a_r1.py
scripts/build_character_gate_a_r1.py
scripts/capture_character_gate_a_r1_maps.py
```

测试覆盖：

- 任务书要求的 8 个交付文件全部存在；
- 精灵表、单帧和运行时尺寸正确；
- 有效色数在 16～24（含透明）；
- 角色总宽 32～40 px；
- 角色总高 64～72 px；
- Alpha 只有 0/255，半透明和抗锯齿像素为 0；
- 单帧非空且主体不触边；
- 1× 图与四方向表首帧逐字节一致；
- 4× 图确为最近邻放大；
- 左右方向既不相同，也不是简单水平镜像；
- 3 个方向 × 2 个视口 × 4 个朝向共 24 张真实页面截图；
- 玩家矩形在真实地图舞台内，且大小为 48×72；
- 浏览器控制台错误为 0。

运行命令：

```powershell
$py = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = ((Resolve-Path .b6-deps).Path + [IO.Path]::PathSeparator + (Resolve-Path .).Path)
& $py -m pytest tests/test_character_gate_a_r1.py -q
```

本轮完整回归结果：

```text
2 passed（Gate A R1 定向测试）
264 passed, 1 warning（完整 pytest）
warning 为项目现有 fastapi.testclient 第三方弃用提示
```

## 6. 积分

上一轮已提交的记录：

```text
00A：4
旧 Gate A：20
已用合计：24
Gate A R1 最多再使用：96
```

R1 的原生像素重绘、参考板、色板、指标和真实页面截图消耗小云雀积分：0。
本轮没有新增模型生成图，因此不存在未知扣点。

## 7. 重新提交自检表

```text
[x] 从最新 origin/main 创建 codex/character-art-v2-r1。
[x] 没有覆盖或回退 docs/agent-B-character-art-v2-taskbook.md。
[x] 提交了 3 个方向的 64×96 四方向静态精灵。
[x] 每个方向都有 RGBA、透明、整数像素网格。
[x] 每个运行时精灵不超过 24 色。
[x] 每个运行时精灵 Alpha 只有 0/255。
[x] 没有把 1024 大图直接缩成 64×96。
[x] 在 48×72 实际尺寸检查了角色。
[x] 在 4× 预览中检查了像素簇。
[x] 在真实游戏地图上截了桌面和手机图。
[x] 没有把立绘贴在地图截图下方冒充游戏内验证。
[x] 带 AIGC 元数据/角标的参考图没有进入运行时。
[x] 记录了已知历史和本轮积分口径。
[x] 明确区分参考图与运行时图。
```

## 8. 已知风险与待 A 决策

1. 三个方向都以地图小人的 48×72 可读性为主，1024 参考板不代替游戏内截图。
2. 本轮只证明四方向静态可游戏化，不包含最终 idle/walk/turn/stop 动画。
3. 当前执行环境未发现 Pixelorama/bridge，原生编辑源保存在
   `art-source/character-v2/gate-a-r1/{a|b|c}/source/`。
4. 需要 Agent A 选择一个方向，或明确淘汰全部方向并说明必须修改的轮廓/色板项；
   未选择前 B 不进入 Gate B。
