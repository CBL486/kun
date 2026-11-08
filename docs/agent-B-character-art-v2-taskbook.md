# Agent B 角色美术资源重制任务书 V2

状态：待执行
编写人：Agent A
编写日期：2026-11-08
执行人：Agent B
审查人：Agent A
基线仓库：`origin/main`
编写时基线提交：`f802c3aeca06da89b3e2768af27c3f4000d204b3`
执行分支：`codex/character-art-v2`
美术工具：小云雀（约 1500 积分，具体扣点以平台实时账单为准）
生产边界：B 不接触生产服务器、VNC、RDP、SSH、生产 `.env`、API Key、数据库、真实用户数据；不修改 `main`，不部署。

## 1. 任务目的

当前角色资源只是“功能占位级”，还不适合作为产品主角色长期展示。本轮只重做主智能体林澄的角色美术与运行时动画，不重做小镇地图、建筑、UI 或四名 NPC。

目标是把林澄从“几何像素占位角色”升级为：

- 有明确、可记忆的蓝鲸少女视觉身份；
- 头像、立绘、地图小人和动作语义属于同一个角色；
- 在 48×72 的实际游戏尺寸下仍能一眼认出；
- 有可信的行走、转身、学习、坐下和交谈动作；
- 能接入现有 `character-player.js`、资源 manifest 和测试体系；
- 有完整来源、积分消耗和批准记录，不混入未经授权的真人或 IP 素材。

本轮不是“多做几张好看的图”，而是交付一套能进入游戏、能验收、能继续迭代的角色资产包。

## 2. 当前资源审计

现有资源目录：

```text
assets/characters/whale-girl/
  whale-girl-manifest.json
  lin-cheng-map.png
  portraits/
    lin-cheng-hero.png        1024×1024
    lin-cheng-calm.png        512×512
    lin-cheng-happy.png       512×512
    lin-cheng-low.png         512×512
    lin-cheng-focus.png       512×512
  sheets/
    idle-{down,left,right,up}.webp
    walk-{down,left,right,up}.webp
    turn-{down,left,right,up}.webp
    stop-{down,left,right,up}.webp
    study-{down,left,right,up}.webp
```

已确认的问题：

| 资源 | 当前问题 | 本轮目标 |
| --- | --- | --- |
| 1024 主视觉 | 由低分辨率几何图形放大，像素块巨大，缺少头发、服装、光影和表情细节 | 重新制作真正可用的半身主视觉 |
| 512 表情图 | 五官变化少，主要是眉毛和嘴部替换，情绪辨识弱 | 重做 6 个有明确情绪差异的表情 |
| 64×96 地图小人 | 轮廓过于几何化，鳍状发饰像三角块，角色像通用占位小人 | 重绘有蓝鲸身份的四方向小人 |
| walk 动画 | 帧间变化小，手脚和衣摆动作不足，转身与移动方向不够明确 | 按标准步态重做 |
| turn 动画 | 更像整体左右倾斜，不像真实转身 | 明确表现朝向变化和发饰惯性 |
| study 动画 | 学习动作可读性弱，接近 idle 变化 | 明确手持书本、低头阅读和翻页动作 |
| sit / talk | API 和 UI 已有语义，但没有专用动画 | 新增四方向 sit 与 talk 精灵表 |
| 整体风格 | 角色细节密度明显低于小镇和室内背景 | 提升到与背景匹配的现代像素游戏品质 |

## 3. 范围

### 3.1 必须完成

1. 林澄原创蓝鲸少女视觉锁定。
2. 1024×1024 主视觉 1 张，透明背景。
3. 512×512 表情 7 张：calm、happy、low、focus、tired、curious、shy。
4. 四方向完整角色设定图：front、left、right、back。
5. 64×96 四方向运行时精灵表。
6. 下列动作全部四方向完成：
   - idle：4 帧，5 fps，循环；
   - walk：6 帧，9 fps，循环；
   - turn：4 帧，10 fps，单次；
   - stop：3 帧，10 fps，单次；
   - study：4 帧，5 fps，循环；
   - sit：4 帧，4 fps，循环；
   - talk：4 帧，6 fps，循环。
