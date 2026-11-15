# ART-V2 PixelLab P2-1R 验收与 P2-1 最终判定

状态：P2-1R `FAIL`；P2-1 四方向 `PASS WITH OCCLUSION WAIVER`；P2-2 已授权
审查人：Agent A
执行人：Agent B
日期：2026-11-15
分支：`codex/character-art-pixellab-p2`
提交：`22ebab6`

## 1. 验收对象

本轮只验收 PixelLab Edit Image 对北向帧鲸尾的一次局部修补尝试：

```text
输入：art-source/character-v2/pixellab/P2/north-raw.png
输出：art-source/character-v2/pixellab/P2/north-tail-edit-attempt.png
工具：PixelLab Edit Image
模型：Standard
提交次数：1
显示消耗：1 generation
```

## 2. 技术核验

复跑 `scripts/character_pixellab_p2_raw_audit.py` 与检查 `metrics-p2-1r-attempt.json` 后确认：

```text
原图与结果尺寸：96×96
原 bbox：(29,26,67,90)
结果 bbox：(29,26,67,90)
新增不透明像素：1
删除不透明像素：0
颜色变化像素：1821
结果总色板：135（含透明）
Alpha：0/255
尾巴轮廓向外扩展：否
```

唯一新增的不透明像素为 `(59,55)`，没有形成新的尾巴剪影。与此同时，1821 个原有像素被重新着色，已经超出“只局部补尾巴、其余保持不变”的授权范围。

## 3. 视觉核验

通过：

- 后发可读；
- 背面服装可读；
- 腰后蝴蝶结可读；
- 角色身份轮廓仍然存在。

失败：

- 北向仍看不到鲸尾剪影；
- 鲸尾没有从裙摆左侧或右侧露出；
- 结果不满足 P2-1R 的任务目标。

结论：`P2-1R FAIL — REJECT`。该结果不得进入精灵表，不得替代北向原图。

## 4. P2-1 最终判定

P2-1R 的提示词式修补已证明不可靠，不再继续烧额度尝试同一件事。

修订验收规则：

```text
北向必须可读：后发、服装背面、腰后蝴蝶结、脚部与整体身份
北向允许：鲸尾被身体或裙摆自然遮挡
身份保证：由 south / west / east 三个可见鲸尾的方向共同承担
```

按此规则，P2-1 原始四方向结果判定为：

```text
south：PASS
west：PASS
east：PASS
north：PASS WITH NATURAL TAIL OCCLUSION
```

该判定属于视觉规范修订，不是把 P2-1R 判为通过。P2-1R 永久保持失败记录，不再继续修补。

## 5. 额度与账号

```text
P2-1R 实际提交：1 次
P2-1R 实际消耗：1 generation
P2-1 + P2-1R 记录消耗：9 generations
PixelLab Tier 1：Active
B 自行购买/升级：0
Pro：未使用
```

没有发现 B 自动购买、升级或触碰生产环境的行为。

## 6. 当前遗留问题

P2-1 原始导出仍不是运行时资源，尚需完成：

1. 将每帧 `96×96` 无损裁切为 `64×96`；
2. 将方向顺序映射为 `down / left / right / up`；
3. 统一脚底接触边到 `y=88`；
4. 将 29 色确定性收敛到 21～24 色；
5. 保持 Alpha 仅为 `0/255`；
6. 生成 `256×96` 四方向精灵表；
7. 在真实地图中按 `48×72` 检查桌面和手机可读性；
8. 由用户完成最终风格确认。

这些问题统一进入 P2-2，不再继续使用 AI 生成或手工补画。

## 7. 最终决策

```text
P2-1R：关闭，失败，不采用
北向鲸尾：允许自然遮挡
继续生成 / Inpainting：停止
P2-2 静态清理：授权
动画：P2-2 和用户视觉门通过前不开始
生产接入：未授权
```

下一步任务书：

```text
docs/agent-B-character-art-v2-pixellab-p2-2-cleanup-taskbook.md
```
