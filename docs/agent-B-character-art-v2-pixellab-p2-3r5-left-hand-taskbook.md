# ART-V2 PixelLab P2-3R5 左手可读性修复任务书

状态：仅授权左手单区域遮罩重绘；最多一次生成
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r5`
起点：`c655558`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮目标

修复 down 帧左手，使其在 48×72 下能被读成一只手，而不是细长布条。

只处理左手腕、袖口和手部，不处理其他区域。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R4/down-left-skirt-cleaned.png
SHA-256: 4B51182AA44702F47DB84B014B52DF5ADDD3CCA5D961B21177F85D5557D9B9A2
```

参考：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

只参考左手在角色比例中的大小和连接关系，不复制 1024 图像素，也不整体缩放角色。

## 3. 修改区域

只允许编辑：

```text
x=9..19
y=68..83
```

重点区域：

```text
x=10..18
y=71..81
```

硬性禁止覆盖：

- 左腿 x>=20；
- 右腿；
- 靴子；
- 裙摆主体；
- 鲸尾；
- 脸、头发和鳍耳；
- 右臂；
- 上半身服装。

遮罩必须排除左腿边缘。允许区域外最终变化必须为 0。

## 4. 目标手型

在当前 Q 版比例下，左手应满足：

```text
手腕宽度：2～3 px
掌心宽度：3～4 px
掌心高度：3～4 px
拇指：向内或向前 1 px
白袖口：1 px 可辨认
总手部高度：4～6 px
```

允许的最小外形逻辑：

```text
上方：白袖口/手腕
中间：浅肤色掌心
内侧：1 px 拇指或圆角
下方：深色 1 px 边缘，不拖成长条
```

必须：

- 与上方手臂连续；
- 有掌心而不是单一竖条；
- 拇指或圆角轮廓至少能读出其中一种；
- 白袖口与皮肤分层清楚；
- 手下方没有拖到 y=84 的袖布、旧裙或黑边；
- 48×72 下手部不再像悬挂布条。

禁止：

- 画成手套或袖套；
- 画成第二把刀或鲸尾；
- 拉成细长手指；
- 只手绘整条手臂；
- 改变手臂长度；
- 增加第三只手；
- 手工补像素绕过生成；
- 多次 Inpaint 试错。

## 5. 遮罩与生成

创建：

```text
art-source/character-v2/pixellab/P2-3R5/left-hand-mask.png
art-source/character-v2/pixellab/P2-3R5/left-hand-mask-api.png
art-source/character-v2/pixellab/P2-3R5/left-hand-mask-preview-16x.png
```

遮罩要求：

- 64×96 RGBA；
- 只覆盖左手腕、手、袖口和紧邻 1 px 边缘；
- 不覆盖左腿、裙摆和鲸尾；
- Alpha 只允许 0/255；
- 使用明确多边形/固定像素集合，不能整块清空允许区。

工具：

```text
PixelLab Inpaint v3
输入：down-left-skirt-cleaned.png
遮罩：left-hand-mask-api.png
提交次数：1
seed：20261117
crop_to_mask：false
no_background：true
```

提示词：

```text
Repair only the character's left hand, wrist and 1-pixel white cuff inside
the mask. The hand must connect naturally to the existing bare arm above.
Create a compact readable chibi hand with a 3-4 pixel palm, one small thumb
or rounded inner contour, pale skin highlight and one skin shadow edge.
Keep a distinct 1-pixel white cuff. The hand must not extend below y=80 and
must not form a long glove, sleeve, cloth strip, blade or dangling shape.
Preserve all outside-mask pixels exactly, including the shortened skirt,
both legs, both boots, whale tail, face, hair and fin ears. Pixel art,
binary alpha, no antialiasing.
```

如果 PixelLab 界面要求使用 Classic Inpaint：

- 允许使用；
- 记录模型；
- 仍只提交一次；
- 不接受细长布条结果。

## 6. 生成后处理

Inpaint v3 可能重新映射遮罩外颜色，因此必须：

1. 遮罩外全部恢复为输入原像素；
2. 遮罩内将颜色映射回现有角色色板；
3. 不手工重画手；
4. Alpha 保持 0/255；
5. 总色板不超过 22；
6. 只手部区域允许变化。

如果遮罩内模型生成了可读手型但边缘有 1 px 杂边，可以做确定性透明化/色板映射；不得人工补出手指。

## 7. 输出

```text
art-source/character-v2/pixellab/P2-3R5/
  left-hand-mask.png
  left-hand-mask-api.png
  left-hand-mask-preview-16x.png
  down-left-hand-raw.png
  down-left-hand-cleaned.png
  down-left-hand-diff-16x.png
  down-left-hand-grid-32x.png
  runtime-48x72-preview-8x.png
  metrics.json
  credit-log.json
  api-response.json
  job-response.json

scripts/
  character_pixellab_p2_3r5_left_hand_cleanup.py

docs/character-art-v2/pixellab/
  P2-3R5-report.md
```

## 8. 必须提供的视觉证据

### hand diff

```text
BEFORE | MASK | AFTER | DIFF
```

### hand grid

在 32× 放大图中标出：

- 手腕；
- 掌心；
- 拇指/圆角；
- 白袖口；
- 手部底边；
- 允许区域边界。

### runtime

从最终 64×96 最近邻缩放到 48×72，再放大展示。必须能够确认手不再像布条。

## 9. 硬性验收

必须全部通过：

- 遮罩外最终变化为 0；
- 手与上方手臂连续；
- 掌心可读；
- 拇指或圆角轮廓可读；
- 白袖口与肤色可区分；
- 手部不再向下拖成长条；
- 手部最低点不晚于 y=80；
- 48×72 下手型可读；
- 左腿、右腿、靴子、裙摆和鲸尾完全不变；
- 总色板不超过 22；
- Alpha 0/255；
- 只提交一次有效生成；
- 无手工补手。

直接失败：

- 仍然是 2～3 px 竖条；
- 出现手套或长袖；
- 手变成黑色轮廓块；
- 手与手腕断开；
- 为了手型手绘整只手；
- 左腿或裙摆被改；
- 遮罩外发生变化；
- 需要第二次生成才能成立。

## 10. 停止门

```text
P2-3R5 通过：等用户确认左手
用户确认后：才允许完整四方向腿型
P2-3R5 失败：停止 PixelLab 手部修补，改走 WorkBuddy/Miora 高精度锚点
P3-0 idle：继续锁定
```

## 11. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-3R4 清掉了旧裙，但用户确认左手仍然不可读：当前只有约 2～3px 宽的肤色竖条和深色轮廓，没有掌心、拇指和清楚袖口，48×72 下仍像布片。

创建 codex/character-art-pixellab-p2-3r5，从 c655558 开始，只修复 down 帧左手。

输入：art-source/character-v2/pixellab/P2-3R4/down-left-skirt-cleaned.png
只允许编辑 x=9..19, y=68..83，不能覆盖左腿 x>=20、裙摆、鲸尾、脸或上身。
制作显式左手遮罩，使用 PixelLab Inpaint v3，只提交一次。
目标：2～3px 手腕、3～4px 掌心、1px 拇指/圆角、1px 白袖口，手最低点不晚于 y=80，不能拖成长条。
遮罩外必须恢复为原像素，最终色板<=22，Alpha 0/255。

不要手绘手，不要重画整条手臂，不要第二次生成，不要开始四方向或动画。
如果仍像细长布条，停止报告；下一步改走 WorkBuddy/Miora 锚点重做。
```
