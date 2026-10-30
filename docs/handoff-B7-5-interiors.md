# B7.5 室内资产修复与角色模型现状交接

状态：本轮工作已完成并通过自动化与视觉验收，纳入最终美术提交

日期：2026-10-30

分支：`codex/bx-b7-5-art`

基线提交：`bd56080`

## 1. 本轮完成内容

### 室内场景

五个真正的室内场景均已重建并复查：

- 宿舍：补齐两扇墙面窗户；粉色和棕色圆盘使用完整图块；粉色圆盘右移至
  `(330, 378)`，不再遮挡紫色沙发；角色、床位和右侧家具没有新增重叠。
- 教学楼：补齐粉色与棕色圆盘，移除残缺边角装饰，替换为完整盆栽。
- 青禾书院：补齐粉色与棕色圆盘，移除压在沙发上的残缺边缘物件，保留完整盆栽。
- 食堂：移除画布角落的残片，换成完整盆栽；桌椅和角色位置不变。
- 便利店：不再使用区域拼图中间截段，改为完整独立冰箱、货架、商品展台、
  收银台、货架组和盆栽重新编排；所有家具都落在 960×540 画布内。

河边步道属于室外场景，本轮没有改动。

### 资产记录与回归检查

- `assets/manifest.json` 已重新生成，记录每个室内图块的来源、裁切框、
  最终落点、透明收缩后尺寸和运行导出哈希。
- 新增室内家具完整性测试，检查：
  - 宿舍窗户使用完整裁切框；
  - 前三间场景使用完整双圆盘；
  - 粉色圆盘起点不早于沙发右缘；
  - 已废弃的残缺植物裁切不会重新出现；
  - 所有室内家具的最终落点都在画布范围内。

## 2. 关键文件

```text
assets/interiors/
  dorm.png / dorm.webp
  classroom.png / classroom.webp
  library.png / library.webp
  canteen.png / canteen.webp
  shop.png / shop.webp
  river.png / river.webp
assets/manifest.json
scripts/build_b75_assets.py
tests/test_b75_assets.py
docs/art-pipeline.md
docs/art-budget-b7-5.json
docs/screenshots/
  b75-interiors-overview.png
  b75-interior-desktop.png
  b75-interior-mobile.png
```

构建入口会重建主资产和 Spine 资源：

```powershell
pwsh -NoProfile -File scripts/build-b75-assets.ps1
```

完整测试与视觉验收：

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

## 3. 验证结果

- `pytest`：112 项通过，存在 1 条 Starlette/httpx 弃用警告，不影响本轮功能。
- Node 语法检查：`web/app.js`、`web/spine-player.js` 通过。
- 桌面视觉检查：通过，`scrollWidth=1440`，控制台无错误。
- 手机视觉检查：通过，`scrollWidth=390`，控制台无错误。
- 室内图加载、角色移动、Spine `idle`/`walk` 切换和河边移动均通过。
- 验收记录：`docs/art-budget-b7-5.json`。
- 室内总览：`docs/screenshots/b75-interiors-overview.png`。

## 4. 角色模型现状

当前项目没有 3D 角色资产，不存在 `.glb`、`.gltf`、`.fbx`、`.obj`、
`.blend` 或 `.vrm` 模型文件。角色呈现采用 2D 像素和 Spine 骨骼动画。

### 已有可动画模型

只有林澄：

- Spine 3.8/4.3 JSON 兼容数据：`assets/spine/lin_cheng.json`；
- 图集：`assets/spine/lin_cheng.png`；
- Atlas：`assets/spine/lin_cheng.atlas`；
- 5 根骨骼：`root`、`torso`、`head`、`leg_left`、`leg_right`；
- 4 个贴图区域：身体、左右腿、阴影；
- 动作：`idle`、`walk`；
- 地图静态帧：`assets/characters/lin_cheng.png`；
- 运行时尺寸约 48×70。

### 只有静态资源的角色

陈岚、苏晚、高原、顾言共有：

- 96×96 PNG/WebP 头像；
- Modern Interiors 的 48×96 静态角色帧；
- 日程、状态、知识边界和反应模板；
- 没有独立 Spine 骨骼、独立行走贴图或个人动画。

原始 `New_Characters 48x48.png` 角色表为 576×768，包含 16 套角色模板，
每套可提供 4 方向、每方向 3 帧。该表可以继续制作 2D 骨骼或逐帧行走角色，
但目前只有五名具名角色被映射到项目内容。

## 5. 已知问题与风险

- 室内静态角色帧与角色身份尚未完成全量一一核对。当前食堂场景使用的是
  “苏晚”对应角色帧，而食堂设定角色是高原；顾言也尚无稳定的室内出场位置。
- 四名 NPC 没有独立行走模型，不能直接当作可移动的 2D Spine 角色复用。
- 没有 3D 模型、3D 骨骼、绑定、材质或动画，若转 3D 需要另立资产与渲染范围。
- Spine 数据由项目内兼容 JSON 生成；当前 Spine Trial 不允许正式保存项目和导出动画。
- 当前工作树包含大量未提交变更，本轮资产与截图均在未提交状态。

## 6. 建议的后续顺序

1. 先确定角色美术路线：继续 2D Spine，还是另立 3D 角色管线。
2. 若继续 2D，优先为陈岚、苏晚、高原、顾言制作 `idle` 与 `walk` 骨架，
   并建立统一的 `assets/spine/<character_id>/` 结构。
3. 核对每个室内静态角色帧与人物设定，修正食堂等场景的身份映射。
4. 将角色模型、场景静态帧和头像建立同一份角色资产清单，避免“有头像但无模型”
   被误认为已具备可操作角色。
5. 若需要 3D，先独立评估建模数量、绑定和动画人力，不从当前 2D 资产直接推定。

## 7. 交接字段

```text
任务 ID：B7.5 室内资产修复与角色模型盘点
分支：codex/bx-b7-5-art
基线提交：bd56080
当前提交：本次最终美术提交（使用 `git log -1` 查看）
主要改动：assets/、scripts/build_b75_assets.py、tests/test_b75_assets.py、
          docs/art-pipeline.md、docs/art-budget-b7-5.json、docs/screenshots/
测试命令：pwsh -NoProfile -File scripts/test-b75.ps1
测试结果：112 项通过；桌面/手机视觉检查通过
素材许可：Modern Interiors、Modern Exteriors、AppleDog Modern Interior Tileset
原始素材：压缩包和解包源不提交，只提交裁切、拼贴和运行时资源
未完成项：NPC 独立骨骼模型、角色身份映射核对、3D 模型路线
```
