# ART-V2 WorkBuddy / Miora 角色美术任务书 V1

状态：替代小云雀路线，待执行
编写人：Agent A
日期：2026-11-11
执行人：Agent B
审查人：Agent A
目标分支：`codex/character-art-workbuddy-miora`
基线：最新 `origin/main`，执行前必须重新 fetch
生产边界：B 不接触生产服务器、VNC、RDP、SSH、生产 `.env`、API Key、数据库或真实用户数据；不修改 `main`，不部署。

## 1. 工具决定

小云雀会员已过期，本轮改用已经安装、已经验证可用的：

```text
WorkBuddy
  -> Hy4
  -> miora-creative-core
  -> miora-brand-design
  -> miora_edit_image
```

不使用普通 `miora-image-generation` 纯文生图，不使用 DeepSeek/GLM 生成角色主视觉。

选择理由：

1. WorkBuddy 已安装，不需要重新购买会员；
2. 已经用 `miora-brand-design + miora_edit_image` 生成过目前最接近目标的主形象；
3. 支持实际参考图输入、角色一致性、三视图和 IP 物料工作流；
4. 可以直接把参考图作为硬约束，避免模型自由发挥成普通蓝发动漫少女。

替代方案暂不采用：

- Scenario：适合更专业的角色一致性和 LoRA，但当前未配置账号和连接；
- Retro Diffusion：适合专门像素画，但角色多视图一致性仍需额外工作；
- Leonardo/Krea：可以做参考图，但不如 WorkBuddy 当前已验证的 Miora 角色链路直接。

## 2. 目标角色

视觉母版：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

目标：原创、商用级、适合像素叙事 RPG 的“蓝色大肥鱼少女”。

必须保留：

- 深海蓝长发和浅蓝发尾；
- 左右明显的鲸鳍耳；
- 鲸尾；
- 蓝白女仆/学院式服装；
- 鲸尾腰扣；
- 圆脸、大蓝眼、略丰满但明确是 19 岁成年人；
- 游戏尺寸下清楚的轮廓和服装层级。

不得 1:1 复制网上参考图、真人、原角色身份、文字、UI 或品牌标识。

## 3. B 的职责

B 负责：

- 在 WorkBuddy/Miora 中生成和筛选候选；
- 使用参考图驱动生成；
- 记录提示词、模型、参考图和实际积分；
- 对生成结果做技术性裁切、背景处理、色板量化、Alpha 清理、拼表和接入；
- 交游戏内截图、测试和 manifest。

B 不负责：

- 从零手绘角色主体；
- 用程序化几何图形重新设计头发、脸或衣服；
- 每次重新用文字生成不同角色；
- 直接拿 1024 图缩小成 64×96；
- 删除 AIGC 标识；
- 未经 A 批准制作批量动作。

## 4. 工作流

```text
参考图锁定
  -> WorkBuddy/Miora 生成主形象锚点
  -> 生成四方向角色设定
  -> 生成四方向静态精灵
  -> 技术性清理和 64×96 拼表
  -> 真实游戏截图
  -> 表情和角色卡
  -> 动作关键帧
```

每一步都必须使用同一张已批准锚点图作为后续参考，不能用文字重新描述一遍就重新生成。

## 5. 分阶段执行

### X0：工具与参考图冒烟

最多生成 1～3 张测试图。

必须确认：

- WorkBuddy 能读取本地参考图；
- Miora 的 `miora_edit_image` 能保持参考图的脸、发色、鳍耳、服装和鲸尾；
- 输出没有变成普通的蓝发少女或抽卡海报；
- 能保留平台 AIGC 标识；
- 记录实际生成方式和消耗。

交付：

```text
docs/character-art-v2/workbuddy-miora/X0-reference-smoke.md
art-source/character-v2/workbuddy-miora/X0/
```

若无法读取参考图，或一致性明显失败，B 停止报告，不进入 X1。

