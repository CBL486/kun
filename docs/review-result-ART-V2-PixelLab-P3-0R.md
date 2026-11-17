# ART-V2 PixelLab P3-0R 确定性 Idle 验收

状态：技术 `PASS`；用户视觉确认 `PENDING`；P3-1 walk 未授权
审查人：Agent A
执行人：Agent B
日期：2026-11-17
分支：`codex/character-art-pixellab-p3-0r-idle`
提交：`6d34656`

## 1. 验收结论

P3-0R 通过技术验收。

本轮没有 AI 重绘角色，只对已批准的四方向静态像素做确定性次级运动。脸、嘴、躯干、手、腿和靴子保持原像素。

## 2. 独立核验

```text
Sheet：256×384 RGBA
单帧：64×96
方向：down / left / right / up
每方向帧数：4
色板：22
Alpha：0/255
半透明像素：0
输出 SHA-256：2277C5B0B4D4C50F40D0246C87828C16197C4A5AA0F83B8A58E5C0D42D510B69
```

四方向 bbox 全部逐帧不变：

```text
down ：(7,27,57,88)
left ：(19,21,58,88)
right：(18,22,62,88)
up   ：(13,22,57,88)
```

Frame 0 与 P2-4 对应静态帧逐像素一致；Frame 2 与 Frame 0 逐像素一致。四方向鞋底接触边界全部为 y=88。

相邻帧变化像素：

```text
down ：8 / 8 / 7 / 7
left ：14 / 14 / 12 / 12
right：14 / 14 / 13 / 13
up   ：12 / 12 / 12 / 12
```

变化局限于尾巴或发梢次级区域，没有脸部、嘴、躯干、手和腿部漂移。

## 3. 动画文件核验

```text
WebP：4 帧，5 FPS，loop=0
GIF：4 帧，200ms/帧，5 FPS，loop=0，disposal=2
Down proof WebP：4 帧，5 FPS，loop=0
```

透明背景和循环信息正常，没有帧累积、拖影或伪平滑。

## 4. 地图核验

```text
桌面：1440×1000
手机：390×844
运行时角色：48×72
方向切换横向偏移：0 px
Console errors：0
```

## 5. 可复现性与回归

连续运行 idle rig 脚本两次，输出哈希一致。

```text
262 passed, 1 warning
node --check web/app.js：通过
```

警告为既有 Starlette/httpx 弃用提示。

## 6. 预算与边界

```text
AI 生成调用：0
PixelLab 调用：0
generation 消耗：0
walk / turn / stop：未开始
正式运行时：未修改
生产数据：未接触
```

## 7. 状态

```text
P3-0R 技术验收：PASS
P3-0R 用户视觉门：PENDING
P3-1 walk：未授权
正式运行时：未修改
```

需要用户在原始 5 FPS 速度下查看 Idle WebP/GIF，确认这种“静态身体 + 1 px 尾部/发梢摆动”的轻微呼吸感足够自然。确认后才下发 P3-1 walk。
