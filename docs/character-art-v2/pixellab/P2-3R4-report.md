# ART-V2 PixelLab P2-3R4 左侧旧裙摆残留清理报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-16

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-3r4`

起点：`3994f04`

任务书提交：`96e0d86`

## 1. 根因

P2-3R2 的 Inpaint 遮罩从 `x=16` 开始，而旧长裙左外缘仍延伸到
`x=9..15`。遮罩外恢复把这条旧长裙边缘带回最终图。P2-3R3 只修改
`x=19..40` 的腿和靴，没有覆盖该残留，因此用户看到左腿外侧仍有长条。

## 2. 输入

```text
art-source/character-v2/pixellab/P2-3R3/down-legs-microadjusted.png
64×96 RGBA
SHA-256: 3FB4CBF62C854294220838E04C8DA3EDF9CE9E2C4CE5E354FB0843687F563683
```

辅助参考仅用于区分短裙后的轮廓：

```text
art-source/character-v2/pixellab/P2-3R2/input-down-soft-lips-64x96.png
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-raw.png
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask.png
```

没有从 raw Inpaint 图复制像素。

## 3. 清理方式

确定性脚本：

```text
scripts/character_pixellab_p2_3r4_left_skirt_cleanup.py
```

允许区域：

```text
x=8..18
y=72..88
```

脚本使用显式 residue mask，将 48 个旧裙像素设为透明。未移动或重画手部，
未补画袖子，未修改两腿和两只靴子。

## 4. 保留结构

```text
手部连通区域 bbox：(12,72,17,79)
保留肤色像素：11
保留白袖口/手腕像素：6
允许区域内不透明连通区域：1
悬空碎片：0
左腿 bbox：(20,75,26,82)
右腿保持 P2-3R3 原状
腿间距离：6 px
双鞋底接触边界：y=88
```

## 5. 结果

```text
art-source/character-v2/pixellab/P2-3R4/down-left-skirt-cleaned.png
64×96 RGBA
SHA-256: 4B51182AA44702F47DB84B014B52DF5ADDD3CCA5D961B21177F85D5557D9B9A2
```

旧裙斜向长条以及随后暴露出的 1 px 悬空残边均已清除。清理后的允许区域只剩
一个与上方手臂相连的手/袖口连通区域，没有漂浮像素。

## 6. 技术指标

```text
residue_pixel_count：48
removed_pixel_count：48
changed_pixels_outside_allowed_region：0
colors：22
alpha_values：0/255
semi_transparent_pixels：0
generation_submissions：0
pixellab_calls：0
animation_started：false
production_modified：false
```

## 7. 预览

```text
art-source/character-v2/pixellab/P2-3R4/left-residue-mask.png
art-source/character-v2/pixellab/P2-3R4/left-residue-mask-preview-16x.png
art-source/character-v2/pixellab/P2-3R4/down-left-cleanup-diff-16x.png
art-source/character-v2/pixellab/P2-3R4/down-left-cleanup-preview-12x.png
art-source/character-v2/pixellab/P2-3R4/runtime-48x72-preview-8x.png
```

## 8. 确定性验证

连续运行脚本两次，输出哈希一致：

```text
4B51182AA44702F47DB84B014B52DF5ADDD3CCA5D961B21177F85D5557D9B9A2
```

## 9. 状态

```text
P2-3R4 技术检查：PASS
P2-3R4 用户视觉确认：PENDING
四方向腿型：未开始
P3-0 idle：继续锁定
正式运行时：未修改
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
