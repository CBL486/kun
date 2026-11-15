# ART-V2 PixelLab P2-2 四方向静态清理验收

状态：技术验收 `PASS`；用户视觉确认 `PENDING`；P3 动画未授权
审查人：Agent A
执行人：Agent B
日期：2026-11-15
分支：`codex/character-art-pixellab-p2`
提交：`89c491d`

## 1. 验收结论

P2-2 静态清理通过技术验收，可以进入用户视觉确认。

本轮没有修改正式运行时，没有开始动画，没有再次调用 PixelLab。P2-1R 的失败修补结果没有被采用，北向鲸尾继续按自然遮挡规则处理。

## 2. 独立复核

复跑 `scripts/character_pixellab_p2_cleanup.py` 到独立临时目录，输出哈希与提交结果完全一致：

```text
ACFFDB829384987DA361150F82CC036F66C0847B16C81C55705061A4AFD55DB8
```

实际图片检查结果：

```text
精灵表：256×96
单帧：64×96
方向：down, left, right, up
总色板：24（含透明）
不透明色：23
Alpha：0/255
半透明像素：0
P2-2 PixelLab generations：0
P2-2 PixelLab calls：0
```

四方向 bbox：

```text
down ：(7,27,57,88)
left ：(13,24,54,88)
right：(2,24,43,88)
up   ：(9,24,47,88)
```

脚底接触边全部为 `y=88`。最小透明边距为 right 帧左侧 `2 px`，没有裁切。

## 3. 地图证据

独立核对截图的实际尺寸与 SHA-256：

```text
map-desktop-4dir.png：1440×1000
125DFA9840B8291F579809A5FEC797C78E6AE020F76966409ED8CE66D1706620

map-mobile-4dir.png：390×844
03A8964F2695B2B0D29D93822CF6E24C9D0700A6D15C2D5EB45FE4A704950BF2
```

页面中的角色显示尺寸为 `48×72`，四方向切换的水平位移为 `0 px`。截图和页面证据显示：

- 草地、道路、浅色地砖上没有白底方块；
- 脚底贴合地面；
- down、left、right 的鲸尾可读；
- up 的后发、服装背面和蝴蝶结可读；
- 四方向在手机尺寸下仍能辨认；
- 页面明确标注为预览专用，不是玩家控制功能。

## 4. 视觉检查

通过：

- 蓝发、鳍耳、蓝白女仆/学院服、围裙、鲸尾和玫瑰唇色保持一致；
- 四个方向的轮廓与服装结构一致；
- left/right 不是镜像；
- 色板收敛后没有明显脏色、杂边或半透明边缘；
- 北向鲸尾自然遮挡，没有强行补画；
- 4×深色、浅色、棋盘格预览均可读。

保留意见：

- 最终审美仍需用户确认；
- 48×72 下角色细节会自然损失，这是运行时尺寸的预期表现；
- `character_pixellab_p2_map_capture.py` 依赖 Playwright，当前主虚拟环境没有该包；截图证据已经独立核验，因此不阻塞本轮验收，但后续如要一键复跑地图截图，需要补充环境依赖说明。

## 5. 回归测试

使用项目依赖路径运行完整测试：

```text
262 passed, 1 warning
```

警告为既有 Starlette/httpx 弃用提示，不影响结果。

`node --check web/app.js` 通过。

## 6. 验收边界

```text
P2-2 技术清理：PASS
用户视觉门 U1：PENDING
P3-0 idle：未授权
walk / turn / stop：未授权
生产接入：未授权
正式运行时修改：0
```

## 7. 下一步

用户应先查看以下预览：

```text
art-source/character-v2/pixellab/P2/sprite-preview-4x.png
art-source/character-v2/pixellab/P2/map-desktop-4dir.png
art-source/character-v2/pixellab/P2/map-mobile-4dir.png
```

如果用户确认当前角色风格可以继续，再单独下发 P3-0 idle 四方向四帧任务书。不得把本轮通过自动解释为动画或生产接入授权。
