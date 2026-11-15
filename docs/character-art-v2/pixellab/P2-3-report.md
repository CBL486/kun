# ART-V2 PixelLab P2-3 腿部可见性与嘴唇微调报告

状态：`BLOCKED — NO READABLE LEGS OR BOOTS`

日期：2026-11-15

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3`

起点：`89c491d`

## 1. 本轮范围

本轮只处理：

1. 将嘴部改为更柔和的玫瑰色；
2. 通过一次 PixelLab Standard 四方向主生成，让裙摆下出现两条短腿和
   深蓝短靴。

本轮没有开始动画，没有修改正式运行时，没有购买或升级会员。

## 2. 柔唇输入

来源：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-cleaned.png
```

确定性修改 4 个嘴部像素：

```text
(25,53) #B85F6C -> #C97882
(26,53) #B85F6C -> #C97882
(27,53) #B85F6C -> #C97882
(26,54) #8D4654 -> #A05D63
```

输出：

```text
art-source/character-v2/pixellab/P2-3/input-down-soft-lips-64x96.png
SHA-256: 77FB41D39AC16C839246EAAA12FDEC438F270CCE76973FA7E1B20B70E333940B
```

8× 前后对比：

```text
art-source/character-v2/pixellab/P2-3/lip-preview-8x.png
```

嘴唇形状与修改范围保持正确。

## 3. PixelLab 主生成

执行设置：

```text
模式：Standard
方向：4
相机视图：high top-down
参考槽：down
参考图：input-down-soft-lips-64x96.png
页面显示费用：8 generations
提交次数：1
Pro：未使用
```

生成结果：

```text
Character ID: b7e2cd64-af72-4f75-98a6-180c450bce4c
尺寸：96×96
方向：4
输出：south / west / east / north
```

## 4. 原始结果

原始四方向精灵表：

```text
art-source/character-v2/pixellab/P2-3/sprite-4dir-raw.png
384×96
SHA-256: FA891F6C00D1F7B00E4DA26F5DEB4D013782E16C7202B7521282E62DD3C4D437
```

导出元数据：

```text
art-source/character-v2/pixellab/P2-3/sprite-4dir-raw.json
```

原始指标：

```text
总色板：29（含透明）
不透明色：28
Alpha：0/255
半透明像素：0
```

各方向 bbox：

| 方向 | bbox | 底部接触像素 y |
| --- | --- | ---: |
| south | `(23,27,73,88)` | 87 |
| west | `(28,23,76,91)` | 90 |
| east | `(26,26,68,94)` | 93 |
| north | `(29,25,73,91)` | 90 |

## 5. 视觉验收

下半身 8× 预览：

```text
art-source/character-v2/pixellab/P2-3/lower-body-preview-8x.png
```

通过：

- 蓝发、白色头带、浅蓝鳍耳、服装主体和鲸尾保持同一角色；
- down/left/right/up 均为真实四方向；
- south/west/east 的鲸尾仍可读；
- north 的后发、背面服装和腰后蝴蝶结可读；
- 柔和玫瑰唇色 `#C97882` 与阴影 `#A05D63` 均出现在生成结果中。

直接失败：

- down 仍是长裙直接落到地面，没有两条独立短腿；
- up 仍然没有两条腿和鞋跟；
- left/right 没有可读的近侧腿与远侧腿；
- 四方向均没有独立的深蓝短靴；
- 因腿部完全未生成，无法按任务要求统一鞋底基线或制作有效地图对照。

结论：命中任务书的直接失败条件，不能进入技术清理。

## 6. 未继续产出的内容

按停止门未生成：

```text
sprite-4dir-cleaned.png
sprite-preview-4x.png
sprite-preview-checker-4x.png
map-preview-4dir.html
map-desktop-4dir.png
map-mobile-4dir.png
```

没有再次生成，没有调用 Edit Image，没有手工补腿或改角色。

## 7. 预算

```text
生成前会员用量：1 / 2000
本次提交：1
本次实际消耗：8 generations
预期生成后用量：9 / 2000
购买：0
升级：0
Pro：未使用
```

## 8. 回归

```text
.\scripts\test-b7.ps1
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。

## 9. 停止门

```text
P2-3：BLOCKED
原因：四方向均未生成可辨认的短腿和短靴
P3-0 idle：继续锁定
生产接入：未修改
```

需要 Agent A 根据这次失败决定是否调整生成策略或重新授权；B 不再自行生成
第二次，也不会手工绘制腿部。
