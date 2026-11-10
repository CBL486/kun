# ART-V2 R3-1 / R3-2 底模改造证明

状态：待 Agent A 审查

日期：2026-11-10

分支：`codex/character-art-v2-r3`

基线：`d1ea99d`，即最新 `origin/main`

## 1. 本轮范围

本轮只完成：

- R3-1：授权底模来源、静态四方向精灵；
- R3-2：真实地图桌面和手机证明。

没有制作 idle、walk、turn、stop、study、sit、talk 动画，也没有接入生产。

## 2. 授权底模

| 项目 | 值 |
| --- | --- |
| 素材包 | Modern Interiors |
| 归档 | `2104261.zip` |
| 归档 SHA-256 | `8FE691CE84881936F6B7A25E15A9847A1BFD555D21984A99939EA930A52C4C91` |
| 授权状态 | `project-authorized` |
| 身体成员 | `Modern_Interiors/2_Characters/Character_Generator/Bodies/48x48/Body_2_48x48.png` |
| 服装成员 | `Modern_Interiors/2_Characters/Character_Generator/Outfits/48x48/Outfit_17_Nurse_48x48.png` |
| 头发成员 | `Modern_Interiors/2_Characters/Character_Generator/Hairstyles/48x48/Hairstyle_4_48x48_1.png` |
| 眼睛成员 | `Modern_Interiors/2_Characters/Character_Generator/Eyes/48x48/Eyes_2_48x48.png` |

原始素材包不进入仓库。完整成员哈希、四方向裁切框、颜色映射和最终文件哈希见：

```text
art-source/character-v2/r3-proof/base-source.json
```

## 3. 制作方式

1. 在同一组四方向网格上组合授权成年身体、女装、长发和眼睛层；
2. 保留底模头部、身体、手脚和站立基线；
3. 将底模 15 色映射为林澄的 21 色运行时色板；
4. 在 64×96 网格上逐像素增加：
   - 深蓝长发；
   - 左右鲸鳍；
   - 冰白围裙；
   - 单侧鲸尾；
   - 蓝色大眼与脸部表情；
5. 裁切到安全边界并固定脚底基线。

没有使用 `ImageDraw.polygon`、椭圆、滤镜或 1024 概念图缩放来构造角色。

## 4. 运行时规格

```text
四方向表：256×96
单帧：64×96
运行时：48×72
颜色：21（含透明）
Alpha：0/255
半透明像素：0
脚底基线：88
direction order：down,left,right,up
```

档案：

```text
art-source/character-v2/r3-proof/
  base-source.json
  sprite-4dir.png
  sprite-down-1x.png
  sprite-preview-4x.png
  silhouette-4dir.png
  metrics.json
  source/{down,left,right,up}.png
  map-desktop-down.png
  map-mobile-down.png
```

## 5. 地图证据

```text
art-source/character-v2/r3-proof/map-desktop-down.png
art-source/character-v2/r3-proof/map-mobile-down.png
docs/character-art-v2/r3-proof-map-evidence.json
```

- 桌面：1440×1000；
- 手机：390×844；
- 玩家实际 rect：48×72；
- 页面：真实 `web/index.html`；
- 浏览器控制台错误：0；
- 使用隔离 fake key，不访问生产配置或真实 Key。

## 6. 测试

```powershell
$py = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = ((Resolve-Path .b6-deps).Path + [IO.Path]::PathSeparator + (Resolve-Path .).Path)
& $py -m pytest tests/test_character_r3_proof.py -q
```

结果：

```text
3 passed（R3 定向测试）
265 passed, 1 warning（完整 pytest）
```

测试覆盖底模记录、最终哈希、四方向尺寸、色数、Alpha、4× 最近邻预览、
左/右非镜像，以及桌面/手机真实地图截图。

## 7. 已知风险

1. 当前仅完成静态四方向证明，动作节奏尚未制作；
2. WorkBuddy 母图上的 AIGC 标识和原始元数据仍保留在参考文件中；
3. Modern Interiors 原始素材包未进入仓库，复建需要本地授权源目录；
4. 最终商业授权条款仍需项目所有者在发布前确认。

## 8. 停止点

等待 Agent A 审查 R3-1 和 R3-2。通过前不制作 idle/walk，也不继续其他动作。
