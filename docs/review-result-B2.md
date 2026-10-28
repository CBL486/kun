# B2 评审结果

评审人：Agent A

评审日期：2026-10-28

结论：**通过，允许进入 B3**

## 1. 审查基线

- B2 实现分支：`codex/bx-b2-agent-core`
- B2 实现提交：`144a768`
- 交接回填提交：`d3943e6`
- A 整合分支：`codex/g2-b2-integration`

## 2. 验收证据

```text
B1 unittest：17 项通过
B2 unittest：12 项通过
B1+B2 合计：29 项通过
项目 pytest：32 项通过
```

B2 演示命令成功提交了一个带正式事件 ID 的 `eat` 动作，并返回：

- 最小感知包；
- 候选列表；
- 决策轨迹；
- `IntentProposal`；
- `ActionIntent`；
- 世界事件与状态变化。

## 3. 已确认通过的能力

- 结构化意图不会直接修改世界。
- 未声明的意图字段会被拒绝。
- 候选动作来自合法集合。
- 同 seed 和同状态产生相同决策。
- 决策轨迹包含候选分数、理由和未选候选。
- 关系变化绑定正式事件 ID。
- operation 重放不重复事件或关系。
- 过期状态可以重新感知和规划，但不重复提交。
- 模型格式错误会降级到规则模式。
- 感知包不包含私有字段或内部数据库字段。

## 4. 接受的有意限制

- 当前策略仍是确定性 `balanced_curiosity_v1`，真实 LLM 适配在 B9。
- B2 世界和 operation 缓存仍在内存，B4/B8 负责持久化、租约和崩溃窗口。
- 课程和事件候选仍使用冻结场景夹具。
- 关系结算复用 B1 引擎，B3 再补齐 NPC 知识、冷却和模板矩阵。

## 5. 流程问题

B2 实现基于 B1 分支而不是 A 的最新 `main`。A 已将 B2 文件单独 graft 到当前 B1 主线上，没有覆盖服务器配置、V6 文档或 README 安全边界。

B3 开始前必须：

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/bx-b3-npc-runtime
```

## 6. 允许的下一批

允许 B 开始 **B3 NPC 脚本运行时**。

B3 继续遵守：

- 不登录服务器；
- 不接触生产密钥或真实用户数据；
- 使用固定 seed、mock LLM、mock 审核器；
- 每个 NPC 必须能在不调用 LLM 的情况下跑完一天；
- 不知道、拒绝、冷却、关系阈值和记忆槽必须有测试；
- 完成后提交独立分支和交接记录，等待 A 评审。