7. 更新 `web/character-player.js`，让 `sit` 和 `talk` 播放对应动作，不再回退到 study/idle。
8. 更新 manifest、测试、截图和交接文档。

### 3.2 本轮不做

- 不重做四名 NPC；
- 不重做小镇地图、建筑、室内和 UI；
- 不引入 Spine 正式工程和新付费骨骼软件；
- 不做完整剧情 CG；
- 不做 3D 模型；
- 不使用未经授权的视频原帧、真人照片、Cosplayer 面部或服装复刻；
- 不为了美术改产品功能、记忆系统或聊天逻辑。

## 4. 视觉方向

### 4.1 风格定位

采用“高细节动漫像素头像 + 高辨识度 Q 版四方向地图角色”的组合：

- 主视觉和表情图：现代像素插画，允许较细的头发分层、衣料明暗、眼瞳高光和柔和边缘；
- 地图角色：64×96 逻辑画布，2.3～2.5 头身，减少细节但保留身份轮廓；
- 角色与背景：角色必须比背景更亮、更清晰，蓝色轮廓在绿地、灰路和夜间场景中都能辨认；
- 不采用写实 Cosplay 头像，不直接复制视频人物。

### 4.2 可参考的抽象特征

可人工查看用户提供的参考视频：

```text
https://v.douyin.com/Su5Ob3EiyaI/
```

只提取以下抽象方向：

- 深海蓝、青绿、蓝白的色彩关系；
- 鲸鳍/鱼鳍形状的发饰意象；
- 长发与轻飘衣摆形成的柔和轮廓；
- 安静、温柔、但眼神有主见的角色气质；
- 水光、贝壳、鲸歌等海洋意象。

不得：

- 下载或使用视频原帧；
- 复刻真人的脸、发型细节、服装版型或镜头构图；
- 使用水印、账号名、品牌标识或可识别真人特征；
- 把参考视频中的人物直接称为本项目角色。

### 4.3 角色身份锁定

- 姓名：林澄；
- 年龄：19 岁；
- 身份：生活在青禾镇的主智能体；
- 轮廓：长深蓝发、两侧鳍状发饰、轻盈但不过度暴露的蓝白服装；
- 服装：深海军蓝短外套 + 冰青白内搭 + 轻微鲸尾/波纹扣饰；
- 面部：清晰眼睛、小鼻点、柔和但不空洞的嘴形；
- 主识别色：深海蓝、青绿、冰白；
- 辅助色：低饱和暖肤色和极少量暖金扣饰；
- 禁止：过度霓虹、过多装饰、角色头部比例忽大忽小、和 NPC 相同的通用脸。

### 4.4 建议色板

```text
outline    #071B26
deep navy  #0B2C43
hair dark  #123F5A
hair mid   #1D6688
hair light #43A4B7
fin glow   #8AF1E4
fin highlight #D9FFF8
skin       #F2C9B8
skin shade #D5968B
coat       #173C56
coat light #2C667A
blouse     #E9FFFB
dress      #9FE7E8
eye        #0C3344
eye glow   #69D9DF
blush      #E6A0A8
gold clasp #D8B36A
```

地图小人建议控制在 16～24 个有效颜色；主视觉可以使用更丰富的同色阶，但不得出现与角色无关的高饱和杂色。

## 5. 技术规格

### 5.1 主视觉与表情

| 项目 | 规格 |
| --- | --- |
| 主视觉 | 1024×1024 RGBA PNG，透明背景，半身或膝上构图 |
| 表情 | 512×512 RGBA PNG，透明背景 |
| 表情差分 | calm、happy、low、focus、tired、curious、shy |
| 头像裁切 | 以头部为中心，缩到 96×96 时仍能看清头发、鳍饰、眼睛和服装领口 |
| 光照 | 柔和顶部偏左光，避免复杂背景光影响透明边缘 |
| 输出 | 不使用平台水印、边框、文字、账号信息和临时 UI |

