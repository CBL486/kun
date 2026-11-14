# ART-V2 PixelLab P2-0 唇色验收与 P2-1 指令

状态：P2-0 PASS，P2-1 已授权
审查人：Agent A
日期：2026-11-14
分支：`codex/character-art-pixellab-p2`
提交：`583429b`

## 1. P2-0 验收结果

通过。

B 只修改了嘴部 4 个像素：

```text
(29,53) #B5A9BC -> #B85F6C
(30,53) #B5A9BC -> #B85F6C
(31,53) #B5A9BC -> #B85F6C
(30,54) #FAD4CA -> #8D4654
```

变化包围盒：

```text
(29,53,32,55)
```

眼睛、头发、鳍耳、服装、围裙和鲸尾均未改变。

## 2. 技术指标

```text
尺寸：64×96
总色板：23（含透明）
Alpha：0/255
半透明像素：0
变化像素：4
变化区域：mouth-only
输出 SHA-256：59DBED82B0CB2E3FE5D1E55F7428CE1B139891D383943BC00DFFF2EBC745AF79
```

通过。

## 3. 视觉检查

8× 预览：

```text
art-source/character-v2/pixellab/P2/lip-fixed-preview-8x.png
```

检查：

- 嘴唇是自然低饱和玫瑰色；
- 嘴线下方有 1 px 阴影；
- 不再出现蓝色、青色、紫色或灰色嘴唇；
- 像素边缘和原 P1 保持一致。

通过。

## 4. 回归

项目标准测试：

```text
262 passed, 1 warning
```

warning 为既有 Starlette/httpx 弃用提示，不影响。

## 5. P2-1 执行指令

B 现在只能做一次四方向静态验证。

使用输入：

```text
art-source/character-v2/pixellab/P2/lip-fixed-64x96.png
```

工具：

```text
PixelLab V3 Standard
4 方向
页面显示费用：8 generations
不购买 Pro
不订阅
```

要求：

1. 使用修正后的下方向作为南向参考；
2. 生成 down、left、right、up 四方向；
3. 保持蓝发、鲸鳍耳、蓝白服装、围裙、鲸尾腰扣和鲸尾；
4. 唇色在可见脸部方向保持自然玫瑰色；
5. 左右方向不能是镜像；
6. 输出统一到 64×96、21～24 色、Alpha 0/255；
7. 交四方向接触表；
8. 交真实桌面 1440×1000 和手机 390×844 的 48×72 地图截图；
9. 记录 8 generations 的实际消耗；
10. 不制作 idle/walk，不接生产。

P2-1 结果路径：

```text
art-source/character-v2/pixellab/P2/
  source-down.png
  sprite-4dir-raw.png
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  metrics-4dir.json
  map-desktop-down.png
  map-mobile-down.png

docs/character-art-v2/pixellab/P2-1-report.md
```

如果 PixelLab 四方向结果出现身份漂移、服装变化、鳍耳消失或鲸尾丢失，停止报告，不允许 B 自己补画。

## 6. 给 B 的启动消息

```text
P2-0 唇色已通过。现在执行 P2-1 四方向静态验证。

从 codex/character-art-pixellab-p2 继续，输入使用：
art-source/character-v2/pixellab/P2/lip-fixed-64x96.png

只做一次 PixelLab V3 Standard 4 方向生成，页面显示 8 generations。
不购买 Pro，不订阅。保留参考图身份，生成 down/left/right/up。
统一到 64×96、21～24 色、Alpha 0/255，并交四方向接触表、
桌面/手机 48×72 地图截图、metrics-4dir.json 和 credit-log.json。

如果身份漂移或关键特征丢失，停止报告，不要自己画。
不制作 idle/walk，不改生产。
```
