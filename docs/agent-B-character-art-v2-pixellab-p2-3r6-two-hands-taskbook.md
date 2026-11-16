# ART-V2 PixelLab P2-3R6 双手比例修复任务书

状态：授权执行；最多一次双手遮罩重绘；P2-4 暂停
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r6`
起点：`1dd7afd`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮目标

同时修复 down 帧双手：

1. 缩小左手，解决手腕以下过大、像圆拳的问题；
2. 增加缺失的右手，使其与右臂/袖口连接并自然位于鲸尾前方。

只处理双手，不改变腿、靴、裙摆、脸、头发、鳍耳和鲸尾主体。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
SHA-256: 8D8AC191FED1DBC7A6180092E025B159E19D99DC0166532BA1A01DC1DD4E2AC1
```

身份参考：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

只参考双手在角色比例中的大小和位置，不整体缩放角色。

## 3. 双手目标尺寸

两只手必须使用同一套小比例，而不是左右各自一套夸张造型。

```text
手腕宽度：1～2 px
掌心皮肤宽度：2～3 px
掌心高度：2～3 px
拇指或圆角：最多 1 px
白袖口：宽度 2～3 px，高度 1 px
手腕以下手部外框：最大 5×5 px
手部最低点：不晚于 y=80
```

禁止：

- 大圆拳；
- 球形手；
- 大手套；
- 长布条；
- 细长手指；
- 一只手明显大于另一只；
- 手与手臂断开；
- 右手浮空。

## 4. 左右手位置

### 左手

只允许编辑：

```text
x=9..19
y=68..81
```

必须缩小当前左手，保留与左臂连续的白袖口。

### 右手

只允许编辑：

```text
x=42..55
y=65..82
```

目标位置：

- 从右侧上臂/袖口向下连接；
- 手位于鲸尾前方；
- 在 48×72 下仍可见 2～3 px 肤色和 1 px 白袖口；
- 不得把鲸尾改画成手，也不得让手消失在鲸尾后面。

允许右手轮廓遮挡鲸尾的少量像素，但遮罩外鲸尾必须保持。

## 5. 遮罩

创建两个独立遮罩区域：

```text
art-source/character-v2/pixellab/P2-3R6/left-hand-mask.png
art-source/character-v2/pixellab/P2-3R6/right-hand-mask.png
art-source/character-v2/pixellab/P2-3R6/two-hands-mask.png
art-source/character-v2/pixellab/P2-3R6/two-hands-mask-api.png
art-source/character-v2/pixellab/P2-3R6/two-hands-mask-preview-16x.png
```

要求：

- 64×96 RGBA；
- 只覆盖双手、袖口和必要的手腕连接边缘；
- 左侧不覆盖左腿；
- 右侧不覆盖腿和鲸尾末端；
- 两个遮罩保持分离；
- Alpha 只允许 0/255；
- 不能整块清空双手区域后再靠手工画图。

## 6. 生成

```text
工具：PixelLab Inpaint v3
输入：down-left-hand-cleaned.png
遮罩：two-hands-mask-api.png
提交次数：1
seed：20261118
no_background：true
crop_to_mask：false
```

提示词：

```text
Repair both hands of the same blue-haired chibi whale maid.

Left hand: shrink the current oversized rounded hand into a compact chibi hand.
Keep it connected to the existing left wrist and 1-pixel white cuff. Palm must
be only 2-3 pixels wide and 2-3 pixels tall, with at most a 1-pixel thumb or
rounded contour. The complete hand below the cuff must fit within a 5x5 pixel
area.

Right hand: add the missing right hand and white wrist cuff connected to the
right arm. Place the compact right hand in front of the whale tail, using the
same 2-3 pixel palm and 1-pixel cuff scale. It must remain visible at 48x72.

Both hands must be small, rounded and readable, not fists, gloves, spheres,
long strips or oversized blobs. Preserve outside-mask pixels exactly: face,
lips, hair, fin ears, outfit, skirt, legs, boots, tail main silhouette and
palette. Pixel art, binary alpha, no antialiasing.
```

如果当前界面只能使用 Classic Inpaint：

- 允许；
- 记录模型；
- 仍只提交一次；
- 不接受大手或缺失右手结果。

