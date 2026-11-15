# ART-V2 PixelLab P2-3R 遮罩下半身局部重绘报告

状态：`FAIL — MASKED INPAINT DID NOT CREATE TWO LEGS`

日期：2026-11-15

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r`

起点：`0dfa3b4`

## 1. 输入与遮罩

输入：

```text
art-source/character-v2/pixellab/P2-3R/input-down-soft-lips-64x96.png
SHA-256: 77FB41D39AC16C839246EAAA12FDEC438F270CCE76973FA7E1B20B70E333940B
```

遮罩只覆盖下半身中央裙摆：

```text
x=14..45
y=79..89
64×96 RGBA
遮罩区域 Alpha 255
其他区域 Alpha 0
SHA-256: D77F1B787C6A268B682354F6CAC16F3EF35593D6AC1757426C699DFB61B3D35D
```

遮罩未覆盖脸、头发、头带、鳍耳、手、上身或鲸尾末端。可视化检查见：

```text
art-source/character-v2/pixellab/P2-3R/down-lower-body-mask-preview-8x.png
```

## 2. PixelLab Inpaint

PixelLab 编辑器提供显式 Inpaint 工具。为避免继续在编辑器画布缩放与图层状态中
引入不可审计差异，本轮使用 PixelLab 官方 Classic Inpaint 接口：

```text
POST https://api.pixellab.ai/v2/inpaint
模型模式：Classic
输入：64×96 RGBA
遮罩：黑底白区 PNG
固定 seed：20261115
有效 generation 提交：1
请求尝试：2（第一次因请求结构错误被 422 拒绝，未生成、未计费）
实际消耗：1 generation
```

请求只提交一次，没有执行第二次生成、Edit Image 提示词修补或手工补画。

## 3. 原始结果

```text
art-source/character-v2/pixellab/P2-3R/down-masked-edit-raw.png
64×96
SHA-256: 2A400F3D27392F79316EC4D37AC82CDFBDCEF02D42AE1FCA8EC4ACD518F539C0
```

8× 前后对比：

```text
art-source/character-v2/pixellab/P2-3R/down-masked-edit-preview-8x.png
```

## 4. 审计结果

遮罩边界通过：

```text
遮罩内变化像素：212
遮罩外变化像素：0
遮罩外新增不透明像素：0
遮罩外删除不透明像素：0
```

技术指标：

```text
尺寸：64×96
色板：22（含透明）
Alpha：0/255
半透明像素：0
结果 bbox：(7,27,57,87)
柔和唇色 #C97882：存在
柔和唇色阴影 #A05D63：存在
```

视觉结果：

- 遮罩外角色完全不变；
- 脸、手、鳍耳、上身和鲸尾保持；
- 遮罩内裙摆下缘被裁进并形成深色缺口；
- 但没有出现两条独立短腿；
- 没有 1～2 px 的两腿透明间隔；
- 没有两只可辨认的深蓝短靴；
- 鞋底无法按 `y=88` 检查。

因此 P2-3R 硬性视觉验收失败。

## 5. 停止门

```text
显式遮罩：可用
遮罩外变化：0
down 双腿：FAIL
短靴：FAIL
其余方向：未制作
P3-0 idle：继续锁定
生产接入：未开始
```

按照 A 的任务书，不再进行第二次局部生成，也不切换其他工具。若继续制作，
需要 A 另发任务书，改用 WorkBuddy/Miora 重做“短裙露腿”的高精度角色锚点。

## 6. 回归

```text
.\scripts\test-b7.ps1
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。
