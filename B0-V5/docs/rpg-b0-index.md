# RPG 世界 B0 契约索引 V5

状态：提交 G1 评审的 B0 草案

批次：B0

日期：2026-10-28

任务来源：《协作 Agent B RPG 世界详细任务单 V5》

## 1. 文档清单

| 契约 | 解决的问题 |
| --- | --- |
| [世界本体](rpg-world-ontology-v1.md) | 世界事实、实体、标识、时间、状态权限和 JSON 结构 |
| [主智能体循环](agent-loop-v1.md) | 感知、召回、意图、裁决、叙事、重试、降级和预算 |
| [NPC 脚本运行时](npc-script-runtime-v1.md) | 四名 NPC、日程、知识边界、有限记忆和台词反应 |
| [导演事件](director-events-v1.md) | 候选事件、注册表、优先级、约束和越权防护 |
| [行动与事件](mvp-actions-v1.md) | 九个动作、ActionIntent、正式事件和状态修改白名单 |
| [七天切片场景](mvp-slice-scenarios.md) | 固定 seed、七天主线、预算、观察者路径和验收矩阵 |
| [需求与风险](rpg-mvp-risks.md) | 要求、已采用决策、G1 待定项、风险和 B1 至 B13 继承 |

## 2. 本轮范围和停止点

本批只写契约与静态验证材料：

- 不实现 B1 模拟器；
- 不实现 B2 主智能体核心；
- 不实现 B3 NPC 运行时；
- 不实现 B4 SQLite 或迁移；
- 不实现 B5 API、B6 Web 或 B7 集成；
- 不开始 B8 至 B13；
- 不接触服务器、生产数据库、生产 key 或真实用户数据。

B0 完成后必须停下，等待 A 的 G1 冻结结论。

## 3. 核心冻结输入

如果 G1 接受本草案，以下内容应被作为 B1 的共同输入：

```text
scenario_id       = slice-seven-day-v1
seed              = 20261028
world_id          = world_qinghe_v1
main_character_id = char_lin_cheng
npc_count         = 4
location_count    = 6
action_count      = 9
director_templates = 12
start             = 2026-11-02T06:40:00+08:00
timezone          = Asia/Shanghai
default_run_mode  = rule_only
```

这些只是待冻结值。A 修改任何一项时，应同步更新七天场景、测试预算和交接版本。

## 4. 本地验证

在仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/check-b0-v5.ps1
git diff --check
```

静态检查验证：

- 七份必需文档存在；
- 文档标明 B0 草案；
- 九个动作恰好匹配；
- 四名 NPC 和六个地点存在；
- 十二个导演模板存在；
- 七天日期与固定输入存在；
- 关键安全和越权规则存在；
- 本地 Markdown 链接可解析；
- 没有明显凭据样式；
- Git 没有空白字符错误。

当前环境没有可用的 Python 解释器，因此本轮不以 Python 测试作为 B0 证据。B1 实现开始前，A 应确认其评审环境的 Python 版本和测试命令。

## 5. 资料冲突处理

新 V5 任务书优先于仓库中的 V4 时代 B0 草案。旧文件 `docs/contracts/b0/` 保留为历史背景，但不再是当前世界、导演、NPC 或七天场景的冻结候选。

任务书引用的两个 ADR 和上级 V4 文件未在当前仓库找到。此缺口已列入 [`rpg-mvp-risks.md`](rpg-mvp-risks.md) 的 G1-01，未被静默忽略。

## 6. 评审入口

- 评审请求：[review-request-B0-V5.md](review-request-B0-V5.md)
- 交接记录：[handoff-B0-V5.md](handoff-B0-V5.md)
- A 的评审结果目标路径：`docs/review-result-B0.md`

G1 通过前不提交 B1 代码，不创建服务器动作，也不声称本地实现已经可部署。
