# ART-V2 PixelLab P2-3 腿部可见性与嘴唇微调任务书

状态：授权执行；最多一次四方向主生成；完成后停止等待 A 验收
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3`
起点：`89c491d`（P2-2 技术通过版本）
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 用户反馈

用户对 P2-2 四方向整体评价：

```text
“还不错，就是腿呢？然后嘴唇再微调一下就行”
```

因此本轮只解决两个问题：

1. 露出可辨认的短腿和鞋，让角色不再像没有下半身；
2. 将目前偏浓的玫瑰唇色调整为更柔和、更自然的低饱和唇色。

其他角色身份、发型、服装主体、鲸鳍耳、鲸尾、色板风格和比例不重新设计。

## 2. 视觉目标

### 2.1 腿部

角色保持当前 Q 版比例和女仆/学院服装，但裙摆略缩短，裙摆下方必须出现可辨认的腿和深蓝短靴。

方向要求：

- `down`：两条腿分开，左右各一只鞋；两腿之间保留 1～2 px 透明间隔；
- `up`：看到两条腿背面和鞋跟，不能变成一整块裙底；
- `left`：看到近侧完整腿型，远侧腿露出 1～2 px 轮廓；
- `right`：与 left 为真实不同侧视图，不得镜像冒充。

尺寸建议：

```text
裙摆下可见腿部高度：7～10 px
单腿宽度：3～4 px
单靴宽度：4～5 px
靴高：2～3 px
两腿透明间隔：1～2 px
脚底接触边：统一 y=88
```

允许裙摆和围裙下缘小幅调整，但不得：

- 改成裤子；
- 只露出一只脚；
- 画成悬空火柴腿；
- 用纯黑色两根竖线代替腿；
- 破坏鲸尾、腰扣或服装主体；
- 通过 B 手工逐像素重画角色完成。

### 2.2 嘴唇

当前唇色：

```text
主色：#B85F6C
阴影：#8D4654
```

目标改为更柔和、更自然的低饱和玫瑰色：

```text
主色：#C97882
阴影：#A05D63
```

要求：

- 不改变嘴型；
- 不放大嘴唇；
- 不做高亮唇彩；
- 不让唇色发红、发紫或发灰；
- 正、左、右可见脸方向保持一致；
- 总色板仍不超过 24 色（含透明）。

这一步属于确定性颜色微调，不允许为此单独调用 AI 生成。

## 3. 执行顺序

### 步骤 A：生成嘴唇微调参考

准备本轮参考帧：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-cleaned.png
-> 提取 down 帧 64×96
-> 将 #B85F6C 替换为 #C97882
-> 将 #8D4654 替换为 #A05D63
-> 输出 P2-3/input-down-soft-lips-64x96.png
-> 输出 8×唇部微调预览
```

该步骤不调用 PixelLab。

### 步骤 B：一次 PixelLab 四方向主生成

使用：

```text
模式：Standard / 4 directions
相机视图：high top-down
参考槽：down
参考图：input-down-soft-lips-64x96.png
页面显示预计费用：8 generations
Pro：不使用
提交次数：1
```

生成提示必须明确：

```text
Same blue-haired chibi whale-eared maid, preserve face, navy bob hair,
white headband, light-blue fin ears, navy-and-white outfit, ice-white apron,
waist bow, small whale tail, and soft natural rose lips.
Shorten the skirt hem enough to reveal two short legs and dark navy ankle
boots. In the front and back views the two legs must be separated by a small
transparent gap. In the left and right views show a readable near leg and a
small portion of the far leg. Keep feet planted at the same baseline.
Four cardinal views. Left and right must be real side poses, not mirrors.
Pixel art, transparent background, 96x96 per direction.
```

主生成失败后：

- B 只能提交失败证据并停止；
- 不允许自行再做第二次；
- 不允许用 Edit Image 反复补腿；
- 不允许手工绘制腿；
- 是否授权第二次生成由 Agent A 根据失败原因决定。

## 4. 生成后技术清理

继续执行与 P2-2 相同的确定性原则：

```text
原始四方向
-> 统一 64×96 单帧
-> 脚底接触边 y=88
-> 21～24 色含透明
-> Alpha 0/255
-> 256×96 精灵表
```

