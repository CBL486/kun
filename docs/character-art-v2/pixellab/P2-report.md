# ART-V2 PixelLab P2 四方向静态验证报告

状态：`P2-0 READY FOR A REVIEW`

日期：2026-11-14

执行人：Agent B

审查人：Agent A

分支：`codex/character-art-pixellab-p2`

基线：`origin/main` `0a9e70b`

## 1. 本轮范围

按 P2 任务书的停止门，本轮只执行 P2-0 嘴唇颜色修正。

P2-1 四方向生成尚未开始，未消耗 PixelLab generation，未购买 Pro，
未订阅，未制作 idle/walk，未修改生产资源。

## 2. P1 资源依赖

最新 `origin/main` 已包含 P1 验收文档，但不包含 P1 的实际美术资源。
为避免新检出的 P2 分支缺少任务书指定输入，已将 P1 已验收资源从：

```text
codex/character-art-pixellab-p1
53b08f125dc831789cfa7f6f138d32fc2b8d9bb6
```

同步到当前分支的：

```text
art-source/character-v2/pixellab/P1/
```

未修改 P1 文件。P2 的唯一输入为：

```text
art-source/character-v2/pixellab/P1/cleaned-64x96.png
SHA-256: 45E21D3EDABBB201239B359EAAFFDD9C74EC23A5584880914CA6FE10E178AA47
```

## 3. 唇色修正

采用确定性局部像素替换，不使用新的 AI 生成结果。修改区域严格限制在嘴部：

| 坐标 | 原始颜色 | 修正颜色 | 用途 |
| --- | --- | --- | --- |
| `(29,53)` | `#B5A9BC` | `#B85F6C` | 上唇主色 |
| `(30,53)` | `#B5A9BC` | `#B85F6C` | 上唇主色 |
| `(31,53)` | `#B5A9BC` | `#B85F6C` | 上唇主色 |
| `(30,54)` | `#FAD4CA` | `#8D4654` | 下唇阴影 |

独立差分确认只改变 4 个像素，变化包围盒为 `(29,53,32,55)`。
眼睛、头发、鳍耳、服装、围裙和鲸尾均未改变。

## 4. 技术指标

```text
尺寸：64×96
总色板：23 色（含透明）
不透明色：22 色
Alpha：0/255
半透明像素：0
不透明包围盒：x=11..60，y=27..87
变化像素：4
变化区域：mouth-only
```

确定性脚本重复运行后，输出 SHA-256 保持一致：

```text
59DBED82B0CB2E3FE5D1E55F7428CE1B139891D383943BC00DFFF2EBC745AF79
```

## 5. 视觉检查

8× 近邻放大预览：

```text
art-source/character-v2/pixellab/P2/lip-fixed-preview-8x.png
512×768
```

检查结果：

- 嘴部现在为低饱和玫瑰色；
- 嘴线下方有 1 像素自然阴影；
- 嘴部不再显示蓝灰唇色；
- 眼睛、头发、鳍耳、服装、围裙和鲸尾保持原样；
- 像素边缘保持硬边，没有抗锯齿或半透明污染。

## 6. 交付文件

```text
art-source/character-v2/pixellab/P2/
  lip-fixed-64x96.png
  lip-fixed-preview-8x.png
  lip-metrics.json
  credit-log.json

scripts/character_pixellab_p2_lip_fix.py
```

## 7. 回归测试

使用项目标准测试入口：

```text
.\scripts\test-b7.ps1
262 passed, 1 warning
```

唯一警告为 `.b6-deps` 中 Starlette/httpx 的上游弃用提示，不影响测试结果。

## 8. 额度与停止门

```text
P2-0 唇色：READY FOR A REVIEW
P2-1 四方向：未开始
本轮 PixelLab generations：0
付款：0
订阅：0
Pro：未使用
```

按任务书要求，在此停止，等待 Agent A 对 P2-0 给出通过结论后，
才可使用 `lip-fixed-64x96.png` 作为南向参考进入一次四方向静态验证。
