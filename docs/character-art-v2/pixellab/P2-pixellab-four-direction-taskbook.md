# ART-V2 PixelLab P2 四方向静态验证任务书 V1

状态：待执行
编写人：Agent A
日期：2026-11-14
执行人：Agent B
审查人：Agent A
目标分支：`codex/character-art-pixellab-p2`
基线：最新 `origin/main`，当前编写基线为 `1974fe1` 之后的最新提交
生产边界：B 不接触生产服务器、VNC、RDP、SSH、生产 `.env`、API Key、数据库或真实用户数据；不修改 `main`，不部署。

## 1. 前置条件

P1 静态技术验证已通过：

```text
64×96 真实尺寸
21 色
Alpha 0/255
48×72 地图显示
桌面/手机截图通过
```

P1 文件：

```text
art-source/character-v2/pixellab/P1/cleaned-64x96.png
art-source/character-v2/pixellab/P1/sprite-preview-4x.png
art-source/character-v2/pixellab/P1/map-desktop-down.png
art-source/character-v2/pixellab/P1/map-mobile-down.png
```

本轮不能重做角色，只能在 P1 结果上做局部唇色修正，再验证四方向。

## 2. P2-0：嘴唇颜色修正

### 2.1 用户要求

当前角色嘴唇偏蓝/灰，不符合正常人物嘴唇颜色。

改为自然的低饱和玫瑰唇色：

```text
唇色主色： #B85F6C
嘴唇阴影： #8D4654
可选唇部高光： #D98A94
```

要求：

- 只修改嘴部像素；
- 不使用蓝色、青色、紫色或灰色作为嘴唇；
- 不改变眼睛、头发、鳍耳、服装和鲸尾；
- 不整体改色；
- 不重画脸部；
- 保持像素风格；
- 最终色板仍不超过 24 色。

### 2.2 执行方法

B 可以做确定性的局部像素颜色替换：

1. 从 `cleaned-64x96.png` 复制；
2. 用嘴部区域遮罩找出嘴部像素；
3. 将原先蓝灰色嘴部像素替换为唇色主色；
4. 必要时给下唇加 1 px 阴影；
5. 对照 8× 近邻放大图检查；
6. 保存修正版。

不允许用新的 AI 生成结果来掩盖唇色问题。

### 2.3 交付

```text
art-source/character-v2/pixellab/P2/
  lip-fixed-64x96.png
  lip-fixed-preview-8x.png
  lip-metrics.json
```

`lip-metrics.json` 至少记录：

```json
{
  "source": "art-source/character-v2/pixellab/P1/cleaned-64x96.png",
  "size": [64, 96],
  "lip_colors": ["#B85F6C", "#8D4654"],
  "colors": 21,
  "alpha_values": [0, 255],
  "changed_region": "mouth-only"
}
```

### 2.4 唇色验收

- 8× 放大后嘴唇是自然玫瑰色；
- 嘴部没有蓝色/灰色残留；
- 眼睛和头发没有被误改；
- 服装和鲸尾没有变化；
- 21～24 色范围内；
- A 批准后才能进入 P2-1。

## 3. P2-1：四方向静态验证

使用修正后 `lip-fixed-64x96.png` 作为南向参考。

PixelLab 当前可用：

```text
PixelLab V3 Standard
模式：4 方向
页面显示费用：8 generations
Pro required: no
```

生成：

- down；
- left；
- right；
- up。

要求：

- 同一角色身份；
- 鳍耳、蓝白服装、围裙、鲸尾和腰扣一致；
- 左右方向不能只是镜像；
- 背面能看到后发、服装背面和鲸尾；
- 唇色在可见的脸部方向使用同一自然唇色；
- 如果平台生成结果整体漂移，停止，不得自己补画。

## 4. 技术清理

四方向生成后：

```text
PixelLab 四方向导出
-> 64×96 逻辑帧
-> 透明背景
-> Alpha 0/255
-> 21～24 色
-> 脚底基线 y=88
-> 256×96 精灵表
```

禁止：

- 把 64×64 拉伸；
- 重新设计角色；
- 用程序化几何图形补角色；
- 用新的、不同形象的生成结果顶替；
- 删除 AIGC 标识。

## 5. P2 交付路径

```text
art-source/character-v2/pixellab/P2/
  lip-fixed-64x96.png
  lip-fixed-preview-8x.png
  lip-metrics.json
  source-down.png
  sprite-4dir-raw.png
  sprite-4dir-cleaned.png
  sprite-preview-4x.png
  metrics.json
  map-desktop-down.png
  map-mobile-down.png
  credit-log.json

docs/character-art-v2/pixellab/P2-report.md
```

## 6. P2 验收条件

### 唇色

- 嘴唇为自然玫瑰色；
- 不是蓝色、青色、紫色或灰色；
- 仅嘴部发生变化；
- 8× 预览可确认。

### 四方向

- 四方向都是同一角色；
- down/left/right/up 均有内容；
- 左右有真实结构差异；
- 鳍耳、围裙、鲸尾和腰扣可读；
- 四方向在 64×96 内不触边；
- Alpha 0/255；
- 21～24 色；
- 脚底基线 88。

### 游戏尺寸

- 真实地图预览桌面 1440×1000；
- 手机 390×844；
- 角色显示 48×72；
- 控制台错误 0；
- 不是把概念图贴在大图下面。

## 7. 预算与账号

- 本轮四方向显示消耗：8 generations；
- 不购买 Pro；
- 不订阅；
- 不自动付款；
- 记录实际消耗和可用余额；
- 如果免费额度不足，停止报告。

## 8. 停止门

```text
P2-0 唇色：不通过，不进入 P2-1
P2-1 四方向：不通过，不进入动画
动画：未通过 P2 不开始
生产接入：未通过 P2 不开始
```

## 9. 给 B 的启动消息

```text
你是 AI World 项目的 Agent B。P1 已通过，本轮只做 PixelLab P2 四方向静态验证。

从最新 origin/main 创建 codex/character-art-pixellab-p2。

第一步先改唇色：
- 来源：art-source/character-v2/pixellab/P1/cleaned-64x96.png
- 只改嘴部像素；
- 唇色主色 #B85F6C，阴影 #8D4654，可选高光 #D98A94；
- 不使用蓝色、青色、紫色、灰色嘴唇；
- 不改变眼睛、头发、鳍耳、服装或鲸尾；
- 交 lip-fixed-64x96.png、8× 预览和 lip-metrics.json；
- 这一步完成后先停下，等 A 确认，再进入四方向。

四方向阶段使用 PixelLab V3 Standard 的 4 方向入口；
页面显示 8 generations，不购买 Pro、不订阅。
四方向结果必须保持同一角色，统一到 64×96、21～24 色、Alpha 0/255，
并交真实桌面/手机 48×72 地图截图。

不要把 64×64 拉伸，不要自己补画角色，不要直接接生产。
```
