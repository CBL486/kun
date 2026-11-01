# B7.5 美术资源管线

状态：本地横版大世界切片，接入 Modern Exteriors 商业授权资源与 AppleDog 免费商用室内补充包

日期：2026-10-30

## 1. 创作路线

采用 `source-composite`：

- 建筑、地图、角色头像和 UI 图标均直接读取素材包成员；
- 管线只执行裁切、透明区域收缩、拼贴和最近邻整数缩放；
- 不再用 Pillow 程序化重画建筑或人物造型；
- 原始 ZIP/RAR/PSD/ASEPRITE 不进入仓库；
- 每个运行时资源在 `assets/manifest.json` 中记录压缩包、成员、裁切框和处理操作。

重建命令要求通过环境变量 `B75_SOURCE_ROOT` 指向本地私密素材解压目录；
公开仓库不包含原始素材。

## 2. 视觉规格

| 项目 | 规格 |
| --- | --- |
| 参考方向 | 《去月球》式单场景、黑场留白、顶部轻 HUD 与底部对白框 |
| 投影 | 斜俯视 3/4 |
| 逻辑网格 | 32 px |
| 横向大世界 | 2400×900，镜头只显示局部 |
| 地图视口 | 桌面和手机统一为 16:9 |
| 建筑 | 保留素材原始比例，透明背景 PNG/WebP |
| 头像 | 96×96，角色像素帧最近邻 2 倍 |
| 图标 | 32×32 |
| 运行时采样 | `image-rendering: pixelated` |

## 3. 原素材映射

| 游戏对象 | 主要来源 |
| --- | --- |
| 草地、道路、人行道、树木、花坛与街具 | Modern Exteriors 48×48 图块 |
| 宿舍 | Modern Exteriors `Modern_House_48x48.png` |
| 教学楼 | Modern Exteriors `School_1.png` |
| 青禾书院 | Modern Exteriors `Japanese_House_48x48.png` |
| 食堂 | Modern Exteriors `Market_Medium_1.png` |
| 便利店 | Modern Exteriors `Market_Small_1.png` |
| 河边步道 | Modern Exteriors 的深水、步道、树木、长椅、路灯与栈桥 |
| 六地点内部 | Modern Interiors 的 Room Builder 地板与墙面、卧室、教室、图书馆、会议室、厨房、商店及角色图块；宿舍与书院补充 AppleDog 家具 |
| 林澄、陈岚、苏晚、高原、顾言 | Modern Interiors 角色帧 |
| 地图行走主人公 | Modern Interiors 林澄角色帧 |
| 导航与状态图标 | Modern Interiors UI、Sunnyside World UI |
| 角色骨骼动画 | Spine 4.3 数据格式 + `@esotericsoftware/spine-webgl` 4.3.13 |
| 建筑与街区补充 | `Modern Exteriors`（LimeZu，$2.50，已购买并接入） |

### 角色场景映射

| 角色 | 静态帧裁切 | 稳定出场场景 | 动画 |
| --- | --- | --- | --- |
| 林澄 | `(48, 0, 48, 96)` | 宿舍、教学楼 | Spine `idle` / `walk` |
| 陈岚 | `(192, 0, 48, 96)` | 青禾书院 | 静态 |
| 苏晚 | `(336, 0, 48, 96)` | 教学楼 | 静态 |
| 高原 | `(48, 96, 48, 96)` | 食堂 | 静态 |
| 顾言 | `(336, 192, 48, 96)` | 河边步道 | 静态 |

同一映射写入 `assets/manifest.json` 的 `character_scene_map`，并由资产测试校验
头像、裁切框、场景和动画状态一致。

## 4. 地图构图

横向外部地图：

