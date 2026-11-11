# ART-V2 PixelLab 角色游戏素材任务书 V1

状态：推荐执行；先做免费试用，不自动购买订阅
编写人：Agent A
日期：2026-11-11
执行人：Agent B
审查人：Agent A
目标分支：`codex/character-art-pixellab`
生产边界：B 不接触生产服务器、VNC、RDP、SSH、生产 `.env`、API Key、数据库或真实用户数据；不修改 `main`，不部署。

## 1. 最终工具决定

工具组合：

```text
主视觉锚点：WorkBuddy / Hy4 / miora-brand-design / miora_edit_image
游戏像素资产：PixelLab
技术清理：Aseprite（本机已安装）
可选校验：Retro Diffusion 免费工具
可选备选：Scenario Pro
```

如果只能选择一个新的主工具，选 **PixelLab**。

原因：

- 直接面向像素游戏资产；
- 支持 4 方向/8 方向视图；
- 支持文字动作、骨架动画和自动动画；
- 支持风格参考、init image、inpainting、re-posing、换装；
- 有 Aseprite/Pixelorama 集成和 API；
- 免费试用不需要信用卡，适合先验证效果；
- 比纯文生图和普通插画模型更接近最终可播放的精灵。

## 2. 为什么不继续用单一通用生图

角色项目有两个不同阶段：

| 阶段 | 最擅长工具 | 产物 |
| --- | --- | --- |
| 主视觉/角色锚点 | WorkBuddy/Miora | 1024 商业概念图、表情、角色卡 |
| 游戏精灵/动画 | PixelLab | 64×96 四方向、walk/idle、sprite sheet |
| 像素后处理 | Aseprite / Retro Diffusion | 色板、Alpha、网格、拼表 |

通用图像生成模型无法稳定输出精确网格、脚底基线、动作帧和四方向结构。PixelLab 专门解决这些问题。

## 3. 当前视觉母版

唯一主参考：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

目标角色：

- 19 岁成年女性；
- 深海蓝长发、浅蓝发尾；
- 左右鲸鳍耳；
- 鲸尾；
- 蓝白女仆/学院式服装；
- 鲸尾腰扣；
- 圆脸、大蓝眼、略丰满但不幼态；
- 现代像素叙事 RPG 风格；
- 48×72 游戏尺寸仍可识别。

原始网络参考图只作为气质参考，不进入发布包；不得 1:1 复制第三方角色、真人、文字、UI 或品牌标识。

## 4. 先做免费试用，不先付费

PixelLab 当前提供免费试用入口，页面明确写明无需信用卡。B 必须先用免费额度做验证。

只有以下条件全部通过，A/项目所有者才考虑购买：

1. 能导入现有主形象作为参考或 init image；
2. 能生成风格一致的角色；
3. 能生成 4/8 方向；
4. 能导出透明背景或可用背景；
5. 能导出精灵表；
6. 能在 48×72 下保留鲸鳍、服装和鲸尾；
7. 商业使用条款已经由项目所有者确认。

不得自动扣费、订阅或升级 PixelLab/Scenario 账号。

## 5. 分阶段执行

### P0：免费试用冒烟

B 要交：

```text
docs/character-art-v2/pixellab/P0-capability-report.md
art-source/character-v2/pixellab/P0/
```

验证：

- 上传视觉母版；
- 用 PixelLab 的 image-to-pixel art/init image/style reference 能力；
- 生成 1 张 64×96 或平台最接近的像素角色；
- 检查背景、色板、Alpha 和轮廓；
- 记录实际额度消耗、模型、参数和导出格式。

P0 失败条件：

- 不能使用参考图；
- 不能生成人物；
- 不能导出可处理图片；
- 输出只是普通插画；
- 无法确认商业使用边界。

P0 失败，停止，不购买，不进入 P1。

### P1：四方向静态角色

P0 通过后，使用同一参考和同一 seed/role 生成：

- down；
- left；
- right；
- up；
- 3/4 补充。

要求：