裁切规则：

- 找出四方向并集的合理 64 px 公共横向窗口；
- 四方向必须共用同一窗口；
- 不得按每帧 bbox 单独居中；
- 不得裁掉鳍耳、鲸尾、腿或鞋；
- 每方向至少保留 1 px 透明边。

方向映射：

```text
south -> down
west  -> left
east  -> right
north -> up
```

嘴唇最终必须包含：

```text
#C97882
#A05D63
```

如果生成结果唇色漂移，只能在嘴部区域做确定性颜色替换，不得重画脸部。

## 5. 必须交付

```text
art-source/character-v2/pixellab/P2-3/
  input-down-soft-lips-64x96.png
  lip-preview-8x.png
  sprite-4dir-raw.png
  sprite-4dir-raw.json
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  sprite-preview-checker-4x.png
  lower-body-preview-8x.png
  metrics.json
  visual-review.json
  map-preview-4dir.html
  map-desktop-4dir.png
  map-mobile-4dir.png
  credit-log.json

scripts/
  character_pixellab_p2_3_cleanup.py

docs/character-art-v2/pixellab/
  P2-3-report.md
```

`lower-body-preview-8x.png` 必须把四方向腰部至脚底区域并排放大，能直接看出腿、两腿间隔、靴子和 y=88 基线。

## 6. metrics 最低要求

```text
source_sha256
output_sha256
sheet_size
frame_size
direction_order
common_crop_window
direction_bboxes
foot_baseline_y
foot_anchor_x
leg_visible_height_by_direction
boot_color
colors
alpha_values
semi_transparent_pixels
lip_colors
generation_submissions
generations_used
pixellab_calls
animation_started
production_modified
```

所有字段填实际值。

## 7. 验收条件

### 硬性通过

- 四方向均为同一角色；
- 四方向全部可见腿和鞋；
- down/up 能明显看出两条腿；
- left/right 有真实侧向结构差异；
- 腿部与裙摆连接自然，不悬空、不畸形；
- 两个鞋底/接触边统一到 y=88；
- 48×72 地图尺寸下仍能看出腿；
- 唇色为柔和自然玫瑰色；
- 嘴型与 P2-2 相同；
- 24 色以内，Alpha 0/255；
- 不触边、无明显白底或彩边；
- 不调用除这一次四方向生成之外的 AI；
- 不修改正式运行时。

### 直接失败

- 仍是长裙遮住全部腿；
- 只有一只脚或两只脚粘成一整块；
- 腿像悬空短线；
- 鞋和地面分离；
- 鲸尾、鳍耳或服装主体漂移；
- 为补腿重画了脸；
- 嘴唇过红、发紫、发灰或形状变大；
- 使用左右镜像冒充两个侧向；
- B 自行追加生成或手工画角色。

## 8. 停止门

```text
P2-3 未通过：P3-0 idle 继续锁定
P2-3 通过但用户未确认：仍不开始动画
P2-3 与用户视觉门都通过：只授权 P3-0 idle 四方向四帧
```

## 9. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。P2-2 技术验收通过，但用户要求增加可见的腿，并把嘴唇色调再柔和一点。本轮创建 codex/character-art-pixellab-p2-3，从 89c491d 开始。

这轮只做 P2-3：
1. 先把现有 down 帧的唇色 #B85F6C -> #C97882，阴影 #8D4654 -> #A05D63，不改变嘴型；
2. 用该帧作为 PixelLab Standard 4 方向参考，只提交一次，预计 8 generations；
3. 提示 PixelLab 缩短裙摆，露出两条短腿和深蓝短靴，down/up 两腿有 1～2px 透明间隔，left/right 有近腿和少量远腿，不能镜像；
4. 输出仍统一 64×96、21～24 色、Alpha 0/255、256×96、脚底 y=88；
5. 交 8×下半身预览、8×嘴唇预览、桌面/手机 48×72 地图截图、metrics、credit-log 和可复现清理脚本。

不要手工画腿，不要 Edit Image 反复修补，不要做第二次生成，不要开始 idle/walk，不要修改生产。
如果腿仍被裙子遮住、脚悬空、两腿粘连或身份漂移，停止并报告；push 后等 A 验收。
```
