# ART-V2 PixelLab P3-0 Idle 四方向动画任务书

状态：授权执行；只做 idle；四方向 × 四帧；完成后停止等待验收
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p3-0-idle`
起点：`7b62880`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 目标

基于已通过的四方向静态角色，制作第一套正式 idle 动画：

```text
down：4 帧
left：4 帧
right：4 帧
up：4 帧
总帧数：16
帧率：5 FPS
循环时长：0.8 秒
```

Idle 只表现呼吸、轻微重心变化和头发/鲸尾的 1 px 次级运动。双脚和靴子保持固定，不表现行走。

## 2. 冻结母版

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
256×96 RGBA
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

方向顺序：

```text
down / left / right / up
```

母版帧：

```text
down  = sheet x=0..64
left  = sheet x=64..128
right = sheet x=128..192
up    = sheet x=192..256
```

四方向静态帧必须是每行动画的第 0 帧，并且逐像素不变。

## 3. 动画结构

最终精灵表：

```text
256×384 RGBA
4 列 × 4 行
单帧 64×96
列：frame 0 / 1 / 2 / 3
行：down / left / right / up
```

Frame 0：

- 使用 P2-4 对应静态帧；
- 禁止被动画模型替换；
- 必须逐像素一致。

Frame 1～3：

- 从 PixelLab 动画结果取得；
- 不得重新设计角色；
- 必须清理回 64×96、22 色、Alpha 0/255。

## 4. 运动设计

### 呼吸

- 胸口/肩部最多上抬或下落 1 px；
- 头部允许跟随 1 px，不得超过；
- 不允许头部左右旋转；
- 不允许脸部像素变形。

### 腿和靴

- 两只靴底始终在 y=88 接触边界；
- 脚和腿不抬起；
- 每帧脚底锚点横向变化不超过 1 px；
- 不允许走路式左右脚交替。

### 手

- 双手保持紧凑小尺寸；
- 不允许重新变大；
- 允许最多 1 px 跟随呼吸；
- 不允许手指变化。

### 头发、鳍耳、鲸尾

- 只允许 1 px 次级摆动；
- 相邻帧不能突然反向跳变；
- Down/Up 的鲸尾遮挡保持自然；
- 不允许鲸尾轮廓放大、变长或变成第三条腿。

### 循环

- 播放顺序：0 -> 1 -> 2 -> 3 -> 0；
- Frame 3 回到 Frame 0 必须有连续感；
- 不允许首尾出现明显跳帧；
- 四方向使用相同节奏。

## 5. 生成方式

优先使用 PixelLab 对现有四方向角色提供的动画能力：

```text
可接受：skeleton / rig-based idle
可接受：animation-with-text / text animation
不接受：重新 create-character 生成一套新角色
不接受：逐帧 AI 重绘导致身份漂移
```

执行要求：

- 以 P2-4 四方向精灵为输入；
- 先制作 down 4 帧作为 proof；
- 如果 down proof 已明显漂移、脚底移动或手变大，立即停止，不生成其余方向；
- down proof 通过后，再按同一参数制作 left/right/up；
- 四方向使用同一动作描述和同一节奏。

动作描述：

```text
Very subtle idle breathing loop for a chibi pixel-art whale maid.
Keep both boots planted at exactly the same baseline. Raise and lower the
chest and shoulders by at most one pixel. Let the head follow by at most one
pixel without changing the face. Add only one-pixel secondary motion to the
hair tips, fin ears and whale tail. Keep both compact hands small and attached
to their white cuffs. Preserve the short skirt, legs, boots, tail, outfit and
all four direction silhouettes. Pixel art, binary alpha, no antialiasing,
no blinking, no walking, no turning, no new character design.
```

## 6. 预算控制

```text
起始余额：1965.9 generations
Pro：不使用
购买/升级：0
```

每个方向最多一次主提交。如果 PixelLab 支持四方向批量动画，则优先一次批量提交并记录。

失败后不得自行追加第二次同方向生成。是否重试由 Agent A 根据 down proof 或具体方向的证据决定。

每方向必须记录：

```text
model
submission_count
generations_used
output_id
seed（如有）
```

## 7. 技术清理

所有生成帧：

```text
96×96 或平台输出尺寸
-> 统一公共裁切窗口
-> 64×96
-> 脚底 y=88
-> 沿 P2-4 角色 22 色色板映射
-> Alpha 0/255
-> 256×384 四方向四帧表
```

禁止：

- 拉伸；
- 旋转；
- 逐帧单独居中；
- 手工补画身体；
- 手工改脸部；
- 用程序化几何图形重画角色；
- 改变 P2-4 母版第 0 帧。

## 8. 必须交付

```text
art-source/character-v2/pixellab/P3-0/
  input-sprite-4dir.png
  idle-down-proof-4f.png
  idle-4dir-raw.png
  idle-4dir-4f.png
  idle-preview-4x.webp
  idle-preview-checker-4x.gif
  idle-contact-sheet.png
  frames/down/0.png ... 3.png
  frames/left/0.png ... 3.png
  frames/right/0.png ... 3.png
  frames/up/0.png ... 3.png
  metrics-idle.json
  visual-review.json
  map-preview-idle.html
  map-desktop-idle.png
  map-mobile-idle.png
  credit-log.json

