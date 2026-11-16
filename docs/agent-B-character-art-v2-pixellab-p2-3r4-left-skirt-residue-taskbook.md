# ART-V2 PixelLab P2-3R4 左侧旧裙摆残留清理任务书

状态：授权执行；零 AI 生成；只清理左侧旧裙残留
编写人：Agent A
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p2-3r4`
起点：`3994f04`
生产边界：不修改正式运行时，不部署，不接触生产、密钥、数据库或真实用户数据

## 1. 本轮目标

清除 down 帧左腿外侧残留的旧长裙外缘，保留真实手臂、手腕、手和白袖口。

这不是重新造型，也不是补画身体，属于对 P2-3R2 遮罩外恢复残留的确定性清理。

## 2. 输入与参考

最终输入：

```text
art-source/character-v2/pixellab/P2-3R3/down-legs-microadjusted.png
SHA-256: 3FB4CBF62C854294220838E04C8DA3EDF9CE9E2C4CE5E354FB0843687F563683
```

辅助参考：

```text
art-source/character-v2/pixellab/P2-3R2/input-down-soft-lips-64x96.png
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-raw.png
art-source/character-v2/pixellab/P2-3R2/down-masked-edit-cleaned.png
art-source/character-v2/pixellab/P2-3R2/down-lower-body-mask.png
```

`down-masked-edit-raw.png` 只能作为“短裙后没有旧裙外缘”的形状参考，不得整体复制，也不得把其中的随机色差直接带入最终结果。

## 3. 残留位置

允许检查区域：

```text
x=8..18
y=72..88
```

重点候选：

```text
x=9..17
y=73..86
```

已知该区域内同时有：

- 手部皮肤；
- 白袖口/手腕边缘；
- 旧裙深蓝外缘；
- 旧裙轮廓黑线和白色裙边。

不能把整个矩形区域直接清空。

## 4. 清理判定

必须保留：

- 与上臂连接的皮肤像素；
- 手和前臂的连续轮廓；
- 白袖口/手腕结构；
- 与新短裙连接正常的服装边缘。

必须删除：

- 从手部附近继续向下延伸到左腿外侧的旧长裙外缘；
- 只属于旧裙底边、现在悬空的黑白斜条；
- 与新短裙轮廓不相连的旧裙碎点。

清理原则：

```text
删除旧裙残留 -> 设为透明
不移动手部
不补画新袖子
不重画腿
不修改左腿
不从 raw 图复制随机像素
```

## 5. 执行方式

编写确定性脚本：

```text
scripts/character_pixellab_p2_3r4_left_skirt_cleanup.py
```

脚本必须：

- 从 P2-3R3 输出读取；
- 只在允许区域修改；
- 使用显式 residue mask 标记待删除像素；
- 将待删除像素设为透明；
- 不改变任何保留像素；
- 生成 residue mask 可视化；
- 生成 before / after / diff；
- 重复运行输出哈希一致；
- 不使用网络、AI、随机数或外部生成服务。

建议先通过连通区域和颜色分类找出旧裙外缘，再由固定坐标/连通规则生成 residue mask。不得直接在画布上手工涂抹后不留记录。

如果旧裙边缘与手部在白袖口处发生不可分离重叠：

```text
停止清理并报告
不得猜测性删除手臂
不得手工重画手
```

## 6. 输出

```text
art-source/character-v2/pixellab/P2-3R4/
  down-left-skirt-cleaned.png
  left-residue-mask.png
  left-residue-mask-preview-16x.png
  down-left-cleanup-diff-16x.png
  down-left-cleanup-preview-12x.png
  runtime-48x72-preview-8x.png
  metrics.json
  visual-review.json

scripts/
  character_pixellab_p2_3r4_left_skirt_cleanup.py

docs/character-art-v2/pixellab/
  P2-3R4-report.md
```

## 7. 差异预览

`down-left-cleanup-diff-16x.png` 必须包含：

```text
BEFORE | RESIDUE MASK | AFTER | DIFF
```

要求能直接区分：

- 被删除的旧裙像素；
- 保留的手部像素；
- 未发生变化的腿和靴子；
- 区域外零变化。

## 8. metrics 最低字段

```text
input_sha256
output_sha256
allowed_region
residue_pixel_count
removed_pixels
preserved_skin_pixels
preserved_cuff_pixels
changed_pixels_outside_allowed_region
left_hand_bbox
left_leg_bbox
leg_gap_px
boot_sole_edges
colors
alpha_values
semi_transparent_pixels
generation_submissions
pixellab_calls
animation_started
production_modified
```

## 9. 硬性验收

必须通过：

- 左腿外侧不再有长条旧裙残留；
- 手上方和手部本身仍可辨认；
- 白袖口没有被误删成断臂；
- 删除后没有悬空碎点；
- 左腿、右腿和靴子完全不变；
- 允许区域外变化为 0；
- 总色板不超过 22；
- Alpha 仅 0/255；
- 48×72 下左侧轮廓干净；
- 零 AI 生成；
- 无手工重画。

直接失败：

- 把手一起删掉；
- 为了连接手腕重新画一条新手臂；
- 旧裙长条仍然可见；
- 出现新的悬空像素；
- 左腿或靴子发生变化；
- 使用 AI 重新生成；
- 区域外发生变化。

## 10. 停止门

```text
P2-3R4 未通过：down 帧不可进入四方向
P2-3R4 通过：等用户确认左侧轮廓
用户确认后：才允许制作完整四方向
P3-0 idle：继续锁定
```

## 11. 给 Agent B 的启动消息

```text
你是 AI World 项目的 Agent B。用户发现 P2-3R3 左腿旁边的长条不是腿，而是 P2-2 旧长裙左侧外缘残留。根因是 P2-3R2 遮罩外恢复把它带回来了，P2-3R3 的修改区域没有覆盖它。

创建 codex/character-art-pixellab-p2-3r4，从 3994f04 开始，只做 down 单帧残留清理。

输入：art-source/character-v2/pixellab/P2-3R3/down-legs-microadjusted.png
检查区域：x=8..18, y=72..88
只删除左腿外侧的旧裙斜向长条和悬空碎点，保留手、手腕、白袖口和正常短裙边缘。
不要清除整个矩形，不要手工重画手臂，不要移动左腿，不要改靴子，不要调用 AI。

写确定性 residue mask 和清理脚本，输出 BEFORE/MASK/AFTER/DIFF、12x 预览、48x72 预览、metrics 和报告。
允许区域外变化必须为 0；色板不超过 22，Alpha 仅 0/255。
如果旧裙和手无法安全拆分，停止报告，不得猜测。

push 后停止，不要开始四方向或动画。
```
