# ART-V2 PixelLab P3-0R 确定性 Idle 任务书

状态：授权执行；零 AI 生成；先做 Down proof 再扩展四方向
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p3-0r-idle`
起点：`ff9b334`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 背景

P3-0 的 PixelLab Animation v3 失败，因为它重新生成了脸、嘴、头发和身体轮廓。

本轮不再让 AI 重绘角色。使用已批准的 P2-4 静态四方向精灵，做确定性的 1 px 次级运动 idle。

## 2. 冻结输入

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
256×96 RGBA
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

每个方向静态帧是该行 Frame 0，必须逐像素不变。

## 3. 动作设计

四帧循环：

```text
Frame 0：静态基准
Frame 1：次级摆动 A（最多 1 px）
Frame 2：回到静态基准
Frame 3：次级摆动 B（相反方向，最多 1 px）
播放：0 -> 1 -> 2 -> 3 -> 0
FPS：5
```

Frame 2 必须与 Frame 0 逐像素一致。

### 允许变化区域

只允许变化：

- 头发末端；
- 鳍耳边缘；
- 裙摆/围裙下缘 1 px；
- 鲸尾末端和尾巴轮廓。

### 禁止变化

- 脸部、眼睛、眉毛和柔唇；
- 刘海主体；
- 头带主体；
- 躯干和胸部；
- 双手和袖口；
- 双腿和靴子；
- 角色整体轮廓；
- 22 色色板。

Frame 1 和 Frame 3 的头发/鳍耳/尾巴运动方向应相反，幅度最多 1 px。

不得添加呼吸导致脸或躯干重新绘制。本轮以次级摆动表现 idle。

## 4. 实现方式

允许：

- Aseprite 图层变换；
- Spine / 骨骼位移；
- Python/Pillow 确定性像素位移；
- 已有像素层的平移和透明背景处理。

禁止：

- PixelLab Animation、Inpaint 或其他 AI；
- 手工重画脸、衣服和身体；
- 用不同帧重新生成角色；
- 改变角色轮廓和颜色；
- 逐帧重新编码新像素主体。

每一帧的来源和位移规则必须记录。若使用代码，必须可重复运行。

## 5. Down proof 停止门

先只制作 Down 4 帧：

```text
art-source/character-v2/pixellab/P3-0R/
  down-proof-4f.png
  down-proof-preview-8x.webp
  down-proof-metrics.json
```

Down proof 必须通过：

- Frame 0 与 P2-4 Down 完全一致；
- Frame 2 与 Frame 0 完全一致；
- 脸和躯干区域变化为 0；
- 手部区域变化为 0；
- 双腿和靴子区域变化为 0；
- Frame 1/3 只有允许次级区域发生 1 px 位移；
- 四帧 bbox 和鞋底 y=88 不改变；
- 色板 22，Alpha 0/255；
- 预览中能看出轻微摆动但不闪烁。

Down proof 不通过，停止，不制作 left/right/up。

## 6. 四方向完成

Down proof 通过后，用同一规则处理：

```text
down / left / right / up
-> 256×384 RGBA
-> 4 列 × 4 行
-> 64×96 单帧
-> 5 FPS
```

所有方向 Frame 2 = Frame 0，Frame 1/3 只改变次级区域。

## 7. 必须交付

```text
art-source/character-v2/pixellab/P3-0R/
  input-sprite-4dir.png
  down-proof-4f.png
  down-proof-preview-8x.webp
  down-proof-metrics.json
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
  character_pixellab_p3_0r_idle_rig.py
  character_pixellab_p3_0r_preview.py
  character_pixellab_p3_0r_map_capture.py

docs/character-art-v2/pixellab/
  P3-0R-report.md
```

## 8. metrics 最低字段

```text
source_sheet_sha256
output_sheet_sha256
sheet_size
frame_size
direction_order
frame_count
fps
loop_order
frame0_pixel_identical_to_p2_4
frame2_pixel_identical_to_frame0
face_region_changed_pixels
torso_region_changed_pixels
hand_region_changed_pixels
leg_region_changed_pixels
secondary_region_changed_pixels
changed_pixels_between_adjacent_frames
loop_frame3_to_frame0_changed_pixels
frame_bboxes
sole_bottom_rows
frame_anchor_x
colors
alpha_values
semi_transparent_pixels
generation_submissions
pixellab_calls
animation_started
production_modified
```

## 9. 视觉验收

预览必须提供：

- Down proof WebP；
- 四方向完整 WebP；
- 四方向 GIF；
- 深色/浅色/棋盘格 contact sheet；
- 48×72 地图截图。

验收重点：

- 角色看起来只是轻轻晃头发/鳍耳/尾巴；
- 眼睛、嘴和身体保持完全一致；
- 没有表情变化；
- 没有帧间拉伸；
- 尾迹和裙摆不闪烁；
- 4 帧循环不跳。

## 10. 硬性验收

必须全部通过：

- Frame 0 逐像素用 P2-4；
- Frame 2 逐像素等于 Frame 0；
- 脸、躯干、手、腿、靴变化为 0；
- 只允许次级区域 1 px 位移；
- 每方向 4 帧非空；
- 256×384，64×96；
- 5 FPS；
- 鞋底 y=88；
- 22 色，Alpha 0/255；
- 4 方向循环连续；
- 48×72 地图可读；
- Console errors = 0；
- 零 AI 调用；
- 无手工重画角色主体。

直接失败：

- 脸部或嘴唇变化；
- Frame 2 不等于 Frame 0；
- 手、腿、靴变化；
- 位移超过 1 px；
- 首尾跳帧；
- 新增颜色或半透明；
- 重画或重生成角色；
- 需要 AI 才能完成。

## 11. 停止门

```text
P3-0R Down proof 不通过：停止，不制作其他方向
P3-0R 四方向不通过：停止，不进入 walk
P3-0R 通过：用户确认 idle
用户确认：才授权 P3-1 walk
```

## 12. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P3-0 的 Animation v3 失败，因为脸和身体被重画。现在停止所有 AI 动画，只做确定性 idle。

创建 codex/character-art-pixellab-p3-0r-idle，从 ff9b334 开始。
输入：art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12

先只做 Down proof 4 帧：
Frame 0 = P2-4 Down，逐像素一致；
Frame 1 = 头发末端/鳍耳/鲸尾 1px 摆动 A；
Frame 2 = Frame 0，逐像素一致；
Frame 3 = 相反方向 1px 摆动 B。
脸、躯干、手、腿和靴子像素变化必须为 0；色板 22，Alpha 0/255，鞋底 y=88。

零 AI 调用，不改正式运行时。Down proof 通过后再扩到 left/right/up，最终 256×384、5 FPS，交 WebP/GIF、contact sheet、地图截图、metrics 和可复现脚本。
不要开始 walk/turn/stop；push 后停止等待 A 验收。
```
