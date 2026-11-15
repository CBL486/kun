# ART-V2 PixelLab P2-3R 下半身遮罩重绘任务书

状态：仅授权 down 单帧遮罩验证；最多一次局部生成
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r`
起点：`0dfa3b4`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮只验证一帧

P2-3 的整轮四方向生成没有产生腿。本轮不再重新生成整轮角色，只对正面 down 帧做一次带明确遮罩的下半身局部重绘。

目标：

```text
验证 PixelLab 能否在长裙下半身区域补齐短腿和短靴
```

只做 `down`，不做 left/right/up，不做动画，不做地图接入。

## 2. 输入

唯一基础图：

```text
art-source/character-v2/pixellab/P2-3/input-down-soft-lips-64x96.png
```

要求保留：

- 脸、眼睛和柔唇；
- 蓝发、头带和鲸鳍耳；
- 上身服装、围裙上半部、手臂；
- 鲸尾主体；
- 64×96 画布和透明背景。

## 3. 遮罩规则

创建：

```text
art-source/character-v2/pixellab/P2-3R/down-lower-body-mask.png
```

格式：

```text
64×96
RGBA
遮罩待编辑区域：Alpha 255
保留区域：Alpha 0
除 0/255 外不允许其他 Alpha
```

遮罩范围只覆盖下半身中央裙摆和拟生成的腿/鞋区域，建议 bounding box：

```text
x = 14..50
y = 67..90
```

可以使用固定多边形或确定性遮罩脚本，但必须：

- 不覆盖脸、眼睛、刘海、头带、鳍耳；
- 不覆盖手臂和手；
- 不覆盖鲸尾末端；
- 不覆盖上半身服饰；
- 不通过遮罩重画整个角色；
- 遮罩文件必须提交并记录哈希。

遮罩是编辑范围，不是角色绘制模板；不得在遮罩里手工画腿。

## 4. 局部重绘要求

工具：

```text
PixelLab Inpainting / Edit Image with mask
模型：Standard
输入：input-down-soft-lips-64x96.png
遮罩：down-lower-body-mask.png
提交次数：1
```

如果当前 PixelLab 界面不支持显式遮罩：

```text
不提交生成
记录实际界面限制
停止并报告
不得退化为无遮罩提示词编辑
```

局部提示词：

```text
Replace only the masked lower skirt area with a convincing short chibi
lower body for the same blue-haired whale girl. Keep the navy dress top
and apron. Shorten the skirt hem above the knees. Show two clearly
separated short legs with pale skin and two dark navy ankle boots. Add a
1-pixel transparent gap between the legs. Both boot soles must align
cleanly at y=88. Preserve the whale tail, hands, upper body, face, hair,
headband, fin ears, soft rose lips, palette and transparent background.
Pixel art, no antialiasing, no semi-transparent pixels.
```

禁止：

- 修改遮罩外任何像素；
- 改脸、眼、唇型、头发、鳍耳和上身；
- 删除鲸尾；
- 生成第三只脚；
- 用一条宽腿代替两条腿；
- 让鞋悬空；
- 手工补腿；
- 无遮罩重试；
- 做第二次生成。

## 5. 输出与审计

```text
art-source/character-v2/pixellab/P2-3R/
  input-down-soft-lips-64x96.png
  down-lower-body-mask.png
  down-masked-edit-raw.png
  down-masked-edit-preview-8x.png
  down-masked-edit-metrics.json
  credit-log.json

scripts/
  character_pixellab_p2_3r_masked_audit.py

docs/character-art-v2/pixellab/
  P2-3R-report.md
```

审计脚本至少记录：

```text
input_sha256
mask_sha256
result_sha256
changed_pixels_inside_mask
changed_pixels_outside_mask
removed_opaque_pixels_outside_mask
added_opaque_pixels_outside_mask
result_bbox
leg_visible_height
boot_pixel_count
boot_colors
alpha_values
semi_transparent_pixels
generation_submissions
```

## 6. 硬性验收

### 必须通过

- 生成前后画布均为 64×96；
- 遮罩外变化像素数必须为 0；
- down 帧清楚看到两条短腿；
- 每条腿宽约 3～4 px；
- 两腿之间有 1～2 px 透明间隔；
- 两只深蓝短靴可辨认；
- 两个鞋底/接触边在 y=88；
- 腿与裙摆连接自然，不悬空；
- 柔唇、脸、鳍耳、上身和鲸尾完全保留；
- Alpha 只允许 0/255；
- 生成后如需调色，最终不超过 24 色；
- 只提交一次局部生成。

### 直接失败

- 遮罩外有任何变化；
- 仍然没有腿；
- 只出现一只脚；
- 两腿粘连成一整块；
- 鞋底不齐或悬空；
- 鲸尾被误删或重画；
- 嘴唇、脸、手或鳍耳被改动；
- 需要第二次生成才能看出腿；
- 使用无遮罩 Edit Image；
- B 手工补腿。

## 7. 停止门

```text
P2-3R 通过：仅授权 A 决定其余三个方向如何制作
P2-3R 失败：停止 PixelLab 局部重绘路线
其他方向：未经 A 验收不得开始
P3-0 idle：继续锁定
生产接入：未授权
```

如果 P2-3R 失败，改用 WorkBuddy/Miora 先重做“短裙露腿”的高精度角色锚点，再由 PixelLab 做四方向；该路线必须另行下发任务书，B 不得自行切换工具。

## 8. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-3 整轮四方向生成失败：身份和柔唇通过，但所有方向仍然没有腿。不要重复同一条 Prompt，也不要做第二次整轮生成。

创建 codex/character-art-pixellab-p2-3r，从 0dfa3b4 开始，只做 down 单帧带遮罩的局部重绘。

输入：art-source/character-v2/pixellab/P2-3/input-down-soft-lips-64x96.png
遮罩：自己制作并提交 64×96 down-lower-body-mask.png，仅覆盖下半身裙摆和拟生成腿区域；不得覆盖脸、手、鳍耳、上身和鲸尾末端。
工具：PixelLab Inpainting / Edit Image with mask，Standard，只提交一次。
目标：缩短裙摆，生成两条有 1px 间隔的短腿和两只深蓝短靴，鞋底 y=88。
硬门：遮罩外变化像素必须为 0；脸、柔唇、上身、鳍耳和鲸尾保持不变；不手工画腿。

如果 PixelLab 当前界面不支持带遮罩编辑，停止，不提交生成，报告界面限制。
如果失败，不要重试，不要切换到其他工具；push 后等 A 决定。
```
