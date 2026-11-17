# ART-V2 PixelLab P2-3R6 双手比例修复报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-17

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r6`

起点：`1dd7afd`

任务书提交：`baeab28`

## 1. 本轮范围

同时修复 down 帧双手：

- 将 P2-3R5 中过大的左手缩小；
- 补出与右袖口连接、位于鲸尾前方的右手。

没有修改腿、靴、裙摆、脸、头发、鳍耳和鲸尾末端。

## 2. 输入与遮罩

```text
art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
SHA-256: 8D8AC191FED1DBC7A6180092E025B159E19D99DC0166532BA1A01DC1DD4E2AC1

左手区域：x=9..19, y=68..81
右手区域：x=42..55, y=65..82
左手遮罩：80 px
右手遮罩：60 px
两个遮罩分离：是
```

遮罩文件：

```text
art-source/character-v2/pixellab/P2-3R6/left-hand-mask.png
art-source/character-v2/pixellab/P2-3R6/right-hand-mask.png
art-source/character-v2/pixellab/P2-3R6/two-hands-mask.png
art-source/character-v2/pixellab/P2-3R6/two-hands-mask-api.png
```

## 3. PixelLab 生成

```text
端点：POST /v2/inpaint-v3
模型：Inpaint v3
seed：20261118
no_background：true
crop_to_mask：false
有效生成请求：1
实际消耗：10 generations
任务 ID：1ff8755c-bf1f-44b6-93cf-b74a67e9a411
生成 ID：37e184ad-e091-4300-97fc-2feb42e0ee48
生成前余额：1976.9
生成后余额：1966.9
```

没有第二次生成，没有使用 Edit Image，没有手工补出手。

## 4. 生成后清理

原始结果：

```text
art-source/character-v2/pixellab/P2-3R6/down-two-hands-raw.png
SHA-256: 08BEFA0183DB47715D19CB3A3D89F3408F604108981E0291ED8CE1BC3B5FAF41
```

Inpaint v3 原始结果改动了遮罩外 17 个像素。按授权执行：

1. 遮罩外全部恢复为输入原像素；
2. 遮罩内颜色映射回现有 22 色色板；
3. 排除柔唇颜色；
4. Alpha 保持 0/255；
5. 没有手工补画或移动手部。

最终结果：

```text
art-source/character-v2/pixellab/P2-3R6/down-two-hands-cleaned.png
SHA-256: 54F1C7BD7D301577006A093A5EAE9AAA49B786996E36634C3B4B0FA47869E1E9
```

## 5. 双手指标

左手：

```text
整体 bbox：(12,70,17,75)
腕下手部外框：5×3 px
掌心肤色宽度：y72=1, y73=3
白袖口像素：6
与左臂连接：是
```

右手：

```text
整体 bbox：(42,68,46,76)
腕下手部外框：4×5 px
掌心肤色宽度：y71=1, y72=3, y73=3, y74=2
白袖口像素：4
与右臂连接：是
位于鲸尾前方：是
鲸尾末端：保持，未被遮罩覆盖
```

两只手都满足腕下外框不超过 5×5，尺寸接近；左手不再是大圆拳，右手不再是缺失状态。

## 6. 技术与边界

```text
遮罩内变化像素：65
遮罩外最终变化：0
raw 遮罩外变化：17（已恢复）
手内柔唇颜色：0
总色板：22
Alpha：0/255
半透明像素：0
动画：未开始
正式运行时：未修改
生产数据：未接触
购买/升级：0
```

## 7. 视觉证据

```text
art-source/character-v2/pixellab/P2-3R6/two-hands-mask-preview-16x.png
art-source/character-v2/pixellab/P2-3R6/down-two-hands-diff-16x.png
art-source/character-v2/pixellab/P2-3R6/down-two-hands-grid-32x.png
art-source/character-v2/pixellab/P2-3R6/runtime-48x72-preview-8x.png
```

## 8. 状态

```text
P2-3R6 技术检查：PASS
P2-3R6 用户视觉确认：PENDING
P2-4 四方向：继续暂停
P3-0 idle：继续锁定
```

## 9. 回归

```powershell
.\scripts\test-b7.ps1
```

结果：

```text
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。