- 同一服装、鲸鳍耳、鲸尾和腰扣；
- 左右不是镜像；
- 背面可见后发、衣服背面和鲸尾；
- 导出后进入 Aseprite 做技术性对齐。

### P2：64×96 运行时精灵

PixelLab 负责生成角色与动作，B 只做确定性处理：

```text
PixelLab 角色/动画导出
-> 透明背景
-> 64×96 网格
-> 16～24 色
-> Alpha 0/255
-> 脚底基线 y=88
-> 256×96 精灵表
```

硬指标：

```text
四方向表：256×96
单帧：64×96
运行时：48×72
颜色：16～24（含透明）
Alpha：0/255
无抗锯齿、无渐变
角色主体不触边
鳍耳、服装、鲸尾、腰扣可读
```

### P3：动画

P2 通过后再做：

- idle 4 帧；
- walk 6 帧；
- turn 4 帧；
- stop 3 帧；
- study 4 帧；
- sit 4 帧；
- talk 4 帧。

优先使用 PixelLab 的 skeleton/text animation 或 animation-to-animation；如果没有合适的动作工具，允许使用已授权的动作骨架辅助，但不能重设计角色。

### P4：真实游戏接入与验收

交：

- 真实 `web/index.html` 桌面 1440×1000；
- 手机 390×844；
- 四方向截图；
- 玩家 rect 48×72；
- 控制台错误 0；
- manifest、哈希和测试。

## 6. 视觉验收

在第一眼和 48×72 下必须像“蓝色大肥鱼少女”，而不是普通蓝发小人。

至少保留：

- 大鲸鳍耳；
- 蓝白女仆/学院服装；
- 冰白围裙；
- 鲸尾；
- 鲸尾腰扣；
- 圆脸大眼；
- 略丰满但有身体的成年人比例。

如果 PixelLab 的四方向动作很顺，但角色被简化成普通蓝发 Q 版角色，仍然不通过。

## 7. 工具故障切换

### PixelLab 失败

先不购买订阅，切 Scenario Pro 试用或使用 Scenario 免费额度做一次角色一致性测试；Scenario Starter 当前官方页面为 1500 monthly credits / $15 起，但不得自动购买。

### PixelLab 动作不自然

使用 PixelLab 生成静态四方向，再用 Aseprite 或项目已授权的动作骨架补齐动作；角色造型仍以 PixelLab 输出为准。

### PixelLab 只能输出大图

使用 Retro Diffusion 的免费 Pixel Art Fixer、Sprite Sheet Slicer、Sprite Sheet Maker 做技术清理和拼表；不得重新设计角色。

## 8. 禁止

- 不自己从零画角色主体；
- 不用程序化几何图形重画；
- 不把 1024 图直接缩放成 64×96；
- 不删除 AIGC 标识；
- 不自动购买 PixelLab/Scenario 订阅；
- 不把参考图 1:1 复制进项目；
- 未通过 P2 不批量做动画；
- 不接触生产环境。

## 9. 给 B 的首条启动消息

```text
你是 AI World 项目的 Agent B。小云雀会员已过期，本轮改用 PixelLab 做游戏像素素材，WorkBuddy/Miora 只保留为主视觉锚点。

从最新 origin/main 创建 codex/character-art-pixellab。

先读取：
docs/agent-B-character-art-v2-workbuddy-miora-taskbook.md
docs/agent-B-character-art-v2-pixellab-taskbook.md
art-source/character-v2/workbuddy/2026-11-10/README.md

唯一视觉母版：
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png

只做 P0 免费试用：
1. 上传视觉母版；
2. 测试 image-to-pixel/init image/style reference；
3. 生成 1 张最接近 64×96 的测试角色；
4. 检查轮廓、服装、鳍耳、鲸尾和背景；
5. 记录免费额度和实际参数；
6. 不购买订阅，不做动画，不改运行时；
7. 完成后 push 分支并停止。

如果 PixelLab 不能保持参考角色，停止报告，不要自己画。
```
