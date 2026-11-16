# ART-V2 PixelLab P2-3R4 左手可读性复查

状态：`CHANGES REQUESTED — HAND PRESERVED BUT NOT READABLE`
审查人：Agent A
日期：2026-11-16
用户反馈：左手仍然有问题

## 1. 复查结论

旧裙残留已经清除，这是通过项。

但左手本身不合格：

```text
手部 bbox：约 (12,72,17,79)
有效肤色：约 11 px
可见宽度：约 2～3 px
外形：偏细长竖条
```

当前区域虽然像素连续，但没有清晰的：

- 掌心；
- 拇指；
- 手腕连接；
- 独立的 1 px 白袖口边界。

在 48×72 下，它仍容易被看成一小条黑白布片，而不是一只手。

## 2. 验收标准错误

P2-3R4 只验证了“手还在、区域连续、没有悬空碎片”，没有把“手在游戏尺寸下能读成手”作为硬条件。

因此：

```text
P2-3R4 技术清理：保持通过
P2-3R4 左手视觉：FAIL
P2-3R4 整体用户视觉：CHANGES REQUESTED
```

## 3. 下一步策略

不再继续做简单的删除清理。需要对左手做一次范围极小的**遮罩局部重绘**。

本轮只处理左手和手腕：

- 不改旧裙清理结果；
- 不改腿和靴；
- 不改脸、鲸尾、服装主体；
- 不手工画出新手臂；
- 最多一次 PixelLab Inpaint v3；
- 失败则改走 WorkBuddy/Miora 锚点重做。

## 4. 下一步任务书

```text
docs/agent-B-character-art-v2-pixellab-p2-3r5-left-hand-taskbook.md
```
