# ART-V2 Gate A 风格探索

状态：完成，等待 Agent A 选择方向  
日期：2026-11-08  
分支：`codex/character-art-v2`  
基线：`2b795f8b70078c482f993c9f2897dd7e26c0afc1`

## 1. 本轮结论

已按任务书完成 3 个视觉方向，每个方向包含：

- 2 张方向缩略图；
- 1 张主视觉小样；
- 一套建议色板；
- 与当前地图的并排对比。

B 推荐以方向 B“海玻璃学院轻量像素”为基础进入 Gate B。方向 A 的细节和气质最好，但装饰密度过高；方向 C 的海报轮廓最强，但背景依赖较重，不适合作为地图小人直接生产。A 仍可在 Gate A 选择其他方向或给出混合规则。

## 2. 方向 A：深海童话装饰系

视觉关键词：

- 最接近当前 00A 候选的气质；
- 深海蓝、青绿、冰白和少量暖金；
- 长发、鳍饰、珍珠链和鲸尾扣饰细节丰富；
- 情绪安静、梦幻、略带神秘。

优点：

- 主视觉最有记忆点；
- 眼睛、发丝和服装材质最精细；
- 与“蓝色鲸鱼少女”的视觉联想最直接。

风险：

- 金属链、挂坠和蕾丝过多，缩小到 64×96 后会变成噪声；
- 细节会显著增加逐帧动画成本；
- 目前仍是高分辨率像素化插画，不是原生像素簇。

文件：

```text
art-source/character-v2/candidates/gate-a/a-thumb-01.png
art-source/character-v2/candidates/gate-a/a-thumb-02.png
art-source/character-v2/candidates/gate-a/a-hero.png
docs/character-art-v2/gate-a-a-direction.png
```

## 3. 方向 B：海玻璃学院轻量像素

视觉关键词：

- 更简洁的蓝白学院服装；
- 清晰深色描边和较少的装饰；
- 青绿鳍饰与深蓝长发保持为身份锚点；
- 小尺寸可读性优先。

优点：

- 最适合 64×96 地图角色和后续七套动作；
- 面部、头发和服装轮廓在小尺寸下最清楚；
- 色板和像素密度最容易收敛为正式资产。

风险：

- 比方向 A 少了华丽感；
- 当前候选服装比任务书原设定更偏学院制服；
- Gate B 如果选 B，需要把海军蓝短外套和冰白内搭重新校准，避免角色变成普通校服少女。

文件：

```text
art-source/character-v2/candidates/gate-a/b-thumb-01.png
art-source/character-v2/candidates/gate-a/b-thumb-02.png
art-source/character-v2/candidates/gate-a/b-hero.png
docs/character-art-v2/gate-a-b-direction.png
```

## 4. 方向 C：潮汐复古海报像素

视觉关键词：

- 更强的大色块和黑色轮廓；
- 发尾与衣摆呈海浪状展开；
- 深色背景、青色轮廓光和少量星点高光；
- 更像复古游戏封面或角色海报。

优点：

- 轮廓最鲜明；
- 很适合主视觉、加载页和角色展示舞台；
- 在暗色场景中辨识度最高。

风险：

- 背景和角色绑定明显，不适合直接裁成地图角色；
- 光效和星点较多，缩小后容易糊成亮点；
- 作为 64×96 运行时动作的参考成本高于方向 B。

文件：

```text
art-source/character-v2/candidates/gate-a/c-thumb-01.png
art-source/character-v2/candidates/gate-a/c-thumb-02.png
art-source/character-v2/candidates/gate-a/c-hero.png
docs/character-art-v2/gate-a-c-direction.png
```

## 5. 汇总证据

九宫格：

```text
docs/character-art-v2/gate-a-contact-sheet.png
```

与当前地图并排：

```text
docs/character-art-v2/gate-a-map-comparison.png
```

色板：

```text
docs/character-art-v2/gate-a-palettes.png
```

尺寸、模式和 SHA-256：

```text
docs/character-art-v2/gate-a-assets.json
```

完整提示词：

```text
art-source/character-v2/gate-a-prompts.json
```

生成、积分和候选采用记录：

```text
art-source/character-v2/prompt-log.json
```

## 6. 积分

| 项目 | 积分 |
| --- | ---: |
| Gate A 开始余额 | 1474 |
| Gate A 生成 | 20 |
| Gate A 结束余额 | 1454 |
| 00A 已用 | 4 |
| 当前总计已用 | 24 |

Gate A 上限为 120，实际使用 20。其中包含一次 `a-thumb-02` 的自动化下载误选后重做，额外消耗 2 积分。

## 7. 技术观察

- 九张候选均为 1024×1024 PNG；
- 均保留 TC260 AIGC 元数据；
- A 方向与 C 方向部分候选有可见“AI生成”角标；
- 这些角标和元数据不能为了无水印要求而直接删除；
- 当前结果适合 Gate A 风格判断，但不能直接作为最终运行时精灵；
- Gate B 及后续必须另做像素级重绘、色板压缩和边缘清理。

## 8. B 推荐

推荐方向：**B 海玻璃学院轻量像素**。

推荐理由：

- 最适合 64×96 地图角色；
- 最容易扩展成七套四方向动画；
- 头发、鳍饰、蓝白服装和青绿眼睛在小尺寸下仍有辨识度；
- 允许后续从 A 借用眼睛细节、从 C 借用轮廓光，而不承担两者的完整复杂度。

需要 A 决策：

1. 选择 A、B 或 C；
2. 是否允许“B 为主体，A 的面部细节和 C 的轮廓光只用于主视觉”；
3. 确认正式商用条款风险由项目方接受，或要求平台书面确认；
4. Gate A 选型确认前，不进入 Gate B。
