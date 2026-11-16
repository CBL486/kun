# ART-V2 PixelLab P2-3R2 修正遮罩下半身报告

状态：`FAIL — LEG GAP 6 PX, REQUIRED 1–2 PX`

日期：2026-11-16

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r2`

起点：`28268da`

任务书提交：`22ba0fb`

## 1. 根因确认

P2-3R 的遮罩只有：

```text
x=14..45
y=79..89
高度 11 px
```

它只覆盖裙摆最下缘，模型没有空间同时重画裙摆主体、腿和靴子，因此只收缩了
裙摆。P2-3R2 改用完整下半身多边形遮罩。

## 2. 修正遮罩

```text
输入：
art-source/character-v2/pixellab/P2-3R2/input-down-soft-lips-64x96.png
SHA-256: 77FB41D39AC16C839246EAAA12FDEC438F270CCE76973FA7E1B20B70E333940B

遮罩：
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask.png
SHA-256: 72CBDB2C40088C3BE3F17173789D74861AD74B2A0DA8E4E0155BC66E427C825D

可见范围：x=16..47, y=66..90
半开外接框：(16, 66, 48, 91)
高度：25 px
覆盖像素：718
Alpha：0/255
```

遮罩多边形：

```text
(20,66) (43,66) (46,73) (47,85)
(43,90) (22,90) (16,85) (17,73)
```

红色遮罩预览：

```text
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask-preview-8x.png
```

## 3. PixelLab 生成

```text
端点：POST /v2/inpaint-v3
模型：Inpaint v3
seed：20261116
no_background：true
crop_to_mask：false
有效生成请求：1
提交次数：1
实际消耗：10 generations
任务 ID：7f8271e5-b905-4f84-878a-3b6f20a78a07
生成 ID：b99cae13-c6a5-4fcf-9702-d6454dd9a753
生成前余额：1996.9
生成后余额：1986.9
```

没有进行第二次生成，没有使用 Edit Image，没有手工补腿，没有切换工具。

## 4. 原始结果

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-raw.png
64×96
SHA-256: 7AB1EF712E16F2E707A6D5CCEA4F0423629231D19D206B2DB5D41930EEB62A62
```

视觉结果已经出现：

- 两条独立短腿；
- 两只深蓝色短靴；
- 两个鞋底接触边均为 `y=88`；
- 脸、柔唇、头发、鳍耳、上身和鲸尾保持同一角色。

但 Inpaint v3 原始回传同时重映射了遮罩外颜色：

```text
遮罩外变化：1576 pixels
遮罩外删除不透明像素：129
遮罩外新增不透明像素：517
原始色板：37
```

这不符合“遮罩外变化必须为 0”和“总色板不超过 24 色”的硬条件。

## 5. 确定性清理

没有再次生成。B 按技术清理职责执行：

1. 遮罩外全部恢复为输入原像素；
2. 遮罩内颜色映射回原角色已有色板；
3. 保持 Alpha 为 0/255；
4. 不手工补画任何腿、靴、衣物或身体轮廓。

清理结果：

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
SHA-256: 625D0B1E11686BC9BD9217BC20507F3D66CC295E569DCC7A05BB6D06A1D041B6
```

清理后技术指标：

```text
遮罩外变化：0
遮罩内变化：586
总色板：22
Alpha：0/255
半透明像素：0
柔唇 #C97882：存在
柔唇阴影 #A05D63：存在
```

## 6. 硬性验收

通过：

- 遮罩高度 25 px；
- 遮罩覆盖裙摆主体至脚底；
- 遮罩外变化 0；
- 两条独立短腿；
- 两只深蓝短靴；
- 两个鞋底接触边统一在 y=88；
- 总色板 22；
- Alpha 0/255；
- 无手工补画；
- 只提交一次有效生成。

失败：

```text
左腿 bbox：(20,75,26,82)
右腿 bbox：(32,74,38,82)
腿间透明间隔：6 px
任务硬限制：1–2 px
```

因此本轮仍不能通过 P2-3R2。

## 7. 停止门

```text
P2-3R2：FAIL
原因：腿间透明间隔为 6 px，超过 1–2 px 硬限制
第二次 PixelLab 生成：0
Edit Image：0
手工补腿/移动腿：0
P3-0 idle：继续锁定
正式运行时：未修改
```

按照任务书，PixelLab Inpaint 路线到此停止。是否转入 WorkBuddy/Miora 重做
“短裙露腿”角色锚点，等待 A 下发新任务书。

## 8. 证据

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-preview-8x.png
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-metrics.json
art-source/character-v2/pixellab/P2-3R2/api-response.json
art-source/character-v2/pixellab/P2-3R2/job-response.json
art-source/character-v2/pixellab/P2-3R2/credit-log.json
```
