# ART-V2 PixelLab P2-3R5 左手可读性修复报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-16

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r5`

起点：`c655558`

任务书提交：`2e28c79`

## 1. 本轮范围

只修复 down 帧左手、手腕和袖口。没有修改左腿、右腿、靴子、裙摆、鲸尾、脸、
头发、鳍耳或上半身服装。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R4/down-left-skirt-cleaned.png
64×96 RGBA
SHA-256: 4B51182AA44702F47DB84B014B52DF5ADDD3CCA5D961B21177F85D5557D9B9A2
```

## 3. 显式遮罩

允许区域：

```text
x=9..19
y=68..83
```

手部遮罩：

```text
art-source/character-v2/pixellab/P2-3R5/left-hand-mask.png
68 个像素
SHA-256: C20A3C67B9645E63A0DC663B500D291258F3ECAF1E183377DE21D53A97C03DB2
```

遮罩为明确逐行像素集合，仅覆盖手腕、袖口、手掌和紧邻边缘，没有覆盖左腿。

## 4. PixelLab 生成

```text
端点：POST /v2/inpaint-v3
模型：Inpaint v3
seed：20261117
no_background：true
crop_to_mask：false
有效生成请求：1
实际消耗：10 generations
任务 ID：6ed38b07-d4c1-4728-bdaf-3e883b48b310
生成 ID：ea9cd1f8-40d3-4a23-8aba-94c384430f25
生成前余额：1986.9
生成后余额：1976.9
```

没有第二次生成，没有使用 Edit Image，没有手工补出手或手指。

## 5. 原始结果

```text
art-source/character-v2/pixellab/P2-3R5/down-left-hand-raw.png
SHA-256: C11B34E77DA4231A6726F8861E05378B6D0B8105037CA9D86A3901EC1A0EE621
```

Inpaint v3 原始结果改动了遮罩外 20 个像素。按授权后处理：

1. 遮罩外全部恢复为输入原像素；
2. 遮罩内颜色映射回现有角色色板；
3. 排除柔唇颜色，避免手掌出现粉红嘴唇色；
4. 掌内冷蓝色高光映射为现有肤色阴影 `#B5A9BC`；
5. Alpha 保持 0/255。

## 6. 清理结果

```text
art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
64×96 RGBA
SHA-256: 8D8AC191FED1DBC7A6180092E025B159E19D99DC0166532BA1A01DC1DD4E2AC1
```

手部指标：

```text
手部 bbox：(10,69,19,80)
最低点：y=79
手掌肤色宽度：
  y=73：4
  y=74：4
  y=75：5
  y=76：5
  y=77：3
  y=78：3
手部肤色像素：28
白袖口像素：8
允许区域内连通区域：1
手与手臂连续：true
掌形可读：true
圆角/拇指轮廓可读：true
手内柔唇颜色：0
```

在 48×72 下手部不再呈现为细长布条。

## 7. 技术与边界

```text
遮罩内变化像素：51
遮罩外最终变化：0
raw 遮罩外变化：20（已恢复）
总色板：22
Alpha：0/255
半透明像素：0
动画：未开始
正式运行时：未修改
生产数据：未接触
购买/升级：0
```

## 8. 视觉证据

```text
art-source/character-v2/pixellab/P2-3R5/left-hand-mask-preview-16x.png
art-source/character-v2/pixellab/P2-3R5/down-left-hand-diff-16x.png
art-source/character-v2/pixellab/P2-3R5/down-left-hand-grid-32x.png
art-source/character-v2/pixellab/P2-3R5/runtime-48x72-preview-8x.png
```

## 9. 状态

```text
P2-3R5 技术检查：PASS
P2-3R5 用户视觉确认：PENDING
完整四方向：未开始
P3-0 idle：继续锁定
```

## 10. 回归

```powershell
.\scripts\test-b7.ps1
```

结果：

```text
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。