### 5.2 地图精灵

| 项目 | 规格 |
| --- | --- |
| 逻辑帧尺寸 | 64×96 |
| 运行时显示 | 48×72 |
| 方向 | down、left、right、up |
| 采样 | 最近邻，无抗锯齿 |
| 背景 | 全透明 |
| 帧边距 | 角色主体四周至少 3 px 透明边距 |
| 脚底基线 | 每方向固定；允许呼吸浮动 ±1 px，不允许整体漂移 |
| 格式 | lossless WebP 精灵表 |
| 命名 | 保持现有 `{action}-{direction}.webp` 格式，新增 `sit-*`、`talk-*` |

### 5.3 动作语义

- idle：呼吸、发梢和衣摆轻微延迟摆动，脸部不抖；
- walk：必须有接触、下沉、通过、抬起四个可读阶段；
- turn：至少表现头部、肩膀、发饰和身体朝向的连续变化；
- stop：从移动姿态过渡到站稳，不能只跳回 idle；
- study：书本或纸笔必须在画面中可读，头部略低，至少 2 帧有翻页或书写动作；
- sit：坐姿稳定，腿部和衣摆不能穿模，不能直接缩放站立帧；
- talk：头部和一只手有轻微说话手势，嘴部或肩部有 2 帧变化，不能继续播放 idle。

## 6. 门控与 1500 积分预算

### 6.1 阶段结构

本轮采用以下门控：

```text
ART-V2-00A  小云雀能力与授权冒烟
ART-V2-00B  身份锁定与资源落点
Gate A      3 个风格方向
Gate B      主视觉 + 实际角色卡预览 + 96×96 裁切
Gate C      7 表情 + mood_label 映射
Gate D      四方向设定和关键姿态
Gate E1     idle / walk / turn / stop
Gate E2     study / sit / talk
Gate F      完整测试、截图、哈希与交接
```

这个顺序是正确的。先确认工具能不能稳定产出可商用、干净、可落地的资源，再锁身份和路径，最后才批量画表情和动画。任何一门失败，后续阶段不得继续消耗积分。

### 6.2 积分分配

| 阶段 | 用途 | 积分上限 | 累计上限 | 通过条件 |
| --- | --- | ---: | ---: | --- |
| 00A 能力与授权冒烟 | 5～8 张工具验证图 | 50 | 50 | 透明、一致性、导出、授权可用 |
| 00B 身份与落点 | 不改图，只写设计锁定和资源映射 | 0 | 50 | 路径、文件名、动作和映射冻结 |
| Gate A 风格方向 | 3 个方向，每个方向 2 张缩略图 | 120 | 170 | A 选出唯一方向 |
| Gate B 主视觉锚点 | 3 个主视觉候选 + 2 次定向修正 + 裁切预览 | 300 | 470 | 实际角色卡和 96×96 可辨识 |
| Gate C 表情包 | 7 张表情 + 定向修正 + mood 映射 | 280 | 750 | 身份、情绪和映射全部通过 |
| Gate D 转面与关键姿态 | 四方向设定 + 5 类动作关键姿态 | 280 | 1030 | 轮廓、比例、手脚和衣装可动画 |
| Gate E1 基础动作 | idle / walk / turn / stop 的定向修正 | 120 | 1150 | 四方向基础动作和运行时截图通过 |
| Gate E2 生活动作 | study / sit / talk 的定向修正 | 100 | 1250 | 三种生活动作语义可读 |
| Gate F 完整验收 | 测试、截图、哈希和交接，不再生成 | 0 | 1250 | 全部交付和证据齐全 |
| R 保留 | 只在 A 明确批准时用于返工 | 250 | 1500 | 不自动消耗 |

### 6.3 预算原则

