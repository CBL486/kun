# ART-V2 PixelLab P2-2 四方向静态清理任务书

状态：授权执行；零 AI 生成；完成后停止等待验收
编写人：Agent A
执行人：Agent B
审查人：Agent A
目标分支：`codex/character-art-pixellab-p2`
建议起点：`22ebab6` 或该分支最新提交
生产边界：不修改生产、不部署、不接触 VNC/RDP/SSH、生产 `.env`、API Key、数据库或真实用户数据

## 1. 本轮目标

把已通过的 PixelLab 原始四方向结果清理成真正可进入游戏的静态精灵表：

```text
PixelLab 原始四方向
-> 固定 64×96 单帧
-> 统一脚底锚点
-> 21～24 色
-> Alpha 0/255
-> 256×96 四方向精灵表
-> 真实地图桌面/手机证据
-> Agent A 验收
-> 用户视觉确认
```

本轮不允许再次调用 PixelLab 生成、Edit Image、Inpainting 或其他 AI 生图工具。额度消耗必须为 0。

## 2. 唯一输入

必须只使用以下已存在的原始资产：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-raw.png
art-source/character-v2/pixellab/P2/sprite-4dir-raw.json
art-source/character-v2/pixellab/P2/metrics-4dir-raw.json
art-source/character-v2/pixellab/P2/lip-fixed-64x96.png
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

不采用以下失败产物：

```text
art-source/character-v2/pixellab/P2/north-tail-edit-attempt.png
art-source/character-v2/pixellab/P2/north-tail-edit-attempt-preview-8x.png
```

## 3. 已冻结的视觉决定

```text
角色身份：PixelLab 四方向原始输出
嘴唇：沿用 P2-0 的自然玫瑰色
南、西、东：必须保留鲸尾
北向：保留后发、服装背面、腰后蝴蝶结和脚部
北向鲸尾：允许被身体/裙摆自然遮挡
```

不得重新设计角色，不得改变服装结构，不得手工补尾巴，不得把左右方向改成镜像。

## 4. 精确裁切规则

原始表：

```text
尺寸：384×96
单格：96×96
顺序：south, west, east, north
```

每格统一裁切：

```text
x：20 <= x < 84
y：0 <= y < 96
输出：64×96
```

必须使用统一窗口，不得按每帧完整 bbox 单独居中。原因是鲸尾会让左右和正面的 bbox 不对称；按 bbox 居中会造成角色在换方向时横向跳动。

裁切后目标方向顺序：

```text
south -> down
west  -> left
east  -> right
north -> up
```

最终表顺序必须固定为 `down, left, right, up`。

## 5. 锚点与对齐规则

```text
单帧：64×96
脚底接触边：y=88
水平基准：保留统一裁切后的原始横向位置，不做逐帧重新构图
```

执行要求：

1. 以角色脚部/接触阴影底边作为垂直基准；
2. 通过整帧平移把四方向脚底接触边统一到 `y=88`；
3. 不允许拉伸、挤压、旋转或局部变形；
4. 记录每方向脚底锚点 x，并检查相邻方向无大于 2 px 的视觉跳变；
5. 如果 x 对齐需要修正，只能整帧平移，不能改身体；
6. 不得裁掉鳍耳、头发、手、鲸尾或裙摆。

原图 bbox 参考：

```text
south：(27,27,77,88)
west： (34,26,75,90)
east： (22,28,63,92)
north：(29,26,67,90)
```

统一 x=20..84 裁切后，四个 bbox 都必须完整落在帧内，且至少保留 1 px 透明边。east 的鲸尾最靠左，必须重点检查是否触边。

## 6. 色板清理规则

```text
总色板目标：21～24 色（含透明）
Alpha：只允许 0 或 255
半透明像素：0
抗锯齿：禁止
渐变：禁止
抖动：禁止
```

只允许做确定性的调色板合并，不允许：

- 用新的 AI 结果替换；
- 直接套用与角色不匹配的外部色板；
- 改变皮肤、头发、服装、玫瑰唇色的语义；
- 删除嘴部修正；
- 把透明边缘变成白色或黑色底。

必须保留以下语义色：

```text
皮肤亮/中/暗
头发深/中/亮
鳍耳浅蓝
服装深蓝/白
围裙冰白
玫瑰唇主色/阴影
鲸尾深蓝与高光
轮廓深色
```

交付中记录：

```text
原始色数：29
最终色数
颜色合并映射
因调色板合并而变化的总像素数
每个语义色的最终 RGB
```

如果无法在 24 色以内保持嘴唇、鳍耳和鲸尾可读，停止并报告，不允许通过重画解决。

## 7. 必须交付

```text
art-source/character-v2/pixellab/P2/
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  sprite-preview-checker-4x.png
  metrics-4dir-clean.json
  visual-review.json
  map-preview-4dir.html
  map-desktop-4dir.png
  map-mobile-4dir.png
  credit-log.json

scripts/
  character_pixellab_p2_cleanup.py

docs/character-art-v2/pixellab/
  P2-2-report.md
```

`character_pixellab_p2_cleanup.py` 必须满足：

- 从原始 `sprite-4dir-raw.png` 一键可复现；
- 固定裁切、锚点、方向和调色板规则；
- 重复运行结果哈希一致；
- 不使用网络、AI API 或 PixelLab；
- 可输出 metrics 与预览；
- 不允许把逻辑藏在不可审计的手工步骤里。

