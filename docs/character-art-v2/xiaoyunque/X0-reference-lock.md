# ART-V2 小云雀 X0 参考能力检查

状态：`PASS WITH EXPORT LIMITATION`，等待 Agent A 审查

日期：2026-11-10

执行人：Agent B

分支：`codex/character-art-xiaoyunque`

基线：`623f4888763c92b928c23dacbc21c519ff07babf`

## 1. 唯一视觉母版

```text
art-source/character-v2/workbuddy/2026-11-10/lin-cheng-blue-fat-fish-approved-reference.png
```

```text
SHA-256: 53435A18105C34843611EA6FAEFD7CD5BBBAFDEF5FD3A142BB4C711E6AF54306
尺寸：1024×1024
```

该图只用作视觉参考，不作为运行时文件。使用边界：

- 不复制参考图中的人物身份、脸部细节、原服装图案、现有动漫 IP 或官方吉祥物；
- 只提取深海蓝长发、浅蓝发尾、左右大鲸鳍耳、鲸尾、蓝白女仆/学院服、
  圆脸大眼和圆润但不幼态的视觉语汇；
- 最终角色是原创的林澄；
- 不手工删除平台 AIGC 标识；
- 下载所得 480 预览只作为 X0 证据，不进入运行时或发布包。

## 2. 浏览器与参考图能力

执行环境：

```text
浏览器：Microsoft Edge
页面：https://www.xiaoyunque.com/project
登录状态：已登录
模型：智能图片V2.5 Pro
内部模型标识：gpt_image_2_5_sunburst
画幅：1:1
分辨率：2K
画质偏好：轻度
页面单张标价：3 积分
```

Edge 的 ChatGPT 扩展已启用“允许访问文件 URL”。自动化文件选择在当前项目页
成功附加母图；小云雀识别参考图并完成生成。平台在第一次提交前弹出素材授权
确认，项目所有者明确确认母图已获合法授权后才继续。

结论：

```text
参考图读取：PASS
参考图编辑入口：PASS，页面提供“局部编辑”和参考素材替换
参考一致性生成：PASS
平台 AIGC 标识：保留在项目页，画面显示“包含 AI 生成内容”
```

## 3. X0 实际生成

提交时间：`2026-11-10 22:09:12`

完成时间：`2026-11-10 22:10:48`

提交提示词：

```text
使用已附加的参考图作为唯一视觉参考，生成 1 张 X0 参考一致性与风格可用性测试图。
角色是原创的 19 岁成年女性林澄，不复制参考图中的人物身份、脸型细节、原服装图案、
现有动漫 IP 或官方吉祥物。保留参考图的视觉语汇：深海蓝长发与浅蓝发尾；左右两枚
大鲸鳍耳从头部两侧展开；圆脸、大眼、圆润但不幼态；深蓝白女仆/学院式服装；冰白
围裙；腰部鲸尾扣；身后有与身体分离、轮廓清楚的大鲸尾；蓝白高对比。现代游戏角色
设定图，半 Q 比例，3/4 站姿，全身完整不裁切。衣服必须有清楚层级：深蓝外层、冰白
围裙、腰扣至少两个明暗色阶；头发不能遮住身体主体；头和身体比例协调，不能头大身小。
纯浅蓝灰色背景，单角色，无文字、无 logo、无边框、无水印、无拼贴，不出现真人、
Cosplayer、现有 IP 或品牌。输出应便于后续透明抠图和像素化。仅做 X0 单张测试，
不制作四方向，不制作动画。
```

平台实际生成记录：

```text
文件名：lincheng_x0_test.png
模型：智能图片V2.5 Pro
参数：1:1、2K、轻度
实际扣点：3
```

已保存证据：

```text
art-source/character-v2/xiaoyunque/X0/lincheng-x0-test-01-platform-480.png
尺寸：480×480
SHA-256: 612F827D13757D4FA010B922E6CEBB226212ECB3F65A925327FA1944E7B0A68F

art-source/character-v2/xiaoyunque/X0/lincheng-x0-test-01-canvas-proof.png
尺寸：1272×620
SHA-256: 9232D1BA53F5BF705635CE85F854145E2489876361F289A270A16E699A94F8BE
```

## 4. 色板摘要

参考图 20 色量化摘要：

```text
#EFE7D3  #445986  #2E3E6B  #050B25  #242746
#F7F7F3  #F5F1EC  #8D8CA1  #5075A2  #F7D9CC
#A5AFC3  #395383  #D1CFD7
```

X0 候选 20 色量化摘要：

```text
#C5D3E4  #3E5284  #F9F6F6  #232A4F  #6479A5
#B3BDD7  #CED8E7  #BED7E9
```

## 5. 视觉验收

通过项：

- 单角色，全身完整，未裁切；
- 深海蓝长发和浅蓝发尾清楚；
- 左右大鲸鳍耳、鲸尾、蓝白女仆/学院服和冰白围裙均可读；
- 圆脸、大眼，整体是圆润但不幼态的成年角色；
- 头发没有完全遮住围裙主体；
- 无文字、logo、边框、拼贴、真人或 Cosplayer；
- 背景为浅蓝灰色平涂，适合后续确定性抠图；
- AIGC 标识保留在小云雀项目页。

保留意见：

- 当前可见的是平台 480 预览；页面内 2K 图的“下载”按钮没有产出文件，
  `pageAssets` 对 2K 原始资源返回安全校验失败；
- 因此 2K 原图只存在小云雀项目云端，仓内证据暂为 480 预览与画布截图；
- 第一张已经达到“参考能力可用”的判定门槛，但不能把 480 预览用于运行时；
- 正式接入前必须在 X1 获取可验证的 1024 或更高分辨率原图。

## 6. 积分记录

```text
开始时可见积分：1390
本次实际消耗：3
结束时可见积分：1387
X0 阶段上限：100
X0 剩余预算：97
```

明细见：

```text
art-source/character-v2/xiaoyunque/X0/credit-log.json
```

## 7. 判定与停止条件

```text
参考图读取能力：PASS
参考一致性生成：PASS
风格可用性：PASS
干净背景/可抠图条件：PASS
普通蓝发动漫少女风险：LOW
角色关键特征可读性：PASS
高分辨率下载：BLOCKED BY PLATFORM EXPORT
```

X0 能力验证通过，可以等待 Agent A 审查。未经 Agent A 明确批准，不进入 X1，
不制作四方向、表情、角色卡或动画，不修改运行时资源。

## 8. 基线测试

完整测试：

```text
.venv\Scripts\python.exe -m pytest -q
252 passed, 9 skipped, 1 failed
```

唯一失败为既有 OpenAPI 快照测试：

```text
tests/test_b6_api.py::test_checked_in_openapi_matches_runtime_schema
```

失败原因是 `docs/openapi-v2.json` 与当前测试环境生成的运行时 schema 不一致。
本轮未修改任何 API 或业务代码，因此判为环境/既有基线问题。

排除该既有失败后：

```text
.venv\Scripts\python.exe -m pytest -q -k "not test_checked_in_openapi_matches_runtime_schema"
252 passed, 9 skipped, 1 deselected
```