### X1：主形象锚点

交付：

- 3 张 1024×1024 主形象候选；
- 1 张选定锚点；
- 96×96 头像裁切；
- 112×112 角色卡预览。

通过条件：

- 看起来是蓝色大肥鱼少女，不是普通蓝发动漫少女；
- 鲸鳍耳、鲸尾、蓝白服装和腰扣都能看见；
- 圆脸和略丰满体态成立，但不幼态；
- A 批准锚点图。

### X2：四方向设定

以 X1 锚点图为唯一参考，生成：

- front；
- left；
- right；
- back；
- 3/4 补充图。

要求：

- 同一角色、同一服装、同一鳍耳和尾巴；
- 左右方向不是水平镜像；
- 背面能看见后发、服装背面和鲸尾；
- 角色比例一致。

### X3：四方向静态精灵

B 可以通过 WorkBuddy/Miora 生成关键姿态，再做确定性处理：

```text
Miora 生成四方向角色/姿态
-> 选候选
-> 背景去除
-> 64×96 逻辑帧
-> 16～24 色量化
-> Alpha 清理为 0/255
-> 脚底基线 y=88
-> 256×96 精灵表
```

硬指标：

```text
单帧：64×96
运行时：48×72
颜色：16～24（含透明）
Alpha：0/255
无抗锯齿、无渐变
角色主体不触边
四方向可辨
鳍耳、服装、鲸尾、腰扣可读
```

### X4：真实游戏证明

必须在真实 `web/index.html` 中显示：

- 桌面 1440×1000；
- 手机 390×844；
- 四方向；
- 玩家 rect 48×72；
- 控制台错误 0；
- 不是把概念图贴在截图下方。

### X5：表情和角色卡

X3 通过后再做：

- 1024 主视觉；
- calm、happy、low、focus、tired、curious、shy 七个表情；
- 96×96 头像；
- 112×112 角色卡；
- 58×64 桌面对话头像；
- 40×47 手机对话头像；
- `mood_label` 映射完整。

### X6：动作

X3 和 X5 通过后，按顺序制作：

- idle 4 帧；
- walk 6 帧；
- turn 4 帧；
- stop 3 帧；
- study 4 帧；
- sit 4 帧；
- talk 4 帧。

每段单独交接触表和真实截图。

## 6. 预算纪律

WorkBuddy 的实际积分/额度以账户页面为准。B 不自行购买、不订阅、不升级账号。

每次生成记录：

- 模型/技能；
- 参考图；
- 提示词；
- seed（平台提供时）；
- 实际扣点；
- 候选路径；
- 采用或拒绝原因。

如果额度不足以完成当前阶段，B 停止并报告，不得用程序化自绘替代。

## 7. 停止门

```text
X0：参考图冒烟失败即停
X1：主形象不批准不继续
X2：四方向不一致不继续
X3：静态精灵不通过不继续
X4：真实游戏截图不通过不进入 X5
X5：表情/角色卡不通过不进入 X6
X6：动作全部通过后进入 R4
```

## 8. 给 B 的启动消息

```text
你是 AI World 项目的 Agent B。小云雀路线已经停止，本轮改用已经安装的 WorkBuddy/Miora。

先读取：
docs/agent-B-character-art-v2-workbuddy-miora-taskbook.md
art-source/character-v2/workbuddy/2026-11-10/README.md

从最新 origin/main 创建 codex/character-art-workbuddy-miora。

本轮只做 X0：
1. 使用 WorkBuddy 的 miora-creative-core + miora-brand-design；
2. 必须使用 miora_edit_image，参考图是
   art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png；
3. 做 1～3 张参考一致性测试图；
4. 记录模型、参考图、积分和结果；
5. 不生成动画，不改运行时，不接生产；
6. 完成后 push 分支并停止。

如果 Miora 不能稳定保持参考图角色，停止报告，不要自己画。
```
