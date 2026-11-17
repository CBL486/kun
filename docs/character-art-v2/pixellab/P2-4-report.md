# ART-V2 PixelLab P2-4 四方向静态角色报告

状态：`TECHNICAL PASS — PENDING USER CONFIRMATION`

日期：2026-11-17

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2-4`

起点：`bf2a640`

任务书提交：`1f3fab9`

## 1. 唯一 down 母版

```text
art-source/character-v2/pixellab/P2-3R6/down-two-hands-cleaned.png
64×96 RGBA
SHA-256: 54F1C7BD7D301577006A093A5EAE9AAA49B786996E36634C3B4B0FA47869E1E9
```

为满足 PixelLab 四方向接口的 `96×96` 参考尺寸，创建透明居中的
`input-down-approved-96x96.png`，仅用于生成参考。最终 down 直接取原
`64×96` 批准帧，未使用生成的 south。

## 2. PixelLab 四方向

```text
端点：POST /v2/create-character-with-4-directions
模型：Standard
相机视图：high top-down
参考方向：south
seed：20261119
有效生成请求：1
实际计费：1 generation
任务 ID：fb23530c-8170-4f80-a070-e8387939daca
角色 ID：7b4646da-32b0-4ac6-8e40-f66082036224
生成 ID：5226c0da-1e04-49c4-81e1-57fd2474223c
生成前余额：1966.9
生成后余额：1965.9
```

没有第二次生成，没有使用 Edit Image，没有手工补画角色。

## 3. 技术清理

```text
统一公共裁切窗口：(16,0,80,96)
输出 sheet：256×96
单帧：64×96
方向顺序：down / left / right / up
垂直脚底校正：down 0，left -2，right -5，up -2
色板：22
Alpha：0/255
半透明像素：0
```

left/right/up 仅进行统一裁切、脚底对齐和现有色板最近色映射。没有按方向
单独居中，没有拉伸、旋转或镜像。

down 与批准母版逐像素一致。

## 4. 方向检查

```text
down bbox：(7,27,57,88)
left bbox：(19,21,58,88)
right bbox：(18,22,62,88)
up bbox：(13,22,57,88)

四方向鞋底接触边界：y=88
left/right 轮廓差异比：0.30254184748915064
```

通过：

- left/right 为真实侧面，不是镜像；
- 左右两侧均可辨认近侧腿和靴子；
- 侧面鲸尾方向正确；
- up 不显示正脸，有后发、背面服装、双腿与双靴；
- 两只手保持小尺寸并与袖口连接；
- 四方向脚底基线一致；
- down 的柔唇、双手和旧裙清理保持。

## 5. 输出

```text
art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png
SHA-256: 6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12

raw sheet SHA-256:
906A0157ADF76F17F6D70BE3DD5C055F9E4AD90EC77DD25FAF5EE43136926CEB
```

预览：

```text
art-source/character-v2/pixellab/P2-4/sprite-preview-4x.png
art-source/character-v2/pixellab/P2-4/sprite-preview-checker-4x.png
```

## 6. 地图验证

真实青禾镇预览，不改正式页面：

```text
桌面：1440×1000
手机：390×844
运行时角色矩形：48×72
方向切换横向偏移：0 px
Console errors：0
```

四方向在桌面和手机预览中均可见。方向按钮只用于观察者预览，不描述为玩家控制。

```text
art-source/character-v2/pixellab/P2-4/map-desktop-4dir.png
art-source/character-v2/pixellab/P2-4/map-mobile-4dir.png
art-source/character-v2/pixellab/P2-4/map-capture.json
```

## 7. 可复现性

连续运行四方向清理脚本两次，输出哈希一致：

```text
6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12
```

## 8. 边界

```text
AI 生成有效请求：1
generations_used：1
Edit Image：0
手工补画：0
动画：未开始
正式运行时：未修改
生产数据：未接触
购买/升级：0
```

## 9. 回归

```text
.\scripts\test-b7.ps1
262 passed, 1 warning

node --check web/app.js
通过
```

警告为既有 Starlette/httpx 弃用提示。

## 10. 状态

```text
P2-4 技术检查：PASS
P2-4 用户视觉确认：PENDING
P3-0 idle：继续锁定
```
