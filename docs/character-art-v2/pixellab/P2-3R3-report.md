# ART-V2 PixelLab P2-3R3 腿部细节微调报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-16

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r3`

起点：`b62a152`

任务书提交：`4e34fc9`

## 1. 本轮范围

用户已确认 P2-3R2 的正面腿型、站姿和短靴方向，只要求对腿部细节进行微调。

本轮未重新生成角色，未调用 PixelLab、WorkBuddy、Miora 或其他 AI，仅通过确定性
像素脚本修改 down 单帧中的两条腿和两只短靴。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
64×96 RGBA
SHA-256: 625D0B1E11686BC9BD9217BC20507F3D66CC295E569DCC7A05BB6D06A1D041B6
```

没有使用 P2-3R2 的 raw Inpaint 图作为最终基础。

## 3. 修改边界

```text
左腿/左靴：x=19..28, y=73..89
右腿/右靴：x=31..40, y=73..89
```

两个区域之外的变化像素为 `0`。

## 4. 确定性修改

脚本：

```text
scripts/character_pixellab_p2_3r3_leg_detail.py
```

共修改 `62` 个像素：

```text
ankle_shadow：4
boot_body：28
boot_cuff：12
boot_highlight：2
boot_sole：12
boot_toe：4
```

具体处理：

- 脚踝外侧各增加 2 px 现有肤色阴影，形成膝盖到脚踝的轻微收束；
- 靴口收窄为 6 px，靴筒保持深蓝色层级；
- 每只靴子增加 1 px 冷蓝高光；
- 每只鞋头向外增加 1 px；
- 两只靴底均保留 1 px 深色接触线；
- 未修改手臂、手、裙摆、围裙、脸部、柔唇、头发、鳍耳或鲸尾。

## 5. 输出

```text
art-source/character-v2/pixellab/P2-3R3/down-legs-microadjusted.png
SHA-256: 3FB4CBF62C854294220838E04C8DA3EDF9CE9E2C4CE5E354FB0843687F563683
```

对比和预览：

```text
art-source/character-v2/pixellab/P2-3R3/down-legs-diff-12x.png
art-source/character-v2/pixellab/P2-3R3/down-legs-preview-12x.png
art-source/character-v2/pixellab/P2-3R3/runtime-48x72-preview-8x.png
```

## 6. 技术指标

```text
允许区域外变化像素：0
左腿像素宽度：y=76..77 为 6 px，y=79..81 为 4 px
右腿像素宽度：y=76..78 为 6 px，y=79..80 为 5 px，y=81 为 4 px
腿间透明间隔：6 px
靴口像素：14
冷蓝高光：2 px
两只鞋底：y=88
总色板：22
Alpha：0/255
半透明像素：0
```

腿仍为两条独立轮廓，脚踝比膝盖窄但没有变成 2～3 px 细线。

## 7. 确定性验证

连续执行脚本两次，输出哈希一致：

```text
3FB4CBF62C854294220838E04C8DA3EDF9CE9E2C4CE5E354FB0843687F563683
```

## 8. 边界确认

```text
AI 生成调用：0
PixelLab 调用：0
动画：未开始
正式运行时：未修改
生产数据：未接触
购买或升级：0
```

## 9. 状态

技术检查通过，等待用户视觉确认：

```text
P2-3R3：待用户确认
四方向腿型：未开始
P3-0 idle：继续锁定
```

## 10. 回归

```powershell
.\scripts\test-b7.ps1
```

结果：

```text
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示。
