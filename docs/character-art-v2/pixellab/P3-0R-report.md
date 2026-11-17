# ART-V2 PixelLab P3-0R 确定性 Idle 报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-17

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p3-0r-idle`

起点：`ff9b334`

任务书提交：`d70c687`

## 1. 输入

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
256×96 RGBA
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

本轮为零 AI 的确定性像素位移，没有调用 PixelLab 或其他生成服务。

## 2. 动画结构

```text
sheet：256×384
单帧：64×96
方向：down / left / right / up
每方向：4 帧
FPS：5
循环：0 -> 1 -> 2 -> 3 -> 0
```

每方向：

```text
frame 0 = P2-4 静态帧
frame 1 = 次级轮廓向左 1 px
frame 2 = frame 0
frame 3 = 同一轮廓向右 1 px
```

down/left/right 位移鲸尾轮廓，up 位移背面发梢。位移均使用显式像素集合，
只清除源位置并在相邻 1 px 位置写入原像素。

## 3. 输出

```text
art-source/character-v2/pixellab/P3-0R/idle-4dir-4f.png
SHA-256: 2277C5B0B4D4C50F40D0246C87828C16197C4A5AA0F83B8A58E5C0D42D510B69
```

预览：

```text
art-source/character-v2/pixellab/P3-0R/down-proof-4f.png
art-source/character-v2/pixellab/P3-0R/down-proof-preview-8x.webp
art-source/character-v2/pixellab/P3-0R/idle-preview-4x.webp
art-source/character-v2/pixellab/P3-0R/idle-preview-checker-4x.gif
art-source/character-v2/pixellab/P3-0R/idle-contact-sheet.png
```

独立帧：

```text
art-source/character-v2/pixellab/P3-0R/frames/down/0.png ... 3.png
art-source/character-v2/pixellab/P3-0R/frames/left/0.png ... 3.png
art-source/character-v2/pixellab/P3-0R/frames/right/0.png ... 3.png
art-source/character-v2/pixellab/P3-0R/frames/up/0.png ... 3.png
```

WebP 与 GIF 都是 4 帧、5 FPS、无限循环。GIF 使用 `disposal=2` 和固定
透明索引。

## 4. 硬指标

```text
Frame 0 与 P2-4 逐像素一致：true
Frame 2 与 Frame 0 逐像素一致：true
face_region_changed_pixels：全为 0
torso_region_changed_pixels：全为 0
hand_region_changed_pixels：全为 0
leg_region_changed_pixels：全为 0
max_anchor_x_drift：0 px
max_sole_bottom_drift：0 px
鞋底接触边界：四方向全部 y=88
色板：22
Alpha：0/255
半透明像素：0
```

各方向四个 bbox 均保持不变：

```text
down ：(7,27,57,88)
left ：(19,21,58,88)
right：(18,22,62,88)
up   ：(13,22,57,88)
```

次级区域变化：

```text
down：11 px
left：19 px
right：20 px
up：18 px
```

相邻帧变化：

```text
down ：8 / 8 / 7
left ：14 / 14 / 12
right：14 / 14 / 13
up   ：12 / 12 / 12
```

首尾循环变化：

```text
down：7
left：12
right：13
up：12
```

## 5. 地图证据

```text
桌面：1440×1000
手机：390×844
运行时角色：48×72
方向切换横向偏移：0 px
Console errors：0
```

截图包含 down 的 frame 0/1，以及 left/right/up 的 frame 1：

```text
art-source/character-v2/pixellab/P3-0R/map-desktop-idle.png
art-source/character-v2/pixellab/P3-0R/map-mobile-idle.png
art-source/character-v2/pixellab/P3-0R/map-capture-idle.json
```

## 6. 可复现性

```text
character_pixellab_p3_0r_idle_rig.py
character_pixellab_p3_0r_preview.py
character_pixellab_p3_0r_map_capture.py
```

连续运行 rig 两次，输出哈希一致：

```text
2277C5B0B4D4C50F40D0246C87828C16197C4A5AA0F83B8A58E5C0D42D510B69
```

## 7. 预算与边界

```text
AI 生成调用：0
PixelLab 调用：0
generations_used：0
余额保持：1964.9
walk / turn / stop：未开始
正式运行时：未修改
生产数据：未接触
```

## 8. 回归

```text
.\scripts\test-b7.ps1
262 passed, 1 warning

node --check web/app.js
通过
```

## 9. 状态

```text
P3-0R 技术检查：PASS
P3-0R 用户视觉确认：PENDING
P3-1 walk：继续锁定
生产接入：未授权
```
