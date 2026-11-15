# ART-V2 PixelLab P2-2 四方向静态清理报告

状态：`READY FOR A REVIEW AND USER VISUAL CONFIRMATION`

日期：2026-11-15

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2`

建议起点：`22ebab6`

本轮 PixelLab generations：`0`

PixelLab calls：`0`

## 1. 输入与冻结决定

唯一生成来源：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-raw.png
SHA-256: 02B6C148B3139932F4D6B703F7E1B1C4B40ECAD557DE357B515912C533FEB65A
```

未采用 P2-1R 失败修补结果，没有调用 PixelLab、AI API、Inpainting 或
任何其他生成工具。

## 2. 固定裁切与方向映射

四格统一从原始 `96×96` 帧裁切：

```text
x = 20..84
y = 0..96
输出 = 64×96
```

方向映射：

```text
south -> down
west  -> left
east  -> right
north -> up
```

最终精灵表：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-cleaned.png
256×96
```

输出 SHA-256：

```text
ACFFDB829384987DA361150F82CC036F66C0847B16C81C55705061A4AFD55DB8
```

## 3. 锚点

脚底接触边全部统一为：

```text
y = 88
```

最终包围盒：

```text
down： (7,27,57,88)
left： (13,24,54,88)
right：(2,24,43,88)
up：   (9,24,47,88)
```

脚底锚点 `x`：

```text
down：26.5
left：28.5
right：27.0
up：28.0
```

相邻方向最大脚底锚点差为 `2.0 px`，符合不超过 `2 px` 的要求。

只有 `left` 做了 `-1 px` 整帧水平校正；其余方向保留统一裁切后的位置。
没有任何拉伸、旋转、局部变形或逐帧重新构图。

## 4. 色板

原始总色板：`29`。

最终总色板：`24`，其中不透明色 `23`。

确定性合并：

| 原色 | 目标色 | 像素数 |
| --- | --- | ---: |
| `#BB6C79` | `#B85F6C` | 13 |
| `#A39BAF` | `#B5A9BC` | 19 |
| `#B1BEE0` | `#BAC8DD` | 61 |
| `#477FBC` | `#3B76AE` | 151 |
| `#151520` | `#191927` | 149 |

因调色板合并而变化的总像素：`393`。

玫瑰唇主色 `#B85F6C` 与阴影 `#8D4654` 均保留。

Alpha 仅允许：

```text
0 / 255
```

半透明像素：`0`。

## 5. 精灵证据

三背景 4× 预览：

```text
art-source/character-v2/pixellab/P2/sprite-preview-4x.png
```

透明棋盘格 4× 预览：

```text
art-source/character-v2/pixellab/P2/sprite-preview-checker-4x.png
```

检查结果：

- down/left/right/up 四方向均未触边；
- 最小透明边距为 `2 px`，位于 right 帧左侧；
- down、left、right 的鲸尾可读；
- up 的后发、背面服装、腰后蝴蝶结和脚部可读；
- up 的鲸尾按 A 已批准的自然遮挡规则处理，没有人工补尾巴；
- 白色背景与棋盘格下没有底色污染或半透明彩边。

## 6. 地图证据

预览页：

```text
art-source/character-v2/pixellab/P2/map-preview-4dir.html
```

桌面：

```text
art-source/character-v2/pixellab/P2/map-desktop-4dir.png
1440×1000
```

手机：

```text
art-source/character-v2/pixellab/P2/map-mobile-4dir.png
390×844
```

浏览器实测：

```text
角色显示尺寸：48×72
四方向切换水平位移：0 px
Console errors：0
```

方向按钮仅用于静态预览检查，不构成玩家控制角色的运行时功能。

## 7. 可复现脚本

图像清理：

```text
scripts/character_pixellab_p2_cleanup.py
```

地图截图：

```text
scripts/character_pixellab_p2_map_capture.py
```

清理脚本不使用网络、AI API 或 PixelLab；连续运行得到相同输出哈希。

## 8. 回归

项目标准回归：

```text
.\scripts\test-b7.ps1
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。

## 9. 验收状态

`visual-review.json` 中 B 可确认的技术与视觉检查均填写为 `pass`。

最终字段保持：

```json
{
  "accepted": false
}
```

原因：最终审美接受和是否进入 P3-0 idle 动画仍由 Agent A 与用户确认。

## 10. 停止门

```text
P2-2 技术清理：READY FOR A REVIEW
动画：未开始
生产接入：未开始
下一阶段：等待 A 验收与用户视觉确认
```
