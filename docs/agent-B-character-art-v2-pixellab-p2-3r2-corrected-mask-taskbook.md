# ART-V2 PixelLab P2-3R2 修正遮罩下半身任务书

状态：仅授权 down 单帧修正遮罩验证；最多一次生成
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r2`
起点：`28268da`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮目的

P2-3R 的遮罩只覆盖 `y=79..89`，高度不足，模型只收缩了裙摆下缘，没有空间生成腿和鞋。

本轮只修正遮罩结构，再用一次 down 单帧 Inpaint 验证：

```text
能否在裙摆主体至脚底的完整区域内生成两条腿和两只短靴
```

不做其他三个方向，不做动画，不做生产接入。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R/input-down-soft-lips-64x96.png
SHA-256: 77FB41D39AC16C839246EAAA12FDEC438F270CCE76973FA7E1B20B70E333940B
```

必须保留：

- 脸、眼睛和柔唇；
- 蓝发、头带和鲸鳍耳；
- 上身服装、围裙上半部、双臂和手；
- 鲸尾主体与腰扣；
- 64×96 画布、透明背景和现有色板语义。

## 3. 修正遮罩

创建：

```text
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask.png
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask-api.png
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask-preview-8x.png
```

要求：

```text
64×96 RGBA
遮罩编辑区域 Alpha 255
其他区域 Alpha 0
只允许 0/255
```

遮罩必须覆盖完整的下半身裙摆和拟生成区域，不能只盖最低边缘。

推荐使用以下固定多边形，最终外接框应为：

```text
x=16..48
y=66..90
```

推荐多边形点序：

```text
(20,66)
(43,66)
(46,73)
(47,85)
(43,90)
(22,90)
(16,85)
(17,73)
```

允许 B 为避开手和鲸尾末端做 1～2 px 安全性微调，但必须：

- 不覆盖脸、眼睛、头发、头带、鳍耳；
- 不覆盖手臂和手；
- 尽量不覆盖鲸尾末端；
- 覆盖至少 70% 的裙摆下半段；
- 覆盖裙摆下缘至 y=89；
- 垂直高度不得低于 20 px；
- 遮罩外所有像素必须在结果中保持不变。

遮罩只定义编辑范围，不允许在里面手工画腿。

## 4. 生成规则

工具：

```text
PixelLab 官方显式 Inpaint
模型：当前订阅内可用的 Standard / V3 Inpaint
输入：input-down-soft-lips-64x96.png
遮罩：down-lower-body-mask-api.png
提交次数：1
固定 seed：20261116
```

如果只能使用 Classic Inpaint：

- 允许使用；
- 必须记录模型名；
- 仍然只提交一次；
- 不接受“只收缩裙摆”的结果。

提示词：

```text
Replace the entire masked lower skirt area with a coherent short chibi
lower body for the same blue-haired whale girl. Shorten the navy skirt hem
to mid-thigh while preserving the white apron and outfit design above it.
Generate exactly two clearly separated short legs with pale skin and two
dark navy ankle boots. Keep a 1-pixel transparent gap between the legs.
Both boot soles must align at y=88. Preserve the whale tail outside the mask.
Keep the face, soft rose lips, hair, headband, fin ears, hands and upper body
exactly unchanged. Pixel art, no antialiasing, binary alpha only.
```

禁止：

- 手工补腿；
- 无遮罩编辑；
- 第二次生成；
- 用一条宽腿代替两条腿；
- 改脸、柔唇、鳍耳、手或上身；
- 删除鲸尾；
- 只收缩裙摆不做腿；
- 把鞋画到 y=88 以外；
- 修改运行时。

## 5. 输出

```text
art-source/character-v2/pixellab/P2-3R2/
  input-down-soft-lips-64x96.png
  down-lower-body-mask.png
  down-lower-body-mask-api.png
  down-lower-body-mask-preview-8x.png
  down-masked-edit-raw.png
  down-masked-edit-preview-8x.png
  down-masked-edit-metrics.json
  mask-metrics.json
  credit-log.json
  api-response.json

scripts/
  character_pixellab_p2_3r2_prepare.py
  character_pixellab_p2_3r2_masked_audit.py

docs/character-art-v2/pixellab/
  P2-3R2-report.md
```

## 6. 硬性验收

必须全部通过：

- 遮罩高度至少 20 px；
- 遮罩覆盖裙摆下半段和脚底区域；
- 遮罩外变化像素为 0；
- 结果出现两条独立短腿；
- 两腿之间有 1～2 px 透明间隔；
- 两只深蓝短靴可辨认；
- 两个鞋底接触边统一在 y=88；
- 腿与裙摆连接自然；
- 脸、柔唇、鳍耳、手、上身和鲸尾保持不变；
- Alpha 0/255；
- 总色板不超过 24 色；
- 只提交一次有效生成；
- 不手工补画。

以下任一情况直接失败：

- 只收缩裙摆，没有腿；
- 只有一条腿；
- 两腿粘连；
- 鞋悬空或错位；
- 遮罩外发生变化；
- 身份或柔唇被改；
- 进行第二次生成；
- 切换到其他工具。

## 7. 失败后的固定路线

如果 P2-3R2 仍然失败：

```text
停止 PixelLab Inpaint 路线
不得再追加局部生成
由 WorkBuddy/Miora 基于原 1024 角色锚点重做“短裙露腿”正/侧/背四视图
A 验收新锚点后，才允许 B 用 PixelLab 重新做四方向
```

该 WorkBuddy 路线必须另行下发任务书，B 不得自行切换。

## 8. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-3R 明确失败：遮罩只有 y=79..89，太短，模型只收裙摆，没有生成腿。不要继续原遮罩，也不要重复原提示词。

创建 codex/character-art-pixellab-p2-3r2，从 28268da 开始，只做 down 单帧。

使用输入：art-source/character-v2/pixellab/P2-3R/input-down-soft-lips-64x96.png
创建覆盖 x=16..48、y=66..90 的多边形遮罩，完整包住裙摆下半段至脚底，不能只覆盖最下缘。
用 PixelLab 显式 Inpaint，只提交一次；目标是两条分开的短腿、两只深蓝短靴、鞋底 y=88、腿间 1px 透明间隔。
遮罩外变化必须为 0。脸、柔唇、鳍耳、手、上身和鲸尾必须保持不变。
不要手工画腿，不要无遮罩编辑，不要第二次生成，不要切换工具。

如果结果仍然只是收裙摆，停止并报告；push 后等 A。下一步将改走 WorkBuddy/Miora 角色锚点重做路线。
```
