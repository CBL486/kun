# R2 原创蓝鲸少女角色动画交接

状态：待 R2 审查

日期：2026-11-07

分支：`codex/product-r2-character-art`

基线：`4941b9d04b27b70c29e6d6cc016819d77f7c9cca`

## 1. 交付

- 原创蓝鲸少女 1024×1024 主视觉；
- 平静、开心、低落、专注 4 张 512×512 表情；
- 64×96 四方向地图角色；
- idle 4 帧、walk 6 帧、turn 4 帧、stop 3 帧；
- 右、左、上、下全部为独立精灵表；
- presence 驱动的新精灵播放器；
- walking → stop → idle 和 idle → turn 的过渡；
- 减少动态时固定 idle 首帧；
- 清除 `data-move`、`.map-controls` 和 `.map-move-hint` 死 CSS。

## 2. 创作与版权

当前环境没有可用内置图像生成工具，也未收到额外风格参考图片。因此使用
`native-pixel-authoring` 的 Pillow 像素脚本原创绘制，不冒充模型生成。

不使用抖音视频原帧、Cosplayer 面部或服装、品牌标志或具体版权角色。色板、轮廓、
资源尺寸和动画语义见 `docs/character-design-r2-v1.md`。

## 3. 资源清单

```text
assets/characters/whale-girl/whale-girl-manifest.json
assets/characters/whale-girl/lin-cheng-map.png
assets/characters/whale-girl/portraits/
assets/characters/whale-girl/sheets/
```

每个运行时文件记录字节数和 SHA-256。

## 4. 测试

```text
pytest：210 passed, 1 warning
R2 资源清单/尺寸/Alpha/哈希：通过
四方向 walk 帧差异：通过
旧 movement 控件和死 CSS：不存在
Edge 桌面 1440×1000：无横向溢出
Edge 手机 390×844：无横向溢出
idle/walk/turn/stop 状态切换：通过
控制台错误：[]
```

## 5. 浏览器证据

```text
docs/screenshots/r2-idle-desktop.png
docs/screenshots/r2-walk-desktop.png
docs/screenshots/r2-walk-mobile.png
```

复现：

```text
scripts/run_r2_evidence_api.py
scripts/capture-r2-evidence.js
```

## 6. 已知风险

- 当前运行时使用精灵表替代 Spine；
- sit/study/talk 尚无专用动作，暂时回退 idle；
- 角色美术是轻量几何像素风，不是高预算手绘；
- 浏览器证据通过隔离 fake Key 服务完成，不访问真实 DeepSeek。

## 7. 需要 A 做

1. 审查原创性与资源许可证；
2. 合并前确认 R2 与 R5 的独立分支无文件冲突；
3. 在真实测试环境验收四方向移动和减少动态效果。
