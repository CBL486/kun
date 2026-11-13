# ART-V2 PixelLab P0 审查结果

状态：CONDITIONAL PASS
审查人：Agent A
日期：2026-11-13
分支：`codex/character-art-pixellab`
提交：`153c357`
父基线：`b93eae4`

## 1. 结论

PixelLab 的“图像到像素艺术”能力可用，并且输出明显优于 B 之前自己绘制的版本：

- 蓝发、鲸鳍耳、蓝白女仆服、冰白围裙和鲸尾都能辨认；
- 角色轮廓完整；
- 是实际像素网格，不是低分辨率图片简单缩放；
- 可以作为后续游戏精灵的生成起点。

但本次仍是测试结果，不是运行时资源，不能直接进入 P1/P2。

## 2. 通过项

```text
参考图导入：PASS
像素化生成：PASS
单角色完整性：PASS
关键视觉特征：CONDITIONAL PASS
PNG 导出：PASS
```

输出：

```text
art-source/character-v2/pixellab/P0/candidates/pixellab-p0-image-to-pixel-64.png
64×64
RGBA
206 色
Alpha 全 255
```

对照图：

```text
art-source/character-v2/pixellab/P0/candidates/pixellab-p0-comparison.png
```

## 3. 未通过项

### 3.1 尺寸错误

PixelLab 本次输出 `64×64`，不符合运行时目标 `64×96`。原因是输入参考被保存为 `256×256`，平台按输入画幅生成。

修复要求：

- 不使用这次 64×64 直接放大；
- 重新制作一张 **256×384** 的 2:3 技术输入参考；
- 用同一张角色母版居中放置，补足背景，不改变角色造型；
- 让 PixelLab 输出 64×96 或最接近的 2:3 结果；
- 不再把 64×64 强行拉伸。

### 3.2 背景不透明

当前输出是浅色不透明背景，不能直接进入地图。

修复要求：

- 优先使用 PixelLab 自带背景移除；
- 如果平台不允许，使用确定性纯色背景抠图；
- Alpha 必须是 0/255；
- 不允许把背景残留成半透明色块；
- 不使用人工重画角色来掩盖抠图问题。

### 3.3 色板过多

当前 206 色，不符合运行时 16～24 色。

修复要求：

- 使用 Aseprite/Retro Diffusion 的确定性色板量化；
- 先保留主轮廓、眼睛、头发、围裙、鲸尾和服装的层级；
- 不得通过重新生成一个不同角色来降色；
- 目标 21 色左右，硬上限 24 色。

### 3.4 四方向/动作能力尚未验证

本次只验证了免费标准模式的图片转像素，没有验证：

- 4 方向；
- 8 方向；
- walk/idle 动画；
- 骨架动画；
- 动作一致性。

这些能力在 PixelLab 的 Pro 工具中，免费标准模式不能当作已通过。

## 4. 下一步 P1

B 只能做技术验证，不得自己画角色：

1. 生成 256×384 的 2:3 输入参考；
2. 用 PixelLab 重新生成 64×96 结果；
3. 将背景清理为 0/255 Alpha；
4. 量化到 16～24 色；
5. 在 48×72 游戏尺寸下预览；
6. 再测试 PixelLab 的四方向能力；
7. 如果四方向必须 Pro，B 只能报告价格和试用结果，不得自动购买或订阅。

P1 交付：

```text
art-source/character-v2/pixellab/P1/
  input-2x3.png
  generated-64x96.png
  cleaned-64x96.png
  sprite-preview-4x.png
  metrics.json
  map-desktop-down.png
  map-mobile-down.png
  credit-log.json
```

P1 通过条件：

- 角色不是重新设计的另一个人；
- 鲸鳍耳、蓝白服装、围裙和鲸尾清楚；
- 64×96 真实尺寸；
- Alpha 只有 0/255；
- 16～24 色；
- 48×72 地图中可读；
- 4 方向或至少完整 4 方向能力有明确验证结果。

## 5. 购买边界

PixelLab 免费标准模式可以先完成 64×96、透明化和色彩量化测试，但 4/8 方向和动画属于 Pro 能力。

B 不得自动购买 Pro 订阅。需要 A/项目所有者确认预算后，才能使用 Pro 做四方向和动作测试。

## 6. 最终判断

```text
PixelLab 作为候选主工具：保留
P0：CONDITIONAL PASS
P1：允许继续，但只能做技术处理
P2：未开始
动画：未开始
生产接入：未开始
```

建议继续 PixelLab，不切回 B 自绘。
