# ART-V2 PixelLab P2-3R3 腿部细节微调任务书

状态：授权执行；零 AI 生成；完成后停止等待 A 验收
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r3`
起点：`b62a152`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮目标

只微调 down 帧两条腿和两只短靴的像素细节，使腿部更有体积、脚踝更自然、靴子层级更清楚。

用户已经认可当前腿型和站姿，因此本轮不是重画，也不是重新生成：

```text
保留腿长
保留两条腿的位置
保留约 6 px 的腿间距
保留鞋底 y=88
保留脸、柔唇、手臂、头发、鳍耳、服装和鲸尾
```

## 2. 唯一输入

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
SHA-256: 625D0B1E11686BC9BD9217BC20507F3D66CC295E569DCC7A05BB6D06A1D041B6
```

不得使用 raw Inpaint 结果作为最终基础。

## 3. 允许修改区域

只允许修改两个固定矩形：

```text
左腿/左靴：x=19..28, y=73..89
右腿/右靴：x=31..40, y=73..89
```

两区域之外必须像素级完全不变。

如果为了 1 px 靴子外沿需要调整边界，最多向外扩 1 px，但必须在 metrics 中记录最终区域。

禁止修改：

- 左右手臂和手；
- 裙摆与围裙；
- 鲸尾；
- 脸部、眼睛、柔唇和头发；
- 鳍耳；
- 任意遮罩外区域。

## 4. 细节方向

### 4.1 腿部

当前腿宽约 6 px，整体接近直筒。做以下小范围精修：

1. 膝盖附近保留 5～6 px 宽度；
2. 脚踝附近收窄到 4～5 px；
3. 每个腿只增加 1 px 暗部或边缘阴影，不做大面积渐变；
4. 允许使用现有肤色：
   - 亮部 `#FAD4CA`
   - 暗部/边缘 `#B5A9BC`
5. 不允许使用黑色描边代替腿部阴影；
6. 不允许把腿改成火柴腿或 2 px 细线；
7. 不允许改变腿根连接位置和左右腿的间距。

### 4.2 靴子

在现有深蓝短靴上增加可读层级：

- 顶部增加 1 px 深蓝色靴口；
- 侧面最多增加 1 px 冷蓝高光；
- 鞋头允许向外增加 1 px，形成轻微外扩；
- 鞋底保留 1 px 深色接触线，且底边仍为 `y=88`；
- 靴子内部不得出现新的渐变、抗锯齿或杂色；
- 左右靴子保持同一高度，不得一只悬空或错位。

允许优先从现有角色色板选择：

```text
#10192D
#191927
#202847
#263563
#2D4781
#2A3F72
```

如果新色会导致总色板超过 24，必须复用现有颜色，不得新增。

## 5. 执行方式

本轮禁止调用任何生图或 Inpaint 服务。

B 必须编写可复现的确定性像素脚本，例如：

```text
scripts/character_pixellab_p2_3r3_leg_detail.py
```

要求：

- 从输入文件读取；
- 所有改动限定在允许区域；
- 每一步颜色替换或像素位置调整有明确规则；
- 重复运行哈希一致；
- 输出 changed-pixels 清单和差异预览；
- 不使用网络、AI API 或随机数；
- 不允许手工在画布上直接涂改后不留脚本记录。

如果单纯调整颜色不足以形成自然脚踝，可以只做 1～2 px 的轮廓收束，但不得重画整条腿。

## 6. 输出

```text
art-source/character-v2/pixellab/P2-3R3/
  down-legs-microadjusted.png
  down-legs-diff-12x.png
  down-legs-preview-12x.png
  runtime-48x72-preview-8x.png
  metrics.json
  visual-review.json

scripts/
  character_pixellab_p2_3r3_leg_detail.py

docs/character-art-v2/pixellab/
  P2-3R3-report.md
```

### `down-legs-diff-12x.png`

必须展示：

```text
BEFORE | AFTER | DIFF
```

DIFF 中所有变化像素用高对比色标出，清楚证明没有修改区域外内容。

### `down-legs-preview-12x.png`

必须用最近邻放大，分别放在：

- 浅色背景；
- 深色背景；
- 透明棋盘格背景。

### `runtime-48x72-preview-8x.png`

从最终 64×96 使用最近邻缩到 48×72，再放大展示。不得把 48×72 当成新的源文件。

## 7. metrics 最低字段

```text
input_sha256
output_sha256
allowed_regions
changed_pixels_total
changed_pixels_outside_allowed_regions
changed_pixels_by_rule
left_leg_width_by_row
right_leg_width_by_row
leg_gap_px
boot_cuff_pixels
boot_highlight_pixels
boot_sole_edges
colors
alpha_values
semi_transparent_pixels
generation_submissions
pixellab_calls
animation_started
production_modified
```

所有字段填写实际值。

## 8. 硬性验收

必须通过：

- 两区域外变化像素为 0；
- 两条腿仍独立、可辨认；
- 脚踝比膝盖略窄，但不细成线条；
- 腿间距保持 5～6 px；
- 两只靴子均有清楚的靴口和鞋底；
- 两只鞋底均为 `y=88`；
- 柔唇和上半身完全不变；
- 总色板不超过 24 色；
- Alpha 仅 0/255；
- 48×72 下腿和靴子仍可辨认；
- 没有 AI 生成；
- 没有手工重画整条腿；
- 不修改运行时。

直接失败：

- 只换颜色却没有可读的靴口/鞋底；
- 腿被削成 2～3 px 线条；
- 腿间距小于 5 px或大于 7 px；
- 鞋底不齐；
- 改动区域外任意像素；
- 手臂、裙摆、鲸尾或脸部被改；
- 为了效果再次生成；
- 无脚本可复现。

## 9. 回归

执行：

```powershell
.\scripts\test-b7.ps1
```

报告通过数、警告和 Console errors。只提交本轮相关文件。

提交信息建议：

```text
art: refine P2-3R3 leg and boot pixel details
```

push 后停止，等待 Agent A 验收。

## 10. 停止门

```text
P2-3R3 未通过：不进入四方向
P2-3R3 通过：仅授权完整四方向腿型制作
用户未确认：不进入 P3-0 idle
```

## 11. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-3R2 正面腿型已经获得用户认可，现在只微调腿部细节，零 AI 生成。

创建 codex/character-art-pixellab-p2-3r3，从 b62a152 开始。
输入：art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
只修改：
左腿/左靴 x=19..28, y=73..89
右腿/右靴 x=31..40, y=73..89

目标：膝盖到脚踝轻微收束，腿侧最多 1px 阴影；靴子增加 1px 靴口、最多 1px 冷蓝高光和轻微鞋头/鞋底层次。保留腿长、6px 左右腿间距、鞋底 y=88，以及脸、柔唇、手臂、裙摆、鳍耳和鲸尾不变。

写确定性脚本，不使用 PixelLab/AI，不手工重画整条腿。输出 before/after/diff 12x、48×72 预览、metrics 和报告。区域外变化必须为 0，总色板不超过 24。

push 后停止，等 A 验收；不要开始四方向或动画。
```

