# ART-V2 PixelLab P2-1 四方向静态验证报告

状态：`BLOCKED — NORTH WHALE TAIL MISSING`

日期：2026-11-14

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2`

任务指令基线：`origin/main` `1148671`

分支实现基线：`0a9e70b` + P2-0 提交 `583429b`

P2-0 通过提交：`583429b`

## 1. 执行边界

本轮按 P2-1 指令只提交一次 PixelLab 四方向生成。

最终提交设置：

```text
生成模式：Standard
方向数：4
相机视图：high top-down
参考图：P2 lip-fixed-64x96.png
参考槽：South，1/4
PixelLab 显示费用：8 generations
Pro：未使用
订阅：未购买
动画：未开始
```

提交前曾进入 V3 新计费界面，但没有提交生成；切换到 Standard 后重新选择
四方向并上传参考图，然后执行唯一一次生成。

## 2. PixelLab 输出

生成记录：

```text
Character ID: 40f3ee77-9f90-4e23-b119-c91a24efe478
Name: Idle
Output: 96×96 per direction
Spritesheet: 384×96
Directions: 4
Direction order: south, west, east, north
View: high top-down
```

原始导出文件：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-raw.png
art-source/character-v2/pixellab/P2/sprite-4dir-raw.json
```

原始精灵表 SHA-256：

```text
02B6C148B3139932F4D6B703F7E1B1C4B40ECAD557DE357B515912C533FEB65A
```

## 3. 原始技术指标

```text
精灵表：384×96
单方向：96×96
总色板：29（含透明）
不透明色：28
Alpha：0/255
半透明像素：0
```

各方向不透明包围盒：

| 方向 | bbox | 宽 | 高 |
| --- | --- | --- | --- |
| south | `(27,27,77,88)` | 50 | 61 |
| west | `(34,26,75,90)` | 41 | 64 |
| east | `(22,28,63,92)` | 41 | 64 |
| north | `(29,26,67,90)` | 38 | 64 |

原始结果为 `96×96`。按任务停止门，在确认视觉是否通过前没有继续缩放、
换算到底线 `y=88` 或量化到 24 色以内。

## 4. 视觉验收

四方向证据表：

```text
art-source/character-v2/pixellab/P2/sprite-4dir-raw-preview-4x.png
```

通过项：

- south：蓝发、鲸鳍耳、白色头带、蓝白服装、围裙、玫瑰唇色和鲸尾可读；
- west：侧脸、鲸鳍耳、服装、腰扣和鲸尾可读；
- east：侧脸、鲸鳍耳、服装、腰扣和鲸尾可读；
- north：后发、服装背面和腰后蝴蝶结可读。

左右方向不是简单镜像：将 east 水平翻转后与 west 精确匹配的像素只占
不透明并集的 `28.4663%`。两者来自平台实际生成的不同侧面图。

阻塞项：

- north 背面帧看不到可辨认的鲸尾；
- 不能通过局部补画、镜像拼接或自行加尾巴修复，否则会违反任务书；
- 臀后的白色蝴蝶结可见，但鲸尾轮廓与深蓝裙摆融合，无法单独读出来。

结论：P2-1 视觉验收不通过，停止在原始导出。

## 5. 未继续产出的内容

按任务书停止门，以下内容没有制作：

```text
sprite-4dir-cleaned.png
sprite-preview-4x.png
map-desktop-down.png
map-mobile-down.png
idle / walk / 其他动画
```

原始输出保持 `96×96`、29 色，未包装成满足 `64×96`、21～24 色的通过版。

## 6. 额度

```text
本轮提交次数：1
Standard 四方向显示费用：8 generations
购买：0
订阅：0
Pro：未使用
可用余额：当前浏览器账户路由要求重新登录，未自动登录，因此未读取
```

## 7. 回归测试

使用项目标准入口：

```text
.\scripts\test-b7.ps1
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示，不影响测试结果。

## 8. 停止门与 A 决策

```text
P2-0 唇色：PASS
P2-1 四方向：BLOCKED
原因：north 背面鲸尾不可辨认
动画：未开始
生产接入：未开始
```

需要 Agent A 决定是否：

1. 接受背面鲸尾被身体遮挡这一视觉结果；或
2. 授权另一种相机视图或下一次受控生成来补足背面鲸尾。

Agent B 不自行补画，也不会在未获授权时再次生成。
