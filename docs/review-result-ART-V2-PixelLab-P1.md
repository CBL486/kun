# ART-V2 PixelLab P1 验收结果

状态：PASS
审查人：Agent A
日期：2026-11-14
分支：`codex/character-art-pixellab-p1`
提交：`53b08f1`
父基线：`a085e20`

## 1. 验收结论

PixelLab P1 静态技术验证通过。

这次不是把 P0 的 `64×64` 拉伸，而是重新制作了 `256×384` 的 2:3 输入，并生成了新的 `64×96` 候选。

## 2. 技术指标

```text
输入参考：256×384
PixelLab 原始生成：64×96
清理后运行时源：64×96
运行时显示：48×72
颜色：21（含透明）
Alpha：0/255
半透明像素：0
脚底基线：y=88
不透明包围盒：x=11..60，y=27..87
```

通过。

## 3. 视觉验收

通过项：

- 蓝发和浅蓝发尾可读；
- 左右鲸鳍耳可读；
- 蓝白女仆/学院服和冰白围裙可读；
- 右侧鲸尾与裙摆分离；
- 圆脸、大眼和略丰满体态接近已批准母版；
- 48×72 地图尺寸下仍能识别为同一个角色；
- 没有明显的背景彩边和半透明污染。

保留意见：

- 这是 Q 版静态验证图，不是最终主视觉；
- 细节仍少于 1024 母版，但已经足以作为游戏精灵方向；
- 不能直接据此批量做动画，必须先过四方向身份一致性。

## 4. 地图证明

```text
art-source/character-v2/pixellab/P1/map-desktop-down.png
art-source/character-v2/pixellab/P1/map-mobile-down.png
```

- 桌面 1440×1000；
- 手机 390×844；
- 玩家实际 rect 48×72；
- 控制台错误 0；
- 使用等价本地地图预览，符合 P1 任务书允许范围。

通过。

## 5. 测试复核

B 报告中的 OpenAPI 快照失败是运行环境差异。使用项目标准 `.b6-deps` 后，单独重跑：

```text
test_checked_in_openapi_matches_runtime_schema：1 passed
```

P1 没有修改 API 或业务代码，因此不构成回归。

## 6. 四方向能力

PixelLab 的四方向入口已确认可见：

```text
PixelLab V3 Standard
模式：4 方向
页面费用：8 generations
Pro required: no
```

P2 允许做一次四方向静态验证，但不能把“入口存在”当成“四方向已通过”。

## 7. P2 下一阶段指令

B 从最新 `origin/main` 创建：

```text
codex/character-art-pixellab-p2
```

只完成四方向静态验证：

1. 使用 P1 的 64×96 静态结果为南向参考；
2. 用 PixelLab V3 Standard 的 4 方向流程生成一次；
3. 记录实际消耗、输出尺寸、方向和失败原因；
4. 将四方向结果统一到 64×96、21～24 色、Alpha 0/255；
5. 提交四方向接触表和桌面/手机地图截图；
6. 不制作 walk/idle；
7. 不购买 Pro，不订阅；
8. 若平台四方向结果身份漂移，停止并报告，不得自己重画。

P2 交付路径：

```text
art-source/character-v2/pixellab/P2/
  source-down-64x96.png
  sprite-4dir-raw.png
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  metrics.json
  map-desktop-down.png
  map-mobile-down.png
  credit-log.json

docs/character-art-v2/pixellab/P2-report.md
```

## 8. 最终判定

```text
P0：CONDITIONAL PASS
P1：PASS
P2：允许开始
动画：暂缓
生产接入：未开始
```

PixelLab 继续作为主工具；B 不得退回自己绘制。
