# ART-V2 PixelLab P2-1 验收与会员建议

状态：软件可用，P2-1 仍需一次定向修补；建议开 PixelLab Tier 1 月付
审查人：Agent A
日期：2026-11-15
分支：`codex/character-art-pixellab-p2`
提交：`d033cad`

## 1. 结果结论

PixelLab 的软件能力评价：**值得开会员**。

理由：

- 一次 8-generation 的四方向生成成功；
- 输出了 south / west / east / north 四个方向；
- west 与 east 不是简单镜像；
- 南、西、东三个方向的蓝发、鲸鳍耳、蓝白女仆服、围裙、鲸尾和玫瑰唇色都能读出；
- 北向的后发和衣服背面可读；
- 目前的问题主要是鲸尾在背面被衣服遮挡，以及原始输出需要 64×96 技术清理。

这不是“软件不会做”，而是角色设计与相机视角的局部遮挡问题。

## 2. P2-1 阻塞

```text
north：后发 PASS
north：衣服背面 PASS
north：鲸尾 FAIL（被身体/裙摆遮挡，不可读）
```

南、西、东通过。

P2-1 当前不能直接包装成最终运行时资源，但可以继续使用 PixelLab 做一次局部 inpainting 或重新选择视角。

## 3. 会员建议

### 推荐：Tier 1 Pixel Apprentice

官方价格：

```text
$12/月
2,000 generations/月
图像最大 320×320
地图生成
文字/骨架动画
基础旋转和编辑
商业使用许可***
```

为什么够用：

- 我们的角色精灵是 64×96；
- 96×96 或 200×200 的中间资产也足够；
- 2,000 次/月远超当前需求；
- Tier 1 已包含地图生成，这正是做场景/环境需要的；
- 不需要 Tier 2 的 512×512 和优先队列。

### 不建议立即开 Tier 2 / Tier 3

- Tier 2 `$24/月`：5,000 generations、512×512、优先队列；
- Tier 3 `$50/月`：10,000 generations、最高优先级；
- 当前角色和地图尺寸用不到 512×512；
- 除非后面大量批量生成场景、NPC、动画，否则没必要。

建议先开 **Tier 1 月付**，不要直接年付。确认账号和商业条款后再考虑年付。

## 4. PixelLab 能做什么

### 能做角色

- 单张像素角色；
- 4 方向；
- 8 方向；
- 旋转；
- 文字动画；
- 骨架动画；
- 自动动画；
- inpainting；
- 换装和风格一致性。

### 能做场景和环境

官方首页确认支持：

- scene generation；
- environments；
- textures；
- tilesets；
- game maps；
- top-down / side-scrolling maps；
- isometric support；
- map generation。

### 能做 UI 和物件

- Menu Items；
- Buttons；
- Health Bars；
- object creator；
- props、states、animations。

### 适合和不适合

最适合：

- 像素角色精灵；
- 四/八方向；
- 动作动画；
- 地图、tileset、场景、像素 UI。

不适合作为唯一工具：

- 1024 高精度商业角色主视觉；
- 复杂剧情 CG；
- 高度定制的品牌插画。

后者继续使用已经验证的 WorkBuddy / Miora 主视觉路线。

## 5. P2-1R 定向修补

在购买会员后，B 只允许做一次 PixelLab 局部修补，不得自己补画。

目标：

- 只处理 north 视角的鲸尾；
- 保持后发、衣服背面、腰后蝴蝶结不变；
- 让鲸尾从裙摆左侧或右侧露出一小段可识别轮廓；
- 不改变 south / west / east；
- 使用 PixelLab 的 inpainting 或局部生成；
- 参考 P1/P2 的鲸尾形状和深蓝色板。

如果 inpainting 无法自然补出鲸尾，B 必须停止，不得手工画尾巴。

### P2-1R 交付

```text
art-source/character-v2/pixellab/P2/
  north-tail-fixed.png
  sprite-4dir-fixed.png
  sprite-4dir-fixed-preview-4x.png
  metrics-4dir-fixed.json

docs/character-art-v2/pixellab/P2-1R-report.md
```

通过后再统一：

```text
64×96
21～24 色
Alpha 0/255
脚底基线 y=88
```

## 6. 软件评价

评分（针对本项目）：

| 项目 | 评分 |
| --- | ---: |
| 角色生成质量 | 8/10 |
| 四方向能力 | 8/10 |
| 左右非镜像 | 9/10 |
| 动画潜力 | 9/10 |
| 场景/地图能力 | 8/10 |
| 价格 | 9/10 |
| 高精度主视觉 | 5/10 |

最终定位：

> PixelLab 做主角色游戏精灵、地图、Tileset、场景和像素 UI；WorkBuddy/Miora 做主视觉和角色设定锚点。

## 7. 最终建议

```text
现在值得开 PixelLab Tier 1 月付
不购买 Tier 2 / Tier 3
先做 north 鲸尾局部修补
通过后继续 64×96 清理和动作
```

购买动作必须由项目所有者确认，不由 B 自动完成。