scripts/
  character_pixellab_p3_0_idle_cleanup.py
  character_pixellab_p3_0_preview.py
  character_pixellab_p3_0_map_capture.py

docs/character-art-v2/pixellab/
  P3-0-report.md
```

## 9. metrics 最低字段

```text
source_sheet_sha256
output_sheet_sha256
sheet_size
frame_size
direction_order
frame_count
fps
loop_order
row_frame0_pixel_identical_to_p2_4
frame_bboxes
sole_bottom_rows
frame_anchor_x
max_anchor_x_drift
max_sole_bottom_drift
colors
alpha_values
semi_transparent_pixels
changed_pixels_between_adjacent_frames
loop_frame3_to_frame0_changed_pixels
generation_submissions_by_direction
generations_used
animation_started
production_modified
```

## 10. 视觉证据

### Contact sheet

`idle-contact-sheet.png`：

- 4 行方向，4 列帧；
- 标注每一行方向和每一列帧号；
- 使用深色、浅色、棋盘格三种背景。

### 动画预览

必须提供透明 WebP 和兼容 GIF：

- 4 个方向分别循环；
- 不放慢动作伪装平滑；
- 5 FPS 原始节奏；
- 帧不能累积或拖影；
- GIF disposal=2，透明索引固定。

### 地图证据

使用现有青禾镇地图预览：

```text
桌面 1440×1000
手机 390×844
角色 48×72
```

至少截取：

- down 两个不同 idle 帧；
- left/right/up 各一帧；
- 方向切换水平偏移；
- Console errors = 0。

## 11. 硬性验收

必须全部通过：

- Sheet：256×384；
- 单帧：64×96；
- 每方向正好 4 帧；
- 5 FPS；
- 16 帧均非空；
- 每行 Frame 0 与 P2-4 静态帧逐像素一致；
- 双靴鞋底每帧 y=88；
- 脚底锚点横向漂移不超过 1 px；
- 手部始终保持小尺寸；
- 脸、眼睛和柔唇不漂移；
- 旧裙残留不出现；
- 头发/鳍耳/鲸尾只有 1 px 次级运动；
- 首尾循环连续；
- 22 色以内，Alpha 0/255；
- 无抗锯齿、无半透明边缘；
- 真实地图 48×72 可读；
- Console errors = 0；
- 不修改正式运行时。

直接失败：

- Frame 0 被重新生成；
- 腿开始走路；
- 头部变形或脸部漂移；
- 手变大或消失；
- 鲸尾变形；
- 四方向动作节奏不一致；
- 任一脚悬空；
- 预览闪烁或跳帧；
- 为了修一帧手工重画整块身体；
- 需要重新生成新角色；
- 把 idle 和 walk 混在同一批提交。

## 12. 停止门

```text
P3-0 失败：停止，不进入 walk
P3-0 通过：用户确认 idle
用户确认后：才授权 P3-1 walk
生产接入：仍未授权
```

## 13. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-4 四方向静态角色已获用户确认，现在只做 P3-0 idle。

创建 codex/character-art-pixellab-p3-0-idle，从 7b62880 开始。
母版：art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12

只做四方向 × 四帧 idle，5 FPS，最终 256×384，单帧 64×96。
每行 Frame 0 必须逐像素使用 P2-4 静态帧；Frame 1～3 只表现 1px 呼吸和 1px 头发/鳍耳/鲸尾次级运动。双脚固定，鞋底每帧 y=88，双手保持小尺寸，脸和柔唇不能漂移。

优先使用 PixelLab skeleton/animation 对现有角色做 idle，不要重新生成新角色。先做 down 4 帧 proof；down 明显漂移、脚移动或手变大就停止，不继续其他方向。通过后同参数完成 left/right/up。

交 256×384 精灵表、透明 WebP/GIF、contact sheet、4 方向帧文件、桌面/手机 48×72 地图截图、metrics、credit-log 和可复现脚本。
不要开始 walk/turn/stop，不要手工重画身体，不要修改正式运行时。push 后停止等待 A 验收。
```
