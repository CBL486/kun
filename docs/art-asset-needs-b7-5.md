# B7.5 美术素材补充与接入记录

日期：2026-10-29

## 现有素材可以继续完成的部分

- 现代建筑外观、道路、车辆：Clean City v3；
- 教室、图书馆、宿舍、厨房、商店内部：Modern Interiors；
- 树木、花草、河岸与河面：Modern Exteriors；
- UI 图标、角色帧：Sunnyside World、Modern Interiors；
- 林澄地图角色：Spine 4.3 骨架，包含待机和行走。

本轮已经优先从这些现有素材继续拆分和加密布置，没有引入风格冲突的新素材。

## 已购买并接入的素材

### Modern Exteriors - RPG Tileset

- 作者：LimeZu
- 页面：<https://limezu.itch.io/modernexteriors>
- 当前最低价格：**USD $2.50**
- 文件大小：约 222 MB + RPG Maker MV 版本 6.5 MB
- 规格：16×16、32×32、48×48，包含街道、建筑、店铺、道路细节、车辆与动画
- 授权：可用于商业和非商业游戏，可修改；不可转售/再分发素材包；需要署名 LimeZu
- 适合本项目的部分：它与现有 Modern Interiors 来自同一作者，比例、色彩和家具语言一致，可以直接补齐当前外部街区。

状态：项目所有者已于 2026-10-29 购买并完成接入。

- 解包后的主要来源：`modernexteriors-win.zip`
- RPG Maker MV 兼容包：`Modern_Exteriors_RPG_Maker_MV_v42.3.zip`
- 主包 SHA-256：`D12C6892ED96BC18CDA34EAFDF3EF15B1EDA10D0D6733F377730F46932F728FE`
- MV 包 SHA-256：`3D7436C527037E0AFAB343ED300D3B7666A3C2E160A813E2BC857AB36B746311`
- 已用于：横向街道、草地、人行道、沥青路、宿舍、教学楼、青禾书院、食堂、便利店、长椅、路灯、树、灌木、花坛、消防栓、邮筒和垃圾桶
- 归档规则：原始 ZIP 不入库，只提交项目内裁切与拼贴后的运行资源

本项目当前不需要再购买建筑外观素材。Modern User Interface 仍属于可选补充，
不是 B7.5 的阻塞项。

室内补充采用 AppleDog 的 Modern Interior Tileset：

- 页面：<https://apple-dog.itch.io/modern-tileset-by-appledog>
- 价格：免费
- 规格：16×16、32×32、48×48
- 授权：允许商用与非商用，需要署名 AppleDog，不可转售原始素材
- 已用于：宿舍与青禾书院的沙发、茶几、落地灯、书架和空间层次

### 可选升级：Modern Home Interiors

- 作者：bubbabba
- 页面：<https://bubbabba.itch.io/modern-home-interiors>
- 当前促销价：**USD $4.95**（原价 USD $15）
- 内容：600 件家具、68 件动画道具、93 个地板与墙面图块，包含窗户、门、
  墙面装饰、植物、宠物和大量生活杂物
- 授权：允许商业使用和修改，不要求署名，不可转售原始素材
- 结论：当前 B7.5 没有购买也能验收；如果希望把室内继续提升到样板房级别的
  密度，这一包最值得补。

### 更低预算候选

| 素材包 | 当前价格 | 规格与用途 | 注意 |
| --- | --- | --- | --- |
| [Modern Interior Tileset by AppleDog](https://apple-dog.itch.io/modern-tileset-by-appledog) | 免费 | 16/32/48 px，卧室、客厅、厨房、卫浴和家具 | 已接入；发布时署名 AppleDog |
| [Modern Apartment Interior Pixel Pack](https://godboyhappy.itch.io/modern-apartment-interior-pixel-pack) | USD $1.99 | 289 个 32×32 素材、96 个辅助图块、24 个图标和动画帧 | 页面标记为 AI Assisted，适合补充小物件 |
| [32px Modern Interiors Tile Set](https://evalynn.itch.io/32x32-modern-interiors-tile-set) | USD $2.50 | 286 张无缝地板、墙面和室内表面 | 偏表面材质，不能替代完整家具包 |
| [Modern Interior Pixel Art Tileset](https://comshadow.itch.io/modern-interior-pixel-art-tileset) | USD $3.99 | 客厅、卧室、厨房、卫浴、阳台、门窗与装饰 | 页面标记为 AI Assisted，需按最终画风筛选 |
| [house interior asset pack !](https://styloo.itch.io/houseinteriorassetpack) | USD $0.74 | 低价小型家具补充 | 体量最小，不建议作为唯一主素材包 |

### Modern User Interface - RPG asset pack

- 作者：LimeZu
- 页面：<https://limezu.itch.io/>
- 页面标价：**USD $3.90**
- 用途：对话框、状态面板、按钮、菜单和提示框
- 是否必须：不必须；当前界面可以继续用 CSS 实现类似《去月球》的低干扰布局。

## 免费备选

### Roguelike Modern City Pack

- 作者：Kenney
- 页面：<https://opengameart.org/content/roguelike-modern-city-pack>
- 授权：CC0，可商用，不要求署名
- 已下载并检查。道路、车辆和建筑模块数量充足，但像素颗粒偏大、建筑偏方块，与当前 Clean City 和 Modern Interiors 混用会明显串风格，暂不采用。

### Roguelike Indoor Pack

- 作者：Kenney
- 页面：<https://opengameart.org/content/roguelike-indoor-pack>
- 授权：CC0，可商用，不要求署名
- 已下载并检查。家具数量足够，但室内风格比现有 Modern Interiors 更简化，采用后会降低现有内部精度，暂不采用。

### Modern World Borderless Tileset MegaPack

- 作者：Alec, The Wizard
- 页面：<https://alec-the-wizard.itch.io/modern-world-borderless-tileset-mega-pack>
- 授权：CC0
- 备注：仍在开发中，现代室外部分尚不完整，更适合作未来补充候选。

## 暂不采用

- CreativaStudio Retro Urban：页面标注包含 CC BY-NC，同时又写了允许商业项目，授权表述存在冲突，发布前不宜依赖。
- riekahq Modern Exteriors Lite：公开说明为 AI 辅助绘制，暂不与当前人工像素素材混用。

## 当前结论

B7.5 当前没有阻塞性缺图：

- 六栋外观与连续横向街区已由 Modern Exteriors 覆盖；
- 六处内部由 Modern Interiors 的 Room Builder 地板、墙面、家具与角色资源覆盖；
- 河边步道直接拼在世界底层，使用 Modern Exteriors 的水面、河岸、长椅、路灯与栈桥；
- 林澄已有 Spine `idle` / `walk` 动画；
- UI 继续使用现有 CSS 与图标即可维持低干扰界面。

后续若要进一步加强电影感，可再考虑正式版 Spine 导出、更多角色表情差分和
环境动画；这些属于发布质量提升项，不影响本轮验收。