1. 1500 积分只用于视觉锚点、头像、设定图和关键姿态，不直接生成 100 多张运行时动画帧。
2. `00A` 最多花 50 积分。能力不满足时立即停止，不进入风格探索。
3. Gate B 通过前累计不得超过 470 积分。
4. Gate D 通过前累计不得超过 1030 积分。
5. Gate E2 通过前累计不得超过 1250 积分。
6. 最后 250 积分是返工预算，没有 A 的明确批准不得使用。
7. 每个阶段先记录实际扣点，再记录采用或拒绝。不能边生成边忘记预算。
8. E1/E2 的积分预算只用于关键姿态和失败处的定向重生成；逐帧补间、清理和拼表在本地完成。

### 6.4 积分记录要求

B 必须在 `art-source/character-v2/prompt-log.json` 记录：

```json
{
  "starting_credits": 1500,
  "spent_credits": 0,
  "remaining_credits": 1500,
  "generations": [
    {
      "id": "v2-00a-001",
      "stage": "capability_smoke",
      "prompt_id": "capability-transparent-character-v1",
      "tool_model": "platform-reported-model",
      "seed": "platform-value-or-null",
      "credits": 0,
      "output": "art-source/character-v2/candidates/00a-001.png",
      "accepted": false,
      "rejection_reason": ""
    }
  ]
}
```

禁止在日志中写入账号、密码、Cookie、API Key、订单号或支付信息。

## 7. 分阶段执行与门控

### ART-V2-00：基线与上下文

B 必须先：

1. `git fetch origin`；
2. 从最新 `origin/main` 创建 `codex/character-art-v2`；
3. 阅读：
   - `docs/character-design-r2-v1.md`
   - `docs/handoff-R2-character-art.md`
   - `docs/art-pipeline.md`
   - `assets/characters/whale-girl/whale-girl-manifest.json`
   - `web/character-player.js`
   - `web/app.js`
   - `web/index.html`
   - `tests/test_r2_assets.py`
   - `tests/test_b7_web.py`
   - `scripts/build-r2-assets.py`
4. 运行基线测试；
5. 备份现有运行时资源的 SHA-256 清单；
6. 建立 `art-source/character-v2/`、`docs/character-art-v2/` 和积分日志；
7. 不先覆盖现有运行时文件。

### ART-V2-00A：小云雀能力与授权冒烟

目标：在花大预算前确认小云雀真的能产出本项目需要的资源。

最多消耗：50 积分。

至少测试以下 5 项：

1. **透明或可抠图**：生成 1 张角色半身图，确认能否导出透明 PNG；若平台不提供透明背景，确认纯色背景是否能稳定抠图且没有发丝残边。
2. **身份一致性**：用同一参考图生成 3 张同角色不同表情，检查脸、发色、鳍饰和衣领是否明显漂移。
3. **清晰度**：生成 1 张 1024 级头像，确认不是低分辨率放大，发丝、眼睛和衣料有真实细节。
4. **干净导出**：确认导出文件没有平台水印、账号名、边框、按钮或临时 UI。
5. **授权可用**：由项目所有者确认账号和输出可用于本项目；如果无法确认商用/修改/再分发条款，停止并报告，不得进入 Gate A。

交付：

```text
art-source/character-v2/00a/
docs/character-art-v2/00a-capability-report.md
docs/character-art-v2/00a-credit-log.json
```

能力报告必须给出：

```text
透明导出：pass / fail
参考一致性：pass / fail / partial
1024 细节：pass / fail
干净导出：pass / fail
商用与修改授权：pass / fail / needs_owner_confirmation
推荐工作流：text2img / img2img / reference / edit
已知限制：
```

任一项为 `fail` 或 `needs_owner_confirmation`，B 停止，等 A 决定是否换工具。不得用“先生成再说”跳过。

### ART-V2-00B：身份锁定与资源落点

目标：在生成正式美术前固定角色身份、文件路径、运行时接口和表情映射。

消耗积分：0。

交付：

```text
docs/character-art-v2/identity-lock.md
docs/character-art-v2/asset-map.json
art-source/character-v2/approved/
```

`identity-lock.md` 必须冻结：

