# B0 交接记录 V5

任务 ID：B0

分支：`codex/bx-b0-v5-contracts`

实现提交：`1ea7f05`

日期：2026-10-28

状态：B0 草案已提交本地分支，等待 A 的 G1 评审与冻结

## 1. 改动文件

七份 V5 必需草案：

- `docs/rpg-world-ontology-v1.md`
- `docs/agent-loop-v1.md`
- `docs/npc-script-runtime-v1.md`
- `docs/director-events-v1.md`
- `docs/mvp-actions-v1.md`
- `docs/mvp-slice-scenarios.md`
- `docs/rpg-mvp-risks.md`

评审与验证材料：

- `docs/rpg-b0-index.md`
- `docs/review-request-B0-V5.md`
- `scripts/check-b0-v5.ps1`

历史状态说明：

- `README.md`
- `docs/contracts/b0/README.md`
- `docs/review-request-B0.md`
- `docs/handoff-B0.md`

## 2. 实现摘要

- 将 V4 时代的 AI 学校 B0 标记为历史资料，建立 V5 单镇一人主智能体契约入口。
- 定义世界权威状态、模型权限、时间、标识、重放、实体、事件、关系、记忆和隐私边界。
- 定义主智能体的感知、召回、Intent、世界裁决、叙事、幂等、预算和失败降级。
- 定义四名无 LLM 脚本 NPC、日程、知识过滤、有限记忆槽、关系阈值和台词模板。
- 定义导演只产生候选、优先级、约束和可见提示，不能写状态或选择最终行动。
- 固定九个世界动作、状态修改白名单、正式事件、可见范围和错误码。
- 固定 seed `20261028`、`slice-seven-day-v1`、七天日期、每日动作路线、预算和失败注入。
- 列出 G1-01 至 G1-08 待 A 决定事项，以及 B1 至 B13 的继承要求。
- 增加 PowerShell 静态校验脚本，验证文件、动作、NPC、地点、导演模板、七天预算和链接。

## 3. 测试命令

```powershell
pwsh -NoProfile -File scripts/check-b0-v5.ps1
```

```powershell
git diff --check
```

## 4. 测试结果

```text
B0 V5 静态契约检查通过
必需文档：7
允许动作：9
脚本 NPC：4
地点：6
导演模板：12
七天日期：7
Git 空白字符检查：通过
```

本轮没有运行实现测试，因为 B0 不包含 B1 模拟器或 API，而且当前执行环境没有可用的 Python 解释器。没有把“文档静态检查通过”写成“模拟器可运行”或“生产可部署”。

## 5. seed、mock 与可重复范围

- 场景：`slice-seven-day-v1`
- seed：`20261028`
- 开始：`2026-11-02T06:40:00+08:00`
- 时区：`Asia/Shanghai`
- 运行模式：`rule_only`
- mock：LLM、审核器、计费器均计划在 B1/B7 使用确定性 mock
- 可重复：世界决策、动作、事件、状态、关系和业务快照
- 可变化：真实模型生成的叙事文字，但必须对应同一正式事件和召回包

上述可重复性目前是契约，不是已实现结果。

## 6. 已知风险

- 任务书引用的两个 ADR 和上级 V4 文件不在当前仓库。
- 当前仓库没有配置共享 Git 远程，A 尚未通过远程获取本分支。
- 真实模型价格未确认，0.10 元/日是临时估算上限。
- 单事务与投影对账的最终方案尚未由 A 冻结。
- 课程版权审核负责人尚未确定。
- B1 至 B13 均未实现，不能把 B0 草案当成应用交付物。

## 7. 需要 A 合并的文件

优先评审：

```text
docs/rpg-b0-index.md
docs/rpg-world-ontology-v1.md
docs/agent-loop-v1.md
docs/npc-script-runtime-v1.md
docs/director-events-v1.md
docs/mvp-actions-v1.md
docs/mvp-slice-scenarios.md
docs/rpg-mvp-risks.md
docs/review-request-B0-V5.md
scripts/check-b0-v5.ps1
```

历史说明只需同步，不应作为 V5 实现输入。A 评审通过后，将冻结版本写入 `docs/review-result-B0.md` 并按双方流程合并。

## 8. 需要 A 在服务器执行的动作

B0 不需要任何服务器动作。

A 只需在本机评审分支、确认 G1-01 至 G1-08 并记录冻结结论。服务器、生产数据库、生产密钥、计划任务、反向代理、部署和回滚在 G1 前均不得因 B0 被触发。

## 9. 下一步

停在 B0，等待 A：

1. 复核七份契约；
2. 补齐或确认缺失的上级资料；
3. 对 G1-01 至 G1-08 作出决定；
4. 写 `docs/review-result-B0.md`；
5. 明确是否允许开始 B1。
