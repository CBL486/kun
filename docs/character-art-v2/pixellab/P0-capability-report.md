# ART-V2 PixelLab P0 免费试用能力报告

状态：`CONDITIONAL PASS / NOT PRODUCTION READY`

日期：2026-11-13

执行人：Agent B

分支：`codex/character-art-pixellab`

基线：`b93eae41783205c2d2937e89397212a53c43fa9a`

生产边界：未购买订阅，未修改运行时资源，未进入 P1，不接触生产环境。

## 1. 工具与账号状态

PixelLab 官网当前免费试用信息：

```text
40 fast generations
之后每天 5 次较慢生成，最多保存 20 次
无需信用卡
页面提供商业使用许可说明，但不自动购买或订阅
```

实际入口：

```text
PixelLab → 创造者 → 图像到像素艺术
模式：标准
Pro：不可用，需要订阅
```

本次只使用“标准”免费模式。没有点击 Pro、购买、订阅或升级。

## 2. 输入与工具能力

唯一视觉母版：

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

母版保持原样，没有覆盖或删除 AIGC 标识。

PixelLab 的“从参考图创建角色”入口最高只接受 `256×256` 图片，因此另外保存了
一份不改原图的 `256×256` 技术缩略参考：

```text
art-source/character-v2/pixellab/P0/inputs/lin-cheng-pixellab-reference-256.png
SHA-256: 6C00714C5A243F6ED2E3EA6068A4AA0D8F4C7874FD27308BE08664B73A3124C1
```

该缩略图只作为 PixelLab 输入，不是运行时资源。

“图像到像素艺术”已确认支持：

- 从本地图片上传；
- 标准模式生成；
- 忠诚模式开关；
- 生成后下载 PNG；
- 输出像素网格和有限色板；
- 输出文件尺寸会按源图自动选择。

## 3. P0 实际生成

文件名：

```text
art-source/character-v2/pixellab/P0/candidates/pixellab-p0-image-to-pixel-64.png
```

平台显示尺寸：`64×64`

实际文件属性：

```text
尺寸：64×64
模式：RGBA
颜色数：206（含完全不透明背景）
非透明像素：全部
Alpha 范围：255–255
SHA-256: A0B71A479FC47C6298A5863C96AA5DBD927A2E6009D814ABBF5182F6FB1BC970
```

4× 最近邻预览：

```text
art-source/character-v2/pixellab/P0/candidates/pixellab-p0-image-to-pixel-4x.png
```

输入与输出对照：

```text
art-source/character-v2/pixellab/P0/candidates/pixellab-p0-comparison.png
```

输出检查：

- 是完整单角色，头部、身体、服装和鲸尾都在画面内；
- 鲸鳍耳、蓝白女仆服、冰白围裙和鲸尾仍然可辨；
- 是实际像素网格，不是把 1024 原图直接缩小；
- 轮廓清楚，适合作为 PixelLab 基础测试；
- 背景仍然是不透明浅色，不是透明 PNG；
- 颜色数 206，不符合最终 16～24 色运行时限制；
- 平台自动输出为 `64×64`，不是目标的 `64×96`；
- 脸部仍偏通用萌系，不能把本次结果当作 X1 锚点。

## 4. 判定

```text
参考图导入：PASS
像素化生成：PASS
单角色完整性：PASS
关键视觉特征可辨：CONDITIONAL PASS
导出 PNG：PASS
透明背景：FAIL
目标 64×96：FAIL
16～24 色：FAIL
商业使用边界：需项目所有者确认，未自行判断
```

PixelLab 能完成“参考图 → 像素角色”的基础能力验证，但本次标准模式输出不能直接
进入 P1 或生产。若继续 PixelLab 路线，必须先解决透明背景、64×96 逻辑画布和色板
量化；或者将 PixelLab 作为造型/方向生成器，再按任务书进入 Aseprite 技术清理。

## 5. 免费额度记录

页面显示画廊本次有两个可见条目：

1. 一次通用创建的默认“可爱巫师角色”，非本项目资产；
2. 一次 `Image to Pixel Art` 标准转换。

PixelLab 页面在免费试用期间没有显示精确剩余次数，只显示当前免费档位。本次没有
购买、订阅或付款。详细记录见：

```text
art-source/character-v2/pixellab/P0/credit-log.json
```

## 6. 停止门

```text
P0：CONDITIONAL PASS
P1：未开始
P2：未开始
动画：未开始
运行时接入：未开始
```

等待 Agent A 确认是否采用 PixelLab 作为后续造型工具，以及是否允许继续进行
透明背景和 `64×96` 技术处理测试。

## 7. 测试

完整回归：

```text
.venv\Scripts\python.exe -m pytest -q
252 passed, 9 skipped, 1 failed
```

唯一失败为既有 OpenAPI 快照不一致：

```text
tests/test_b6_api.py::test_checked_in_openapi_matches_runtime_schema
```

本轮没有修改 API 或业务代码。排除该既有失败后：

```text
.venv\Scripts\python.exe -m pytest -q -k "not test_checked_in_openapi_matches_runtime_schema"
252 passed, 9 skipped, 1 deselected
```