- 林澄的脸型、眼睛、发色、发型、鳍饰、服装、鞋、身高比例；
- 允许变化的 7 个表情；
- 禁止出现的真人特征、品牌和水印；
- 主识别轮廓和在 64×96 下的简化规则；
- 左右方向的非对称差异，禁止只做水平翻转；
- 参考视频只允许抽象提炼的边界。

`asset-map.json` 必须冻结：

- 所有运行时路径和文件名；
- 64×96 帧尺寸；
- 四方向；
- 七类动作及每类帧数、FPS、是否循环；
- 7 个表情文件名；
- `mood_label` 到表情文件的映射；
- 现有资源备份位置和回滚方式。

Gate 00B 通过后，B 才能开始 Gate A。

### Gate A：3 个风格方向

最多消耗：120 积分。

每个方向交付 2 张图：

1. 角色半身小样；
2. 角色与青禾镇地图同屏的 64×96 小人小样。

三个方向必须是真正的视觉取舍，例如：

- A：高细节动漫像素，头发和衣料层次最多；
- B：更简洁的 Q 版像素，地图识别性最强；
- C：介于两者之间，头像精致且地图小人不过度复杂。

每张候选都要给出：

- 在小云雀中的实际扣点；
- 96×96 和 48×72 的可读性；
- 与当前地图的协调度；
- 主要优缺点。

Gate A 只由 A 选一个方向。未选择前不得开始 Gate B。

### Gate B：主视觉锚点

最多消耗：300 积分。

交付：

- 3 个 1024×1024 主视觉候选；
- 选定候选的 2 次定向修正；
- 透明背景 PNG；
- 96×96 头像裁切；
- 112×112 实际角色卡预览；
- 58×64 和 40×47 对话头像预览；
- 实际 `web/index.html` 角色卡桌面和手机截图。

Gate B 通过条件：

- 不是低分辨率几何图放大；
- 头发、鳍饰、眼睛、领口和衣装有可信细节；
- 112×112 和 96×96 下仍能识别为林澄；
- 58×64 和手机 40×47 下不糊成色块；
- 与地图背景并排时不突兀；
- A 明确批准。

### Gate C：7 个表情与 mood_label 映射

最多消耗：280 积分。

当前 `mood_label` 的实际值有 5 个：

```text
平静      <- calm
专注      <- flow
有些疲惫  <- low
心情不错  <- excited
需要休息  <- tired
```

因此 6 张表情不够覆盖现有状态。建议交付 7 张：

| mood state | mood_label | 表情文件 | 用途 |
| --- | --- | --- | --- |
| calm | 平静 | `lin-cheng-calm.png` | 默认 |
| flow | 专注 | `lin-cheng-focus.png` | 学习、写作 |
| low | 有些疲惫 | `lin-cheng-low.png` | 低落、疲惫 |
| excited | 心情不错 | `lin-cheng-happy.png` | 开心 |
| tired | 需要休息 | `lin-cheng-tired.png` | 明显疲倦 |
| curious | 无当前公开 label | `lin-cheng-curious.png` | 探索、发现 |
| shy | 无当前公开 label | `lin-cheng-shy.png` | 关系互动、害羞 |

映射必须只有一个来源，推荐写入 `whale-girl-manifest.json`：

```json
{
  "mood_portraits": {
    "平静": "calm",
    "专注": "focus",
    "有些疲惫": "low",
    "心情不错": "happy",
    "需要休息": "tired"
  },
  "expression_fallback": "calm"
}
```

要求：

- 5 个现有 mood_label 全部有文件；
- 未知 mood_label 回退 `calm`；
- 7 张图的角色身份、发饰、衣领和色板一致；
- 情绪只通过眼睛、眉毛、嘴形和轻微头部姿态变化；
- 实际角色卡切换 5 个 mood_label 的截图齐全。

Gate C 通过后才能进入 Gate D。

### Gate D：四方向设定和关键姿态

最多消耗：280 积分。

交付四方向全身设定：

