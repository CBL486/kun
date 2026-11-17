# ART-V2 PixelLab P3-0 Idle 验收结论

状态：`FAIL — AI ANIMATION REDREW FACE AND SILHOUETTE`；P3-0R 确定性动画已授权
审查人：Agent A
执行人：Agent B
日期：2026-11-17
分支：`codex/character-art-pixellab-p3-0-idle`
提交：`ff9b334`

## 1. 验收结论

P3-0 Down proof 不通过。

PixelLab Animation v3 没有对已批准角色做局部 idle，而是重新生成了面部、头发和身体轮廓。结果不能作为 idle 动画。

## 2. 独立核验

```text
proof sheet：256×96
帧数：4
Frame 0 与 P2-4 Down 逐像素一致：true
色板：22
Alpha：0/255
四帧鞋底底部：y=87（接触边界 y=88）
```

四帧 bbox：

```text
frame 0：(7,27,57,88)
frame 1：(8,13,58,88)
frame 2：(8,11,59,88)
frame 3：(7,11,60,88)
```

Frame 1～3 的顶部从 y=27 跳到 y=13 / 11，远超允许的 1 px 呼吸范围。

整帧与 Frame 0 的变化像素：

```text
frame 1：1424
frame 2：1768
frame 3：2003
```

Frame 3 回到 Frame 0 也需要变化 2003 px，无法自然循环。

## 3. 视觉失败

- 柔唇从微笑变成张嘴；
- 眼睛和脸逐帧重绘；
- 头发、头带和身体轮廓明显拉伸；
- Hands 和鲸尾动作超过 1 px；
- 四帧是不同角色状态，不是轻微 idle。

因此 Frame 1～3 全部拒绝。

## 4. 执行合规

```text
Down 主提交：1
实际消耗：1 generation
Left/Right/Up 提交：0
同方向重试：0
手工补画：0
正式运行时修改：0
购买/升级：0
```

B 在 Down proof 失败后停止，没有继续烧额度，执行边界正确。

## 5. 决策

停止 PixelLab Animation v3 对已批准像素角色的直接重绘路线。

下一任务改为零 AI 的确定性次级运动 idle：

- 脸、躯干、手、腿和靴子保持原像素；
- 只对头发末端、鳍耳、裙摆边缘和鲸尾做 1 px 位移；
- Frame 0 固定为 P2-4 静态帧；
- Frame 2 回到静态帧；
- Frame 1 和 Frame 3 分别做相反方向 1 px 次级摆动；
- 先做 Down 证明，再扩展到四方向。

## 6. 状态

```text
P3-0：FAIL
P3-0R 确定性 idle：授权
walk / turn / stop：未授权
正式运行时：未修改
```

任务书：

```text
docs/agent-B-character-art-v2-pixellab-p3-0r-deterministic-idle-taskbook.md
```
