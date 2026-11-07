# R2 原创蓝鲸少女角色设计 V1

状态：待 R2 审查

日期：2026-11-07

## 1. 设计来源与版权边界

只使用任务书中的抽象方向：

- 深海蓝与蓝白配色；
- 轻盈、水光、鲸歌意象；
- 少女轮廓、长发、鳍状发饰；
- 安静、温柔但不软弱。

没有使用抖音原帧、Cosplayer 面部/服装、品牌标志或具体版权角色。当前环境没有
可用图片生成工具，也没有额外风格参考图片，因此采用 `native-pixel-authoring`
脚本直接创作原创像素，不声称由图像模型生成。

## 2. 色板

```text
outline    #06171F
deep blue  #0D2D42
hair       #174D70
hair light #2E7D9E
fin        #75D8D8
fin light  #C9FBF1
skin       #F0C7B8
skin shade #D79D92
coat       #183D55
coat light #2D6177
dress      #A8E8E5
white      #E9FFFB
eye        #092332
blush      #E99BA4
```

色板以冷蓝、青绿和少量暖肤色为主，避免高饱和霓虹色。

## 3. 轮廓语言

- 头发围绕头部形成稳定的深蓝外轮廓；
- 两侧鳍状发饰是最小识别特征；
- 外套形成向下收束的三角形；
- 裙摆使用浅青色，和地图草地/道路保持区分；
- 四方向保持相同身高、肩宽和脚步基线；
- 转身时只改变朝向和鳍饰位置，不改变身份特征。

## 4. 资源

```text
assets/characters/whale-girl/
  whale-girl-manifest.json
  lin-cheng-map.png
  portraits/
    lin-cheng-hero.png       1024×1024
    lin-cheng-calm.png        512×512
    lin-cheng-happy.png       512×512
    lin-cheng-low.png         512×512
    lin-cheng-focus.png       512×512
  sheets/
    idle-{down,left,right,up}.webp   4 frames
    walk-{down,left,right,up}.webp   6 frames
    turn-{down,left,right,up}.webp   4 frames
    stop-{down,left,right,up}.webp   3 frames
    study-{down,left,right,up}.webp  4 frames
```

地图逻辑画布为 64×96，运行时显示为 48×72，最近邻采样。所有地图资源保持透明背景。

## 5. 动画语义

- `idle`：4 帧、5fps、循环呼吸；
- `walk`：6 帧、9fps、循环步态；
- `turn`：4 帧、10fps、播放一次后回 idle；
- `stop`：3 帧、10fps、从移动过渡回 idle；
- `study`：4 帧、5fps、低动作阅读/书写循环；
- 四方向由 presence 的 `facing` 决定；
- `moving=true` 且 `animation=walk` 才播放 walk；
- 减少动态时固定 idle 首帧。

## 6. 可复现性

资源生成脚本：

```powershell
scripts/build-r2-assets.py
```

Manifest 记录每个文件的字节数和 SHA-256。标题、角色名、品牌文字均不写入美术资源。

## 7. 当前限制

- 原生脚本创作是几何化、轻量级像素风，不等同于高预算手绘动画；
- 当前运行时使用精灵表替代 Spine；
- `sit`、`talk` 目前回退到 idle；`study` 已由 R7 正式接入学习状态。