- 大世界从 1440×720 扩展到 2400×900，桌面与手机只显示当前街区；
- 宿舍、教学楼和青禾书院位于主路北侧，沿横向依次展开；
- 食堂、河边步道和便利店位于主路南侧；
- 建筑底部与道路保留间距，教学楼不再压在公路上；
- 河边步道独占南部地块，图片不与其他建筑或标签穿模；
- 河面、南岸步道、树阵与栈桥直接绘入世界底层，不使用矩形贴图覆盖地图；
- 街区加入树阵、灌木、花坛、路灯、长椅、消防栓、邮筒和垃圾桶；
- 主人公从当前地点附近出发，可用方向键、WASD 或屏幕方向键移动；
- 镜头跟随主人公平移，任何尺寸下都不一次展示完整大世界。

地点内部：

- 点击地图建筑或地点卡，会打开对应的内部场景手账；
- 宿舍包含床铺、储物柜、桌椅和角色；
- 宿舍增加电脑书桌、圆形地毯、书架和墙面装饰，床铺使用独立可辨识的完整床体；
- 宿舍与书院使用 AppleDog 补充包加入床铺、沙发、书柜与生活道具，增加生活痕迹与画面密度；
- 教学楼包含成排课桌、讲台和电脑桌；
- 青禾书院包含连续书架、阅读桌椅和角色；
- 食堂包含备餐柜台、灶具、冰箱、餐桌和角色；
- 便利店包含货架、冷柜和收银台；
- 书院与食堂的桌椅使用同源的完整会议桌模块，根据前后朝向拼成四椅一桌；
- 所有室内统一采用剖切式墙面、地板和接触阴影，避免家具悬浮或裁切错位。
- 墙面窗、地毯、沙发、货架和边角绿植均使用覆盖完整透明边界的图块裁切框，
  并记录最终落点与收缩后尺寸；资产测试会拒绝越出 960×540 画布的家具。

手机地图与桌面共用同一横向世界和 16:9 视口，只显示镜头附近区域。

## 5. Spine 角色动画

- 本机安装并使用了 `Spine Trial 4.3.26`；
- 林澄被拆分为躯干、左右腿与阴影纹理；
- Spine 骨架包含 `root`、`torso`、`head`、`leg_left`、`leg_right` 五个骨骼；
- 制作了 `idle` 与 `walk` 两段循环动画；
- 横向移动时角色转身，移动状态切换 `walk`，停止后切换 `idle`；
- 页面使用本地 `@esotericsoftware/spine-webgl` 4.3.13，不依赖 CDN；
- Spine Runtime 的许可证文本随资源保存在
  `web/vendor/SPINE-RUNTIMES-LICENSE.txt`。

Spine Trial 明确禁止保存项目和导出动画数据，因此当前运行时数据采用与
Spine 4.3 格式兼容的骨架 JSON 生成，并使用官方 WebGL Runtime 渲染。取得正式
Spine Editor 许可证后，可将 `spine/lin_cheng/source/lin_cheng.json` 导入编辑器，
保存为 `.spine` 项目并重新导出，不需要修改网页接入代码。

## 6. 重建与验收

测试默认只验证已提交资源，不依赖私密源素材：

```powershell
pwsh -NoProfile -File scripts/test-b75.ps1
```

需要重建时，在拥有私密素材的环境设置源目录：

```powershell
$env:B75_SOURCE_ROOT = "D:\private\b75-source-extracted"
pwsh -NoProfile -File scripts/build-b75-assets.ps1
pwsh -NoProfile -File scripts/test-b75.ps1 -Rebuild
```

验收会检查：

- 六栋建筑在世界坐标内不越界、不重叠，也不压住主路；
- 主人公移动后镜头位置发生变化；
- 页面无横向溢出；
- 图片失败时保留地点名称和状态；
- 六地点内部图均可打开、正常加载并有独立来源记录；
- 资源来源、成员路径、裁切框、哈希和原始像素标记完整。
- `assets/`、Web 入口、`/static` 与 `/assets` 均由同一个应用实例提供；
- Manifest 中的 Spine JSON/Atlas 哈希在干净检出后仍与文件字节一致。
