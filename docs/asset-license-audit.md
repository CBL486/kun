# B7.5 素材授权审计

状态：项目方已授权；仅提交派生运行资源

日期：2026-10-29

## 1. 授权结论

项目所有者明确确认：

- 提供的像素素材可以直接使用；
- 也可以裁切、组合和改造后用于本项目；
- 原始素材由项目所有者私有保存；
- 仓库只提交面向当前页面裁切、压缩后的 PNG/WebP 导出。

## 2. 来源包

| 来源 ID | 来源 | 作用 | 文件 SHA-256 |
| --- | --- | --- | --- |
| `appledog_interiors` | AppleDog Modern Interior Tileset | 卧室、客厅、书架、窗帘和生活道具补充 | `630F38A16CF8D2368612CB92AE7292F234B98EB94A57E5D351B71C937473081F` |
| `modern_exteriors` | LimeZu Modern Exteriors | 现代建筑外观、道路、铺装、围栏、植被和街具 | `D12C6892ED96BC18CDA34EAFDF3EF15B1EDA10D0D6733F377730F46932F728FE` |
| `clean_city_v3` | GuttyKreum Clean City v3 | 现代建筑、道路和店铺 | `467DBFB0887B4EE605D4F4C3038B8642271C1C5CA967A8ABC4EC2247525A0DE5` |
| `sunnyside_world` | Sunnyside World | 像素 UI 状态图标 | `B9084F961E8E78CDB8789ED72ED7383B6A9B3EBE8130F4B792A88A65C5D40CF5` |
| `modern_interiors` | Modern Interiors | 角色帧与 UI 图标 | `8FE691CE84881936F6B7A25E15A9847A1BFD555D21984A99939EA930A52C4C91` |
| `village_pixel_pack` | 村庄田园像素游戏 | 早期原型备选；当前正式世界构图不再依赖该包 | `E2D8D538183A9674C479C7620DE17B8F3547F2236E08604557A6E98F0A1D5F3A` |

## 3. 溯源控制

- `assets/` 不含 ZIP、RAR、PSD 或 ASEPRITE；
- 每个资源至少记录一个 `source_layers` 条目；
- 每个条目包含 `source_archive`、`source_member`、`crop_box` 和
  `modification_operation`；
- 每个资源标记 `original_pixel_used: true`；
- Modern Exteriors 派生资源标记为 `commercial-licensed`，并保留 LimeZu 署名；
- 六地点内部图记录地板、墙纸和每件家具图块的原始成员与裁切框；
- Spine Runtime 使用 `@esotericsoftware/spine-webgl` 4.3.13，随仓库保留其许可证；
- 导出文件记录字节数和 SHA-256；
- `tests/test_b75_assets.py` 会拒绝缺少原始像素来源的资源。

## 4. 发布前仍需补齐

以下材料不在素材包内，属于 G2 前由项目所有者或 A 补齐的合规证据：

- 每个素材包的购买或授权凭证；
- 作者要求的正式署名格式；
- 商业使用与再分发范围；
- 可公开发布的派生资源范围确认。

这些材料不阻塞本地竖切片，但上线前必须补齐。

Modern Exteriors 为本轮由项目所有者购买的商业素材。公开使用时应保留
`Modern Exteriors by LimeZu` 署名，不单独转售或再分发原始素材包。

AppleDog 的 Modern Interior Tileset 由公开页面提供为免费商用素材，允许在
商业和非商业项目中修改使用；发布时保留 `Modern Interior Tileset by AppleDog`
署名，不转售或再分发原始素材包。

Spine Trial 可以用于本地预览，但不能保存项目或导出动画资源。正式发布前必须
使用项目所有者持有的 Spine Editor 正式许可证重新保存和导出角色工程。
