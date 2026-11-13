# ART-V2 PixelLab P1 技术验证报告

状态：`PASS FOR STATIC TECHNICAL VALIDATION`

日期：2026-11-13

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p1`

基线：`a085e20d4baf644f6ee50091a4318b0a7e375fe8`

生产边界：未购买、未订阅、未部署、未修改生产环境，未制作动画。

## 1. 输入参考

从唯一视觉母版制作了 `256×384` 的 `2:3` 输入：

```text
art-source/character-v2/pixellab/P1/input-2x3.png
SHA-256: CAB7D7722DB49A1F19AF7DB20B58006CC233C555E206EB7D0943A20EDF3A035E
```

处理方式：

- 母版保持原样；
- 角色按比例缩放；
- 角色居中；
- 使用统一纯色背景补足画布；
- 没有重画、改脸、改服装或改角色比例。

## 2. PixelLab 生成

工具路径：

```text
PixelLab → 创造者 → 图像到像素艺术 → 标准
```

参数：

```text
输出比例：2:3
输出尺寸：64×96
Output Scale：4
参考 Init Strength：0
页面显示消耗：1 generation
Pro：未使用
```

原始生成文件：

```text
art-source/character-v2/pixellab/P1/generated-64x96.png
尺寸：64×96
SHA-256: 3B854CAC5C9291CBC3DA880176C3F562F9A4B953B3A517C80DA26FD902A604F2
```

该文件是新生成的 2:3 结果，不是将 P0 的 `64×64` 拉伸得到。

## 3. 确定性清理

清理脚本：

```text
scripts/character_pixellab_p1_clean.py
```

处理内容：

- 从边缘 flood-fill 移除连接背景；
- Alpha 二值化为 `0/255`；
- 将脚底最低不透明像素校准到 `baseline_y = 88` 前一行；
- 使用确定性中位切分量化；
- 使用最近邻生成 4× 预览。

清理文件：

```text
art-source/character-v2/pixellab/P1/cleaned-64x96.png
SHA-256: 45E21D3EDABBB201239B359EAAFFDD9C74EC23A5584880914CA6FE10E178AA47

art-source/character-v2/pixellab/P1/sprite-preview-4x.png
SHA-256: 4077F7CE346AA377E7A2E5B9BBDE507ADECE83F0470B5F1CAAFC2843AEB3BC8E
```

指标：

```text
尺寸：64×96
颜色：21（含透明）
Alpha：0/255
半透明像素：0
不透明包围盒：x=11..60，y=27..87
脚底基线：y=88
```

## 4. 游戏尺寸证明

等价本地地图预览：

```text
art-source/character-v2/pixellab/P1/map-preview.html
```

真实渲染截图：

```text
art-source/character-v2/pixellab/P1/map-desktop-down.png
1440×1000
SHA-256: 2F503F79AF0891BF95A9D59599F0AB8F718746B3AE063B6558DB8459CDE3FD43

art-source/character-v2/pixellab/P1/map-mobile-down.png
390×844
SHA-256: 032E697D99E920066D44CA09E82713F2AA1877653A7D88939825BBA39AE6E1B9
```

Playwright 实测角色显示矩形：

```text
desktop: 48×72 px
mobile: 48×72 px
console errors: []
```

角色作为 `48×72` 地图元素嵌入，不是把大图贴在页面下方。

## 5. 视觉检查

通过项：

- 蓝发和浅蓝发尾可读；
- 左右鲸鳍耳仍能看出；
- 蓝白女仆/学院服和冰白围裙可读；
- 右侧鲸尾与裙摆分离；
- 48×72 尺寸下仍能识别为同一角色；
- 没有背景污染或半透明彩边；
- 色板为 21 色。

保留意见：

- 64×96 标准模式仍是 Q 版比例，脸部和饰件细节有限；
- 这是 P1 技术验证图，不是最终 X1/Gate A 视觉锚点；
- 不能据此直接批量制作动画。

## 6. 四方向能力

PixelLab 的“从参考文献创建”可进入 `V3 Standard` 四方向流程：

- 可上传南向参考；
- `4 迪` 选项可用；
- 页面显示 `1/4` 上传状态；
- 显示费用 `8 generations`；
- `专业` 模式标记为订阅项，但本次四方向入口本身未要求购买；
- 没有提交四方向生成，因为 P1 只需静态验证，避免在 Gate 2 前扩大范围。

结论：四方向能力“可见且可进入”，但尚未有生成结果；是否值得消耗 8 代，留待 Agent A 决定。

## 7. 额度

```text
本轮静态转换：1 generation
可见画廊条目：3
付款：0
订阅：0
Pro：未使用
```

详见：

```text
art-source/character-v2/pixellab/P1/credit-log.json
```

## 8. 测试结果

完整回归：

```text
.venv\Scripts\python.exe -m pytest -q
252 passed, 9 skipped, 1 failed
```

唯一失败为既有 OpenAPI 快照不一致：

```text
tests/test_b6_api.py::test_checked_in_openapi_matches_runtime_schema
```

排除该既有失败后：

```text
.venv\Scripts\python.exe -m pytest -q -k "not test_checked_in_openapi_matches_runtime_schema"
252 passed, 9 skipped, 1 deselected
```

## 9. 停止门

```text
P1 静态技术处理：PASS
P1 四方向：AVAILABLE，但未生成
动画：未开始
P2：未开始
生产接入：未开始
```

等待 Agent A 审查 P1。A 未通过前不制作 idle、walk 或任何批量动作。
