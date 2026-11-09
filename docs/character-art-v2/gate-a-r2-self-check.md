# ART-V2 Gate A R2 自检与交接

状态：待 Agent A 复审

日期：2026-11-09

分支：`codex/character-art-v2-r2`

基线：`aa2c908`（含 Gate A R1 复审结论）

审查门：Gate A R2。未通过前不进入 Gate B。

## 1. 对 R1 未通过项的修正

| R1 问题 | R2 修正 |
| --- | --- |
| 三个方向是同一生成器变体 | A 为长外套，B 为短外套和腰带，C 为不对称长衣摆；发量、腿长和鳍饰比例分别调整 |
| 使用 polygon / ellipse / filter 决定角色 | 最终角色只由 `64×96` 字符像素矩阵编译；提交中不保留几何角色绘制器 |
| 头部和头发过大 | 总高固定 72 px，脸部和身体比例按 00B 上限重画 |
| up 只是一块后发 | up 增加后发分层、外套背面、腰带或鲸尾扣、双腿和鞋底；三套 up 轮廓均与 down 不同 |
| 服装层次不可读 | 每套都保留外套、冰白内搭、裙装/下摆和暖金扣饰的独立色层 |
| 没有 00B | 已补 `identity-lock.md` 与 `asset-map.json` |
| 没有黑白轮廓证据 | 每套提供 `silhouette-4dir.png` 和四张独立轮廓图 |

## 2. 三个方向

| 方向 | 造型 | 主要可读结构 |
| --- | --- | --- |
| A 叙事长外套 | 长发、长外套、双长衣摆 | 外套最长，发量最大，轮廓柔软 |
| B 海玻璃学院 | 肩长发、大鳍、短外套、金腰带、短裙、长腿 | 外套最短，身体和腿部空间最大 |
| C 潮汐图形 | 角状发束、不对称长衣摆、深色宽轮廓 | 色块最少，外轮廓最强，衣摆一长一短 |

三套不能通过只换颜色互相转换。

## 3. 手工像素源

每个方向目录包含：

```text
source/
  palette.json
  down.txt
  left.txt
  right.txt
  up.txt
  down.png
  left.png
  right.png
  up.png
  down-rgba.png
  left-rgba.png
  right-rgba.png
  up-rgba.png
```

`.txt` 是明确的 64×96 字符像素矩阵，`.` 为透明，其余字符通过
`palette.json` 映射为固定 HEX。`source/*.png` 是无损索引色 PNG；
`*-rgba.png` 是运行检查用的 RGBA 展开。

最终打包脚本 `scripts/pack_character_gate_a_r2.py` 只读取矩阵、上色、
拼表和生成检查图，不负责设计五官、头发或衣服轮廓。

## 4. 技术指标

| 方向 | 有效 RGBA 色数 | 四方向宽度 | 高度 | 半透明 |
| --- | ---: | ---: | ---: | ---: |
| A | 21 | 39 px | 72 px | 0 |
| B | 21 | 39 px | 72 px | 0 |
| C | 22 | 40 px | 72 px | 0 |

共同指标：

```text
精灵表：256×96
逻辑帧：64×96
运行时显示：48×72
Alpha：0/255
脚底基线：88
采样：最近邻
```

## 5. 真实地图证据

每套方案交付：

```text
map-desktop.png
map-mobile.png
map-desktop-{down|left|right|up}.png
map-mobile-{down|left|right|up}.png
```

均在真实 `web/index.html` 中按 48×72 显示。会话使用隔离临时目录和 fake key，
不连接真实 DeepSeek 或生产数据。

索引：

```text
docs/character-art-v2/gate-a-r2-map-evidence.json
```

## 6. 黑白轮廓证据

```text
art-source/character-v2/gate-a-r2/{a|b|c}/silhouette-4dir.png
art-source/character-v2/gate-a-r2/{a|b|c}/silhouette-{down|left|right|up}.png
```

自动化测试要求：

- 四个朝向的轮廓互不相同；
- A/B/C 三个方向的轮廓差异均超过 100 个像素；
- 左右方向不仅内容不同，也不能是水平镜像。

## 7. 测试

定向测试：

```powershell
$py = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = ((Resolve-Path .b6-deps).Path + [IO.Path]::PathSeparator + (Resolve-Path .).Path)
& $py -m pytest tests/test_character_gate_a_r2.py -q
```

结果：

```text
Gate A R2 定向测试：4 passed
完整 pytest：268 passed, 1 warning
真实地图截图：24/24
浏览器控制台错误：0
```

测试会逐字符还原 `.txt` 矩阵，并与索引 PNG、RGBA 展开和四方向表逐字节比较，
避免“文本源与实际导出不一致”。

## 8. 积分与工具边界

```text
历史 00A + R1 Gate A：24
R2：0
未新增模型生成图
```

当前执行环境未发现 Pixelorama/bridge，因此使用可直接审查的字符像素矩阵作为
可编辑源，并通过无损脚本完成索引色编译、拼表和截图。角色造型不再由几何图元决定。

## 9. 已知风险

1. 三套仍共享林澄的基本身份色和鳍饰意象，这是设计约束，不是同模换色；
   外套长度、发量、腿长和衣摆方向已经分别冻结。
2. `up` 方向通过外套背面、腰带/扣饰和后发分层增强身份，但仍需 Agent A
   在真实地图尺寸下最终选择。
3. 本轮只完成 Gate A R2 的静态四方向证明，没有制作动作表和表情包。
4. 像素作者稿仍需 Agent A 判断是否达到产品气质，不能用自动化测试替代美术审查。

## 10. 需要 Agent A 决策

1. 从 A/B/C 中选择唯一方向，或明确淘汰全部方向；
2. 若通过，Gate B 只制作被选中方向，不并行扩展三套；
3. 在 Gate A R2 通过前，不制作 1024 主视觉、表情或动作资源。
