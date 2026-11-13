# ART-V2 PixelLab P1 执行指令

状态：A 已授权 B 执行，仅限 P1 技术验证
日期：2026-11-13
执行人：Agent B
审查人：Agent A
分支：`codex/character-art-pixellab-p1`
基线：`origin/main`，即 `cbfd9cc` 之后的最新提交
生产边界：B 不接触生产服务器、VNC、RDP、SSH、生产 `.env`、API Key、数据库或真实用户数据；不修改 `main`，不部署。

## 1. 前置判断

P0 已验证 PixelLab 可以：

- 导入角色参考；
- 生成完整单角色像素图；
- 保留蓝发、鲸鳍耳、蓝白女仆服、围裙和鲸尾；
- 导出 PNG。

P0 未通过：

- 目标 64×96；
- 透明背景；
- 16～24 色；
- 四方向和动画能力。

P1 只解决前三个技术问题，并验证四方向是否可用。

## 2. 本轮输入

唯一角色母版：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

P0 测试记录：

```text
docs/character-art-v2/pixellab/P0-capability-report.md
docs/review-result-ART-V2-PixelLab-P0.md
```

P0 输入缩略图：

```text
art-source/character-v2/pixellab/P0/inputs/lin-cheng-pixellab-reference-256.png
```

网上参考图只允许作为本地视觉参考，不进入发布包，不 1:1 复制原人物。

## 3. 必须完成的步骤

### P1-1：制作 2:3 输入参考

从角色母版制作一张：

```text
256×384
```

的技术输入参考。

要求：

- 角色完整；
- 角色不拉伸；
- 角色居中；
- 背景保持纯色或统一底色；
- 不改变脸、发色、鳍耳、服装、鲸尾和比例；
- 保存到：

```text
art-source/character-v2/pixellab/P1/input-2x3.png
```

这一步只允许做媒体排版和背景补足，不允许重画角色。

### P1-2：用 PixelLab 重新生成 64×96

使用 PixelLab 的 Image to Pixel Art 标准模式，输入 `input-2x3.png`。

输出要求：

- 优先得到 `64×96`；
- 如果平台只能输出其他尺寸，记录平台实际输出；
- 不允许把 P0 的 `64×64` 直接拉伸成 `64×96`；
- 不允许用重新生成的另一个角色代替；
- 保留平台原始导出文件和参数。

候选路径：

```text
art-source/character-v2/pixellab/P1/generated-64x96.png
```

### P1-3：透明背景和色板清理

如果 PixelLab 输出不是透明背景：

- 优先使用 PixelLab 自带背景移除；
- 否则用确定性纯色背景抠图；
- Alpha 最终只能为 0/255；
- 不允许抗锯齿彩边。

如果输出超过 24 色：

- 使用 Aseprite 或 Retro Diffusion 做确定性色板量化；
- 保留至少：轮廓、眼睛、头发、鳍耳、冰白围裙、深蓝服装、鲸尾；
- 目标 21 色左右，硬上限 24 色；
- 不得重新设计角色。

清理后文件：

```text
art-source/character-v2/pixellab/P1/cleaned-64x96.png
```

### P1-4：游戏尺寸证明

将清理结果按 48×72 放进真实 `web/index.html` 或等价本地预览。

交付：

```text
art-source/character-v2/pixellab/P1/map-desktop-down.png
art-source/character-v2/pixellab/P1/map-mobile-down.png
```

必须满足：

- 桌面 1440×1000；
- 手机 390×844；
- 玩家实际 rect 48×72；
- 控制台错误 0；
- 不是把大图贴在截图下方。

### P1-5：四方向能力验证

尝试 PixelLab 的四方向功能。

如果标准免费模式不可用：

- 记录 Pro 功能名称、是否收费、页面显示的价格；
- 不购买、不订阅、不升级；
- 停止在报告里，不进入动作制作。

P1 只验证能力，不批量制作七套动作。

## 4. 交付清单

```text
art-source/character-v2/pixellab/P1/
  input-2x3.png
  generated-64x96.png
  cleaned-64x96.png
  sprite-preview-4x.png
  metrics.json
  map-desktop-down.png
  map-mobile-down.png
  credit-log.json

docs/character-art-v2/pixellab/P1-report.md
```

`metrics.json` 至少包含：

```json
{
  "input_size": [256, 384],
  "generated_size": [0, 0],
  "cleaned_size": [64, 96],
  "runtime_size": [48, 72],
  "colors": 0,
  "alpha_values": [0, 255],
  "semi_transparent_pixels": 0,
  "baseline_y": 88,
  "console_errors": []
}
```

## 5. P1 通过条件

- 输入参考没有改变角色设计；
- 输出不是 P0 64×64 强行拉伸；
- 清理后为真实 64×96；
- 21 色左右，最多 24 色；
- Alpha 只有 0/255；
- 鲸鳍耳、蓝白服装、围裙、鲸尾可读；
- 48×72 地图中不是一团蓝块；
- 桌面/手机截图通过；
- 四方向能力有明确的可用或 Pro 阻塞报告。

## 6. 明确禁止

- 不自己从零画角色；
- 不用程序化几何图形补角色；
- 不把 64×64 直接拉伸；
- 不自动购买 PixelLab Pro；
- 不改生产资源；
- 不做 idle/walk 或其他动画；
- 不把带 AIGC 标识的原图直接裁进运行时；
- 不把参考图 1:1 复制进项目。

## 7. 完成后停止

B 完成后 push 分支并停止，等待 A 审查。A 没有通过 P1 前，不允许进入动作制作、表情批量生产或生产部署。

## 8. 给 B 的启动消息

```text
你是 AI World 项目的 Agent B。PixelLab P0 已判定 CONDITIONAL PASS。
现在只执行 P1 技术验证，不要自己画角色，不要购买 Pro。

从最新 origin/main 创建 codex/character-art-pixellab-p1。

先读取：
docs/character-art-v2/pixellab/P1-pixellab-execution-instruction.md
docs/review-result-ART-V2-PixelLab-P0.md
art-source/character-v2/pixellab/P0/credit-log.json

本轮完成：
1. 从已批准视觉母版制作 256×384 的 2:3 输入；
2. 用 PixelLab Image to Pixel Art 生成 64×96；
3. 清理透明背景和 16～24 色板；
4. 交 4× 预览、真实地图桌面/手机截图和 metrics.json；
5. 检查 PixelLab 四方向功能是否免费可用；
6. 如果是 Pro-only，只记录价格和阻塞，不购买、不订阅；
7. 不制作动作表，不改生产，不合并 main。

完成后 push 分支并停止。
```
