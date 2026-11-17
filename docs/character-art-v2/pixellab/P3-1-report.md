# ART-V2 PixelLab P3-1 Walk 报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-17

执行人：Agent B

授权依据：用户确认 P3-0R idle 通过，并要求开始 P3-1。

分支：`codex/character-art-pixellab-p3-1-walk`

起点：`6d34656`

## 1. 实现方式

本轮为零 AI 的确定性像素动画：

```text
输入：art-source/character-v2/pixellab/P3-0R/idle-4dir-4f.png
SHA-256: 2277C5B0B4D4C50F40D0246C87828C16197C4A5AA0F83B8A58E5C0D42D510B69
```

以 P3-0R 每个方向的静止帧为基准，对腿和靴的位置做确定性的水平位移与最多
1 px 的抬脚，并附加 1 px 的尾巴/发梢延迟摆动。

六帧相位：

```text
F0 contact
F1 down
F2 pass
F3 contact
F4 down
F5 pass
```

## 2. 输出

```text
art-source/character-v2/pixellab/P3-1/walk-4dir-6f.png
384×384 RGBA
SHA-256: B2778093916657A445757C3CFB31091A11570B09C16EEC46743748AF2314CDED

方向：down / left / right / up
每方向：6 帧
单帧：64×96
FPS：9
循环：0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0
```

独立帧：

```text
art-source/character-v2/pixellab/P3-1/frames/down/0.png ... 5.png
art-source/character-v2/pixellab/P3-1/frames/left/0.png ... 5.png
art-source/character-v2/pixellab/P3-1/frames/right/0.png ... 5.png
art-source/character-v2/pixellab/P3-1/frames/up/0.png ... 5.png
```

预览：

```text
art-source/character-v2/pixellab/P3-1/walk-preview-4x.webp
art-source/character-v2/pixellab/P3-1/walk-preview-checker-4x.gif
art-source/character-v2/pixellab/P3-1/walk-contact-sheet.png
```

## 3. 技术验收

```text
sheet：384×384
单帧：64×96
每方向帧数：6
FPS：9
四方向均非空：true
色板：22
Alpha：0/255
半透明像素：0
```

脚底与锚点：

```text
最大鞋底基线漂移：1 px
最大脚底锚点横向漂移：1 px
```

各方向鞋底底部行：

```text
down ：87 / 88 / 87 / 87 / 88 / 87
left ：87 / 88 / 86 / 87 / 88 / 87
right：87 / 88 / 86 / 87 / 88 / 87
up   ：87 / 88 / 87 / 87 / 88 / 87
```

`86` 是 pass 相的 1 px 抬脚，参考基线为 87；所有帧均在允许的 ±1 px 内。

## 4. 面部与主体

相邻帧审计中：

```text
face changes：全部 0
hand changes：全部 0
torso changes：全部 0
```

角色脸、眼睛、柔唇、双手、躯干和身份像素均未重绘。变化只位于腿部/靴子、
尾巴或发梢。

## 5. 地图证据

```text
桌面：1440×1000
手机：390×844
运行时角色：48×72
方向切换横向偏移：0 px
Console errors：0
```

截图包含 down 的 contact、down、pass 三个相位，以及 left/right/up 的 pass 相位：

```text
art-source/character-v2/pixellab/P3-1/map-desktop-walk.png
art-source/character-v2/pixellab/P3-1/map-mobile-walk.png
art-source/character-v2/pixellab/P3-1/map-capture-walk.json
```

## 6. 可复现性

```text
character_pixellab_p3_1_walk.py
character_pixellab_p3_1_preview.py
character_pixellab_p3_1_map_capture.py
```

脚本不使用网络、AI 或随机数。

## 7. 边界

```text
AI 生成调用：0
PixelLab 调用：0
generations_used：0
turn / stop：未开始
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

警告为既有 Starlette/httpx 弃用提示。

## 9. 状态

```text
P3-1 技术检查：PASS
P3-1 用户视觉确认：PENDING
turn / stop：继续锁定
生产接入：未授权
```
