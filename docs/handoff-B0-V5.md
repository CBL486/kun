# B0 V5 复审修改交接

任务 ID：B0 V5 复审修改

分支：`codex/bx-b0-v5-contracts-fix`

复审基线提交：`eda1d3c31e6386e286e361eafb9a00408d4cf71d`

修复提交哈希：待修复提交生成后回填

日期：2026-10-28

状态：复审修改已提交修复分支，等待 A 再次评审；尚未冻结

## 1. 实际路径结构

采用复审意见中的方案 A，统一使用仓库根目录：

```text
docs/
scripts/
```

远端 `main` 中的 `B0-V5/` 包装目录已在修复分支移除。七份核心契约、记忆 ADR 候选、索引、评审请求和交接记录都位于 `docs/`；校验脚本位于 `scripts/`。

## 2. 改动文件

从 `B0-V5/` 移出到根路径：

- `docs/adr-memory-core.md`
- `docs/agent-loop-v1.md`
- `docs/director-events-v1.md`
- `docs/handoff-B0-V5.md`
- `docs/mvp-actions-v1.md`
- `docs/mvp-slice-scenarios.md`
- `docs/npc-script-runtime-v1.md`
- `docs/review-request-B0-V5.md`
- `docs/rpg-b0-index.md`
- `docs/rpg-mvp-risks.md`
- `docs/rpg-world-ontology-v1.md`
- `scripts/check-b0-v5.ps1`

## 3. 复审意见处理

### 3.1 统一交付路径

- 选择方案 A：移动到根 `docs/` 和 `scripts/`。
- 所有命令统一为 `scripts/check-b0-v5.ps1`。
- 删除 `B0-V5/` 目录，不再混用两套路径。

### 3.2 handoff 提交信息

- 原错误的分支和旧哈希已删除。
- 记录当前复审基线 `eda1d3c31e6386e286e361eafb9a00408d4cf71d`。
- 修复分支为 `codex/bx-b0-v5-contracts-fix`。
- 修复提交哈希在本文件回填提交前由该提交生成。

### 3.3 记忆 ADR

采用复审意见中的方案 B，重写 `docs/adr-memory-core.md`：

- 状态改为 B0 复评候选，未冻结；
- 删除“QQ companion 与 AI School 共用”作为当前实现依据的表述；
- 明确 `tenant_id="rpg-world"`；
- 明确 `world_id` 为当前小镇；
- 明确 `character_id` 为主智能体；
- 明确 `surface="school"` 是现有存储兼容值，不是旧学校租户定义；
- 明确 NPC 有限记忆槽属于世界状态，不进入主智能体记忆召回；
- 定义六维作用域、去重、生命周期、强化、召回、事务一致性和 B4 验收。

### 3.4 缺失上级资料

以下资料状态统一为“**A 提供，待整合分支复核**”：

```text
docs/adr-001-single-agent-town.md
docs/adr-002-mvp-runtime.md
上级 RPG智能体世界项目双人任务书_V4.md
```

B 未读取这些文件，也不声称已经核对。A 将它们带入整合分支后，需要复核是否与 V5 单智能体、导演和脚本 NPC 定义冲突。

## 4. A 已接受的 B0 决定

- 用户有限影响：观察、留言、对公开事件反应、请求下一合法 slot 回应。
- 年龄：主智能体 19 岁，全部 NPC 18 岁以上，禁止涉及未成年角色的性内容。
- 预算：每日最多 6 个世界事件、8 次模型调用、24k 输入 tokens、6k 输出 tokens、0.10 元估算成本。
- 事务：同一事务优先，允许待投影记录加幂等核对降级。
- 课程：只使用原创或已授权摘要，B3 提供来源和 `rights_status`。
- B1 验收：结构化终端报告加确定性快照，Web 放到 B6。
- API：B5 前冻结 `/world`、`/agent`、`/timeline`、`/chat`、`/memory` 的公开投影。

## 5. 静态检查命令

在仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/check-b0-v5.ps1
git diff --check
```

## 6. 静态检查结果

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

本轮不运行模拟器或 API 测试，因为 B0 不包含 B1 至 B13 实现。

## 7. seed、mock 与可重复范围

- 场景：`slice-seven-day-v1`
- seed：`20261028`
- 开始：`2026-11-02T06:40:00+08:00`
- 时区：`Asia/Shanghai`
- 运行模式：`rule_only`
- mock：LLM、审核器、计费器均将在 B1/B7 使用确定性 mock
- 可重复：世界决策、动作、事件、状态、关系和业务快照
- 可变化：真实模型叙事文字，但必须对应同一正式事件和召回包

以上仍为契约，不是已运行结果。

## 8. 未完成项

- A 再次复审并决定是否冻结；
- A 将两个缺失 ADR 和上级 V4 文件带入整合分支后复核；
- B1 模拟器和后续批次均未实现；
- PostgreSQL 隔离测试尚未执行；
- 真实模型价格和审核供应商尚未接入；
- 修复分支尚未合并到 `main`。

## 9. 需要 A 执行的动作

B0 不需要服务器动作。A 只需：

1. 拉取并评审 `codex/bx-b0-v5-contracts-fix`；
2. 确认根目录路径和重写后的记忆 ADR；
3. 复核上级资料；
4. 写 `docs/review-result-B0.md`；
5. 明确是否冻结以及是否允许开始 B1。

G1 通过前，B 不开始 B1，也不触碰服务器、生产数据库或真实用户数据。