- front；
- left；
- right；
- back。

再交付以下关键姿态：

- idle 站立；
- walk 接触/通过姿态；
- study 阅读姿态；
- sit 坐姿；
- talk 说话手势。

要求：

- 衣着结构一致；
- 发型和鳍饰在背面仍可辨认；
- 角色比例一致；
- 左右方向有真实结构差异，不能只水平翻转；
- 先做平光、无透视夸张的设定图，再转为地图姿态；
- 每张关键姿态都标明准备用于哪一类动作和方向。

Gate D 只验证“可动画性”，不要求已经生成完整精灵表。失败时只重做失败的部分，不重做全套。

### Gate E1：idle / walk / turn / stop

积分上限：120，仅用于关键姿态修正。

交付：

- 四方向 idle 4 帧，5 fps，循环；
- 四方向 walk 6 帧，9 fps，循环；
- 四方向 turn 4 帧，10 fps，单次；
- 四方向 stop 3 帧，10 fps，单次；
- 256×96、384×96、192×96 等正确尺寸的 lossless WebP；
- 动作接触表；
- 实际游戏内移动、转身和停止截图。

Gate E1 通过条件：

- walk 有接触、下沉、通过、抬起阶段；
- 脚底基线漂移不超过 1 px；
- turn 能看出朝向变化；
- stop 不是直接跳回 idle；
- 发饰、发梢和衣摆有 1 帧延迟感；
- 角色移动和停止时没有明显抖动；
- 桌面和手机截图通过。

Gate E1 未通过，不得开始 E2。

### Gate E2：study / sit / talk

积分上限：100，仅用于关键姿态修正。

交付：

- 四方向 study 4 帧，5 fps，循环；
- 四方向 sit 4 帧，4 fps，循环；
- 四方向 talk 4 帧，6 fps，循环；
- 对应接触表和实际游戏截图；
- `web/character-player.js` 正确映射 `study`、`sit`、`talk`。

Gate E2 通过条件：

- study 中书本或纸笔可读，至少有阅读或书写变化；
- sit 不是站立帧缩小；
- talk 不是 idle 换名，头部或手部有说话动作；
- 三个动作在桌面和手机端都清晰；
- 减少动态模式固定 idle 首帧。

### Gate F：完整测试、截图、哈希与交接

积分消耗：0，只做本地验收。

必须交付：

- 1024 主视觉；
- 7 张 512 表情；
- 四方向 7 类动作，共 28 张运行时精灵表；
- 新版 manifest；
- 角色卡和对话头像的 mood 映射测试；
- 全部资源 SHA-256；
- 桌面 1440×1000 和手机 390×844 截图；
- idle、walk、study、sit、talk 的游戏内截图；
- 动作接触表；
- 浏览器控制台错误证据；
- 积分开始、已用、剩余和逐项账单；
- 来源、授权、提示词和 seed 记录；
- 最终交接文档。

Gate F 完成后 B 停止，等待 A 在 GitHub 审查和合并。B 不构建生产、不部署、不改 `main`。

## 8. 提示词模板

### 8.1 角色基础提示词

```text
原创角色美术，现代像素游戏角色，深海蓝鲸少女“林澄”，19岁。
角色身份：安静、温柔、有主见，带海洋和鲸歌意象，但不是动物拟人吉祥物。
外观：深海军蓝长发，两侧半透明青绿色鲸鳍发饰，冰白与深海蓝短外套，
内搭浅蓝白裙装，少量鲸尾或波纹金属扣饰，柔和但清楚的青绿色眼睛。
视觉：高细节动漫像素插画，清晰分层头发，细腻衣料明暗，水光高光，
深海蓝、青绿、冰白为主色，暖肤色作为面部焦点。
技术：角色主体完整，透明背景，无文字，无水印，无边框，无账号信息。
版权：原创设计，只参考抽象色彩和鲸鳍意象，不复刻真人脸、真人服装或已有IP角色。
```

### 8.2 主视觉提示词