## 8. metrics 最低字段

`metrics-4dir-clean.json` 至少包含：

```json
{
  "status": "ready-for-a-review",
  "source_sheet": "art-source/character-v2/pixellab/P2/sprite-4dir-raw.png",
  "source_sha256": "02B6C148B3139932F4D6B703F7E1B1C4B40ECAD557DE357B515912C533FEB65A",
  "output_sheet": "art-source/character-v2/pixellab/P2/sprite-4dir-cleaned.png",
  "sheet_size": [256, 96],
  "frame_size": [64, 96],
  "direction_order": ["down", "left", "right", "up"],
  "crop_windows": {},
  "foot_baseline_y": 88,
  "foot_anchor_x": {},
  "colors": 0,
  "alpha_values": [0, 255],
  "semi_transparent_pixels": 0,
  "direction_bboxes": {},
  "changed_pixels_by_palette_reduction": 0,
  "output_sha256": "",
  "generation_count": 0,
  "pixellab_calls": 0
}
```

实际值必须填写，不得保留示例 0。

## 9. 视觉与游戏证据

必须交两类证据。

### 9.1 精灵证据

`sprite-preview-4x.png`：

- 4× 最近邻放大；
- 标明 `DOWN / LEFT / RIGHT / UP`；
- 使用深色、浅色和棋盘格三种背景检查透明边缘；
- 四个方向不得触边；
- 北向不得出现人工补出的尾巴。

`sprite-preview-checker-4x.png`：

- 透明棋盘格背景；
- 不经过平滑缩放；
- 可清楚检查白边、底色和 Alpha。

### 9.2 真实地图证据

基于现有 P1 地图预览，新建 `map-preview-4dir.html`，不得改正式游戏页面。

```text
桌面：1440×1000
手机：390×844
运行时显示：48×72
角色：sprite-4dir-cleaned.png
```

检查：

- 48×72 下脸部、鳍耳、服装和鲸尾仍可读；
- 在草地、道路、浅色地砖上无白底或方块边；
- 角色脚底贴合地面；
- 四方向切换不横向跳动；
- Console errors = 0；
- 截图中不是把概念图贴在大图下面。

## 10. 视觉验收表

`visual-review.json` 必须逐项填写：

```json
{
  "accepted": false,
  "checks": {
    "identity_matches_reference": "fail",
    "down_direction": "fail",
    "left_direction": "fail",
    "right_direction": "fail",
    "up_back_readable": "fail",
    "north_tail_occlusion_expected": "pass",
    "alpha_clean": "fail",
    "palette_within_limit": "fail",
    "foot_baseline_aligned": "fail",
    "no_edge_clipping": "fail",
    "map_readable_48x72": "fail",
    "console_errors_zero": "fail"
  },
  "reviewer_notes": "B 必须根据实际检查填写；未人工检查不得改为 true。"
}
```

B 只能在自己完成实际检查后把各项改为 `pass`，但最终 `accepted` 仍由 Agent A 和用户确认。

## 11. 回归与提交

必须执行：

```powershell
.\scripts\test-b7.ps1
```

记录通过数、警告和控制台错误。只提交艺术候选、脚本和证据，不修改正式运行时。

提交要求：

- 只提交本轮相关文件；
- 不提交临时目录、浏览器缓存、API Key、日志中的敏感信息；
- 不提交仓库根目录的意外 `$null` 文件；
- 提交信息建议：`art: complete PixelLab P2-2 four-direction cleanup`；
- push `codex/character-art-pixellab-p2` 后停止，等待 Agent A 验收。

## 12. 停止门

出现以下任一情况必须停止并报告：

- 任一方向被裁切；
- 四方向脚底基线无法在 2 px 容差内统一；
- 角色身份、鳍耳、服装、鲸尾或唇色发生明显变化；
- 必须重画角色才能满足色板；
- 48×72 下不可读；
- 需要再次调用 PixelLab 或其他 AI；
- 需要修改生产代码或接触生产环境。

```text
P2-2 未通过：不进入动画
用户未确认视觉：不进入动画
P2-2 通过：只授权 P3-0 idle 测试，不自动批量做 walk
```

## 13. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-1R 已被 A 判定 FAIL，停止所有尾巴 Inpainting 和提示词修补；P2-1 的北向鲸尾按自然遮挡规则通过。现在只做 P2-2 四方向静态清理，零 AI 生成。

从 codex/character-art-pixellab-p2 的 22ebab6 或最新提交继续。

只使用：
art-source/character-v2/pixellab/P2/sprite-4dir-raw.png
art-source/character-v2/pixellab/P2/sprite-4dir-raw.json
art-source/character-v2/pixellab/P2/metrics-4dir-raw.json
art-source/character-v2/pixellab/P2/lip-fixed-64x96.png

每格从 96×96 统一裁切 x=20..84、y=0..96 到 64×96；
方向顺序映射为 south->down、west->left、east->right、north->up；
脚底接触边统一到 y=88；
色板收敛到 21～24 色含透明；
Alpha 只能为 0/255；
输出 256×96 精灵表、4×预览、透明棋盘格预览、
1440×1000 与 390×844 的 48×72 真实地图截图和完整 metrics。
写可复现的 character_pixellab_p2_cleanup.py，记录颜色合并和哈希，跑 test-b7。

不要调用 PixelLab，不要重画，不要补尾巴，不要改生产。
push 后停止，等 A 验收和用户视觉确认。
```
