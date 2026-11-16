# ART-V2 PixelLab P2-4 完整四方向静态角色任务书

状态：授权执行；一次四方向主生成；完成后停止等待验收
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-4`
起点：`1dd7afd`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 目标

把当前已确认的 down 单帧扩展成完整四方向静态精灵表：

```text
down：使用当前已批准的 P2-3R5 单帧
left：真实左侧面
right：真实右侧面
up：真实背面
```

最终进入游戏前必须保留本轮确认的：

- 蓝色鲸鳍耳；
- 头发、头带和女仆/学院服装；
- 冰白围裙；
- 柔和玫瑰唇；
- 短裙和可见短腿；
- 深蓝短靴；
- 鲸尾；
- 可读的左手/袖口。

## 2. 唯一 down 母版

```text
art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
SHA-256: 8D8AC191FED1DBC7A6180092E025B159E19D99DC0166532BA1A01DC1DD4E2AC1
```

Down 是最终批准帧。PixelLab 本次即使生成 south 方向，也不得覆盖这个已批准 down；最终精灵表的第一格必须逐像素等于该文件。

辅助参考：

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-raw.png
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

WorkBuddy 图只作为身份和服装参考，不作为运行时像素直接裁切来源。

## 3. PixelLab 主生成

```text
模式：Standard
方向：4
相机视图：high top-down
参考槽：down
参考图：down-left-hand-cleaned.png
页面显示预计费用：8 generations
Pro：不使用
提交次数：1
```

提示词：

```text
Same blue-haired chibi whale-eared maid as the reference. Preserve the exact
face, large blue eyes, soft rose lips, navy bob hair, white maid headband,
light-blue fin ears, navy-and-white outfit, ice-white apron, waist bow,
short skirt with visible short legs, dark navy ankle boots, small whale tail,
and readable rounded left hand with a 1-pixel white cuff.

Generate four cardinal views. Keep the chibi proportions and outfit structure.
In down and up views show two separated legs and two boots. In left and right
views show a readable near leg and a small portion of the far leg, with real
side poses rather than mirrors. Both boot soles must align to the same baseline.
The left hand must remain a compact rounded hand, never a long strip or sleeve.
North view must show back hair, back clothing, rear waist bow and both boots;
the whale tail may be naturally occluded from directly behind.

Pixel art, high top-down game sprite, transparent background, 96x96 per
direction, no antialiasing, binary alpha.
```

不允许：

- 用 Edit Image 再补手或腿；
- 生成后重画身份；
- 把左右方向镜像；
- 用旧的 P2-2 长裙四方向替代；
- 直接改正式游戏。

## 4. 方向与技术清理

方向顺序：

```text
south -> down
west  -> left
east  -> right
north -> up
```

输出：

```text
256×96
单帧 64×96
Alpha 0/255
总色板 21～24（含透明）
脚底接触边界统一 y=88
```

清理规则：

1. 每个 96×96 原始格使用统一 64 px 公共裁切窗口；
2. 不按方向 bbox 分别居中；
3. 不拉伸、不旋转、不手工补画；
4. down 直接使用 P2-3R5 批准帧，不使用生成 south；
5. left/right/up 从 PixelLab 结果裁切；
6. 对生成帧做确定性色板映射，优先沿用 down 的 22 色；
7. 所有鞋底接触边界统一 y=88；
8. 北向鲸尾允许自然遮挡，不再次修尾巴。

## 5. 方向验收

### down

- 必须逐像素等于 P2-3R5 批准帧；
- 柔唇、左手、旧裙清理保持。

### left / right

- 不是镜像；
- 至少能辨认一条近侧腿和一只靴；
- 允许远侧腿只露出 1～2 px；
- 侧面手部不得是长布条；
- 鲸尾方向正确；
- 脚底 y=88。

### up

- 后发、背面服装、腰后蝴蝶结清楚；
- 两条腿或两只鞋跟可读；
- 鲸尾允许自然遮挡；
- 不得出现正面脸；
- 脚底 y=88。

## 6. 必须交付

```text
art-source/character-v2/pixellab/P2-4/
  input-down-approved-64x96.png
  sprite-4dir-raw.png
  sprite-4dir-raw.json
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  sprite-preview-checker-4x.png
  metrics-4dir-clean.json
  visual-review.json
  map-preview-4dir.html
  map-desktop-4dir.png
  map-mobile-4dir.png
  credit-log.json

scripts/
  character_pixellab_p2_4_cleanup.py
  character_pixellab_p2_4_map_capture.py

docs/character-art-v2/pixellab/
  P2-4-report.md
```

## 7. 多方向审计字段

```text
source_down_sha256
raw_sheet_sha256
output_sheet_sha256
sheet_size
frame_size
direction_order
direction_bboxes
foot_baseline_y
foot_anchor_x
down_pixel_identical_to_approved
left_right_mirror_ratio
left_leg_visible
right_leg_visible
up_boots_visible
hand_shape_readable
colors
alpha_values
semi_transparent_pixels
generation_submissions
generations_used
animation_started
production_modified
```

## 8. 地图验收

使用现有青禾镇地图，不改正式页面：

```text
桌面：1440×1000
手机：390×844
运行尺寸：48×72
```

必须检查：

- 四方向均能在地图上显示；
- 切换方向不横向跳动；
- 草地、地砖、道路上无白底和方块边；
- 腿部、靴子和手在 48×72 下可读；
- Console errors = 0；
- 预览按钮不得被描述成玩家控制功能。

## 9. 停止门

出现以下情况直接失败：

- down 被生成结果替换；
- left/right 是镜像；
- left/right 没有腿或靴；
- up 没有两只鞋跟或背面结构；
- 手又变成长布条；
- 旧裙残留重新出现；
- 角色身份明显漂移；
- 需要第二次四方向生成；
- 需要手工补画腿、手或服装；
- 需要修改正式运行时。

```text
P2-4 失败：停止，不得进入动画；由 A 决定 WorkBuddy/Miora 锚点重做
P2-4 通过：用户视觉确认
用户确认：只授权 P3-0 idle，不自动授权 walk
```

## 10. 预算

```text
预计：8 generations
当前余额：1976.9
不购买 Pro
不升级
最多 1 次四方向提交
失败后不自行重试
```

## 11. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-3R5 左手已通过，现在开始 P2-4 完整四方向静态角色。

创建 codex/character-art-pixellab-p2-4，从 1dd7afd 开始。
唯一 down 母版：art-source/character-v2/pixellab/P2-3R5/down-left-hand-cleaned.png
Down 最终必须逐像素保持该文件，不允许被生成的 south 覆盖。

使用 PixelLab Standard 4 directions、high top-down，只提交一次，预计 8 generations。目标：同一角色、短裙露腿、双靴、可读圆手、软唇、鲸鳍耳和鲸尾；left/right 必须真实侧向而非镜像；up 必须有两腿/鞋跟、后发和蝴蝶结，鲸尾可自然遮挡。

清理为 256×96，每帧 64×96，色板 21～24，Alpha 0/255，鞋底 y=88。交 4x/棋盘格预览、桌面/手机 48×72 地图截图、mirror ratio、direction bbox、metrics、credit-log 和可复现脚本。

不要用 Edit Image 再补手/腿，不要镜像左右，不要用旧长裙四方向，不要做第二次生成，不要开始 idle/walk，不要修改生产。
push 后停止，等 A 验收。
```