```text
使用已批准的角色设定，生成林澄的 1024×1024 半身主视觉。
3/4 正面视角，头部到腰或膝上，身体自然放松，安静地看向观察者。
深蓝长发和青绿鲸鳍发饰形成明确轮廓，外套领口、冰白内搭和鲸尾扣饰清晰。
像素插画，真实像素簇，不使用低分辨率放大，不使用写实摄影质感。
透明背景，人物完整居中，四周留白，无文字、无水印、无平台标识。
```

### 8.3 表情差分提示词

```text
保持同一角色身份、同一脸型、同一发型、同一发饰和同一服装。
只改变表情和必要的头部角度，生成 512×512 透明背景头像。
当前表情：{calm|happy|low|focus|tired|curious|shy}。
不改变眼睛颜色、发色、服装结构和角色年龄。像素插画，清晰可读，无文字无水印。
```

### 8.4 四方向设定提示词

```text
同一角色的四方向全身角色设定图，分别生成正面、左侧、右侧、背面。
正交视角，平光，双脚基线一致，服装结构一致，发型和鲸鳍发饰在背面仍可识别。
现代像素游戏角色设定，颜色分层清楚，不夸张透视，不改变体型。
每个方向单独输出，不要拼成不可切割的复杂海报，不要文字和水印。
```

### 8.5 地图角色关键姿态提示词

```text
以已批准的四方向设定图为角色参考，生成 64×96 地图角色的关键姿态。
2.3～2.5 头身，Q版但保留林澄的长发、鲸鳍发饰、蓝白服装和眼睛颜色。
斜俯视 3/4 地图视角，透明背景，角色主体四周留透明边距，脚底基线固定。
当前姿态：{idle|walk contact|study reading|sit|talk gesture}。
只作为逐帧重绘参考，不直接作为运行时精灵表。
```

### 8.6 负面提示词

```text
低分辨率放大，几何色块，塑料脸，通用动漫脸，真人照片，Cosplay 复刻，
多余手指，手臂粘连，腿脚穿模，衣服结构变化，发饰消失，左右方向颠倒，
文字，水印，logo，边框，账号名，复杂背景，过度霓虹色，过多装饰，
不同角色混入，同一张图多个身体，非透明背景。
```

## 9. 验收标准

### 9.1 视觉验收

必须同时满足：

1. 1024 主视觉不是现有低分辨率像素图的简单放大；
2. 96×96 头像裁切和 112×112 实际角色卡仍能看出深蓝发、青绿鳍饰和蓝白服装；
3. 7 个表情能仅凭眼睛、眉毛和嘴形区分；
4. 四方向角色轮廓稳定，左右方向不是简单水平翻转；
5. walk 至少 4 个可读阶段，脚底不漂移；
6. turn 能看出朝向变化；
7. study 画面中书本/纸笔可读；
8. sit 不是站立帧缩短；
9. talk 不是 idle 换名；
10. 发饰、发梢和衣摆有轻微物理感，脸部不抖动；
11. 角色在草地、灰路、夜间背景、角色卡 112×112、对话头像 58×64 和手机 40×47 下都清晰；
12. 5 个现有 mood_label 均能切换到对应表情，未知值回退 calm。

### 9.2 技术验收

必须通过：

```text
pytest
test_r2_assets.py
test_b7_web.py
JavaScript syntax check
桌面 1440×1000 截图
手机 390×844 截图
浏览器控制台错误为 0
资源尺寸、Alpha、帧数、FPS、SHA-256 manifest 校验
减少动态模式
```

新增测试至少覆盖：

- 四方向七动作完整存在；
- 每个 sheet 的 `frames × 64 = width` 且 `height=96`；
- 每帧非空；
- walk 相邻帧不完全重复；
- 角色主体不触碰帧边界；
- `sit`/`talk` 在 player 中被正确选择；
- 5 个 mood_label 全部映射到存在的表情文件，未知值回退 calm；
- manifest 记录 `creation_route`、来源、批准状态和积分摘要；
- 资源哈希与 manifest 一致。

