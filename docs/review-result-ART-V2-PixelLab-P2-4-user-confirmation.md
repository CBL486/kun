# ART-V2 PixelLab P2-4 用户视觉确认

状态：用户视觉 `PASS`；P2-4 正式作为 P3-0 动画母版；生产仍未接入
记录人：Agent A
日期：2026-11-17
用户反馈：还不错，继续安排任务

## 1. 用户确认

P2-4 四方向静态角色获得用户认可。

确认内容：

- 四方向构图可用；
- 短裙、双腿与短靴可用；
- 两只小手比例可接受；
- Down 保留当前角色身份；
- Up 的背面结构可用；
- 地图 48×72 表现可用。

## 2. 冻结母版

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
256×96 RGBA
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

方向顺序：

```text
down / left / right / up
```

## 3. 状态

```text
P2-4 技术验收：PASS
P2-4 用户视觉门：PASS
P3-0 idle：已授权
walk / turn / stop：未授权
生产接入：未授权
```

## 4. 已知非阻塞项

P2-4 报告正文的垂直校正数字与实际 metrics 有一像素笔误：

```text
报告正文：left -2 / right -5 / up -2
实际脚本：left -3 / right -6 / up -3
```

最终 bbox、脚底基线和图像均正确。该问题不阻塞动画制作，但后续汇总时应以 metrics 和最终资产为准。

## 5. 下一步

```text
docs/agent-B-character-art-v2-pixellab-p3-0-idle-taskbook.md
```

P3-0 只做 idle 四方向四帧，不允许扩展到 walk 或其他动作。
