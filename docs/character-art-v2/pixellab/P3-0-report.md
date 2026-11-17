# ART-V2 PixelLab P3-0 Idle down Proof 报告

状态：`BLOCKED — FACE AND SILHOUETTE DRIFT`

日期：2026-11-17

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p3-0-idle`

起点：`7b62880`

任务书提交：`bf4ff47`

## 1. 冻结母版

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
256×96 RGBA
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

Down frame 0 直接使用 P2-4 已批准静态帧。

## 2. PixelLab down proof

```text
端点：POST /v2/characters/animations
模型：Animation v3
character_id：7b4646da-32b0-4ac6-8e40-f66082036224
animation_group_id：e75f8be6-873e-4f99-b41d-177cd0f170ea
animation_id：6ec43bc7-ec2f-46f7-b144-168221ae89e3
任务 ID：674934b7-a715-4c6c-937b-0b4cfadb5de1
请求帧数：4
keep_first_frame：true
平台返回帧数：5
实际使用：frame 0 使用批准母版，frame 1～3 使用生成帧
实际计费：1 generation
请求 seed：20261120
平台返回 seed：571592768
```

只提交 down，没有生成 left/right/up。

## 3. 技术清理

```text
平台帧尺寸：112×112
统一公共裁切窗口：(24,8,88,104)
输出帧：64×96
proof sheet：256×96
frame0 与 P2-4 逐像素一致：true
frame 1～3 垂直校正：0 / +1 / 0
色板：22
Alpha：0/255
半透明像素：0
```

proof：

```text
art-source/character-v2/pixellab/P3-0/idle-down-proof-4f.png
SHA-256: A2DDEDB6EC3BA1C0F3059B4E15D477780336FF5ABC0A3D284897CACECD680DD9

art-source/character-v2/pixellab/P3-0/idle-down-proof-4f-preview-8x.png
```

## 4. 失败证据

帧 bbox：

```text
frame 0：(7,27,57,88)
frame 1：(8,13,58,88)
frame 2：(8,11,59,88)
frame 3：(7,11,60,88)
```

虽然四帧鞋底均在 `y=88`，但角色轮廓顶部从 `y=27` 跳到 `y=13`、`y=11`，
超出允许的 1 px 呼吸幅度。

面部区域变化像素：

```text
frame 1 vs frame 0：876
frame 2 vs frame 0：1111
frame 3 vs frame 0：1267
```

可见问题：

- frame 2、3 的柔唇从微笑变成明显张嘴；
- 眼睛和脸部逐帧重绘；
- 头带、头发和身体轮廓明显拉伸；
- 鲸尾和手部动作超过 1 px；
- frame 3 回到 frame 0 的循环变化为 2003 px，无法连续。

相邻帧变化像素：

```text
0→1：1424
1→2：1564
2→3：1738
3→0：2003
```

这不是轻微 idle，而是模型重新生成了角色动作和表情。

## 5. 停止门

```text
P3-0 down proof：FAIL
left/right/up 提交：0
同方向重试：0
walk/turn/stop：未开始
正式运行时：未修改
```

按任务书停止 PixelLab 当前 idle 生成路线，等待 A 决定是否改用 skeleton
模板、WorkBuddy/Miora 或其他受控动画方案。

## 6. 预算

```text
生成前余额：1965.9
本次消耗：1 generation
生成后余额：1964.9
购买/升级：0
```

## 7. 回归

```powershell
.\scripts\test-b7.ps1
```

结果：

```text
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。