### 9.3 体验验收

- 角色移动时不是“贴图抖动”；
- 停下时能看到 stop 过渡；
- 学习状态一眼能识别；
- 玩家仍只能观察，不能控制角色；
- 手机端角色不糊、不穿出场景；
- 减少动态时不出现动作卡死。

## 10. 版权和来源

B 必须记录：

- 小云雀工具名称、模型名称、生成日期；
- 每个候选的 prompt、seed（若平台提供）和积分；
- 采用的源文件和最终文件；
- 是否做过局部重绘、裁切、调色、补帧；
- 角色为项目原创，不复制真人或已有 IP；
- 参考视频只用于抽象特征提炼，不作为运行时素材；
- 如平台输出带有不允许使用的水印或条款，则不得进入仓库。

最终 manifest 至少增加：

```json
{
  "creation_route": "xiaoyunque-assisted-pixel-authoring",
  "license": "project-original",
  "source_reference": "abstract blue-whale direction only",
  "approval": {
    "approved_by": "Agent A",
    "approved_at": "YYYY-MM-DD"
  },
  "credit_budget": {
    "allocated": 1500,
    "spent": 0,
    "reserved": 150
  }
}
```

## 11. 分支、提交和停止点

建议提交顺序：

```text
art: add character v2 style exploration and credit log
art: add approved Lin Cheng hero portrait
art: add Lin Cheng expression pack
art: add four-direction character model sheet
art: add runtime character animation sheets
feat: wire sit and talk character animations
test: validate character art v2 assets and evidence
docs: record character art v2 handoff
```

B 必须停在以下门：

- 00A：能力和授权冒烟完成，等待 A 判断能不能继续；
- 00B：身份和资源落点冻结，等待 A 检查映射；
- Gate A：3 个风格方向完成，等待 A 选方向；
- Gate B：主视觉、实际角色卡和 96×96 裁切完成，等待 A 批准；
- Gate C：7 个表情和 mood_label 映射完成，等待 A 检查身份与切换；
- Gate D：四方向设定和关键姿态完成，等待 A 检查可动画性；
- Gate E1：idle / walk / turn / stop 完成，等待 A 做游戏中截图验收；
- Gate E2：study / sit / talk 完成，等待 A 做游戏中截图验收；
- Gate F：测试、截图、哈希和交接完成，等待 A 合并和发布。

没有通过上一门，不得为了“用完积分”继续生成。

## 12. 最终交接格式

B 最终必须回复：

```text
任务 ID：ART-V2
分支：
基线提交：
提交哈希：
改动文件：
视觉方向：
采用的候选和 seed：
积分开始 / 已用 / 剩余：
主视觉和表情路径：
四方向动作路径：
实现摘要：
测试命令：
测试结果：
桌面/手机/接触表/浏览器证据：
已知风险：
需要 A 决策或执行的动作：
```

## 13. 给 B 的首条启动消息

```text
你是 AI World 项目的 Agent B。请先读取最新 origin/main 和
docs/agent-B-character-art-v2-taskbook.md。

本轮只做林澄的角色美术重制，不碰生产服务器、VNC、RDP、SSH、
生产 .env、API Key、数据库和真实用户数据，不修改 main。

请从最新 origin/main 创建 codex/character-art-v2，先完成 00A 和 00B：
1. 阅读任务书和现有 R2 资源；
2. 运行基线测试；
3. 建立 art-source/character-v2/ 和积分日志；
4. 用小云雀最多 50 积分做能力与授权冒烟；
5. 确认透明导出、参考一致性、1024 细节、干净导出和授权可用；
6. 写清 identity-lock.md 和 asset-map.json；
7. 提交并 push 分支，然后停止，等待 Agent A 检查。

00A 任一项不通过就停止，不要进入 Gate A。不要先生成完整表情包，
不要生成 100 多张动画帧，不要直接把 AI 生成的连续图当运行时精灵表。
1500 积分是硬预算，Gate B 前累计不得超过 470 积分。
```
