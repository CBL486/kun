# ART-V2 PixelLab P2-4 四方向静态角色验收

状态：技术 `PASS`；用户视觉确认 `PENDING`；idle 未授权
审查人：Agent A
执行人：Agent B
日期：2026-11-17
分支：`codex/character-art-pixellab-p2-4`
提交：`7b62880`

## 1. 验收结论

P2-4 通过技术验收。

四方向静态精灵表已建立，Down 使用已批准的双手母版，Left/Right 是真实侧向，Up 保留后发、背面服装和多腿/鞋跟结构。

## 2. 独立核验

```text
输出：256×96 RGBA
单帧：64×96
方向：down / left / right / up
色板：22（含透明）
Alpha：0/255
半透明像素：0
Down 与批准母版逐像素一致：true
Left/Right 镜像差异比：0.30254184748915064
四个方向鞋底接触边界：y=88
```

四方向 bbox：

```text
down ：(7,27,57,88)
left ：(19,21,58,88)
right：(18,22,62,88)
up   ：(13,22,57,88)
```

输出哈希：

```text
6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

独立复跑四方向清理脚本两次，输出哈希一致。

## 3. 视觉检查

通过：

- Down 保留柔唇、双手和短裙露腿；
- Left/Right 朝向正确，差异比证明不是镜像；
- 两侧均能看到近侧腿和靴子；
- Up 有后发、背面服装、腰带区域和腿/鞋跟；
- 四方向鲸尾方向正确，北向自然遮挡合理；
- 四方向都有小尺寸手部，不再出现大圆拳；
- 棋盘格下没有白底、杂边或半透明边缘。

地图预览：

```text
桌面：1440×1000
手机：390×844
运行时角色：48×72
方向切换水平位移：0 px
Console errors：0
```

## 4. 文档小问题

报告正文写垂直校正为：

```text
left -2 / right -5 / up -2
```

实际 `metrics-4dir-clean.json` 和脚本输出为：

```text
left -3 / right -6 / up -3
```

实际最终 bbox、脚底基线和画面均正确。该项是文档笔误，不阻塞素材验收，但应在后续整理时修正记录。

## 5. 回归与边界

```text
262 passed, 1 warning
node --check web/app.js：通过
有效四方向生成：1 次
generations_used：1
Edit Image：0
手工补画：0
动画：0
正式运行时：未修改
```

警告为既有 Starlette/httpx 弃用提示。

## 6. 状态

```text
P2-4 技术验收：PASS
P2-4 用户视觉门：PENDING
P3-0 idle：未授权
正式运行时：未修改
```

用户确认四方向最终效果后，才下发 P3-0 idle 四方向四帧任务书。不得直接把静态素材接入生产。