## 7. 生成后清理

Inpaint v3 可能改变遮罩外像素，必须：

1. 遮罩外全部恢复为输入原像素；
2. 遮罩内颜色映射回现有 22 色角色色板；
3. 不允许把手掌生成成柔唇色；
4. Alpha 保持 0/255；
5. 不手工修改手型；
6. 只允许双手遮罩内发生变化。

## 8. 输出

```text
art-source/character-v2/pixellab/P2-3R6/
  input-down-left-hand-cleaned.png
  left-hand-mask.png
  right-hand-mask.png
  two-hands-mask.png
  two-hands-mask-api.png
  two-hands-mask-preview-16x.png
  down-two-hands-raw.png
  down-two-hands-cleaned.png
  down-two-hands-diff-16x.png
  down-two-hands-grid-32x.png
  runtime-48x72-preview-8x.png
  metrics.json
  credit-log.json
  api-response.json
  job-response.json

scripts/
  character_pixellab_p2_3r6_two_hands_cleanup.py

docs/character-art-v2/pixellab/
  P2-3R6-report.md
```

## 9. 视觉证据

`down-two-hands-grid-32x.png` 必须标出：

- 左手 cuff；
- 左手掌心；
- 右手 cuff；
- 右手掌心；
- 两手外框；
- 手部最低点；
- 右侧鲸尾保留区域。

`down-two-hands-diff-16x.png` 必须包含：

```text
BEFORE | MASK | AFTER | DIFF
```

在 48×72 预览中要能同时看见两只小手，但手不能抢过脸和腿的视觉比重。

## 10. metrics

```text
input_sha256
output_sha256
left_hand_bbox
right_hand_bbox
left_hand_outer_size
right_hand_outer_size
left_palm_skin_width
right_palm_skin_width
left_cuff_pixels
right_cuff_pixels
left_hand_connected
right_hand_connected
right_hand_in_front_of_tail
changed_pixels_outside_masks
colors
alpha_values
semi_transparent_pixels
generation_submissions
generations_used
animation_started
production_modified
```

## 11. 硬性验收

必须通过：

- 左手外框小于等于 5×5（腕以下）；
- 左手掌心宽度 2～3 px；
- 右手存在且外框小于等于 5×5（腕以下）；
- 两只手都与各自袖口连接；
- 两只手在 48×72 下可见；
- 左右手大小接近，不能明显一大一小；
- 右手在鲸尾前方且不浮空；
- 鲸尾主体和末端保留；
- 左腿、右腿、靴子、裙摆、脸和鳍耳不变；
- 遮罩外最终变化为 0；
- 色板不超过 22；
- Alpha 0/255；
- 最多一次有效生成；
- 无手工画手。

直接失败：

- 左手仍是大圆拳；
- 右手缺失；
- 右手只是没有袖口的悬浮球；
- 右手和鲸尾融合；
- 左右手比例差明显；
- 手低于 y=80；
- 手变成手套或长条；
- 使用第二次生成；
- 手工补手。

## 12. 停止门

```text
P2-3R6 通过：恢复 P2-4 四方向
P2-3R6 失败：停止 PixelLab 手部修补，改走 WorkBuddy/Miora 高精度角色锚点
P2-4：保持暂停
P3-0 idle：继续锁定
```

## 13. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。用户确认 P2-3R5 左手虽然可读，但手腕以下太大、像圆拳；同时右侧没有可辨认的右手。P2-4 已暂停。

创建 codex/character-art-pixellab-p2-3r6，从 1dd7afd 开始，只修双手。

输入：art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
左手区域 x=9..19, y=68..81；右手区域 x=42..55, y=65..82。
制作两个分离遮罩，使用 PixelLab Inpaint v3 只提交一次。
目标：两手都是 2～3px 掌心、1px 拇指/圆角、1px 白袖口、腕以下外框<=5×5，最低点不晚于 y=80。
右手必须从右袖口连接出来并位于鲸尾前方，48×72 下可见；不能是悬浮球。
遮罩外全部恢复原像素；色板<=22；Alpha 0/255。

不要手工画手，不要第二次生成，不要改腿/靴/裙摆/鲸尾主体，不要开始四方向或动画。
push 后停止，等 A 验收。
```
