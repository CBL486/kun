# B2 主智能体核心交接

状态：本地实现完成，等待 A 验收

批次：B2

日期：2026-10-28

分支：`codex/bx-b2-agent-core`

## 1. 实现范围

B2 在 B1 世界引擎之上增加主智能体核心：

- 最小感知包：当前时间、地点、可见设施、需求、目标、附近角色和公开事件；
- 需求、目标和动作选择规则；
- 确定性候选生成、过滤和评分；
- 可解释 `DecisionTrace`，包含分数、理由、未选候选和降级原因；
- 模型层 `IntentProposal` 与世界层 `ActionIntent` 分离；
- 意图字段白名单，模型不能提交事件、状态补丁或关系数值；
- 经营世界引擎校验和提交动作；
- 状态过期后重新读取、重新规划和恢复；
- operation 幂等重放，不重复事件、状态版本或关系变化；
- 模型格式失败后的规则降级记录。

B2 不包含真实 LLM 接入、持久化数据库、调度器、API 或 Web。

## 2. 代码结构

```text
rpg_agent/
  loop.py         主智能体状态机、意图生成与引擎适配
  models.py       Candidate、DecisionTrace、IntentProposal、ActionIntent
  perception.py   最小感知包
  planner.py      balanced_curiosity_v1 候选规则与评分
  __main__.py     单步演示 CLI
tests/
  test_b2_agent_core.py
scripts/
  run-b2-demo.ps1
  test-b2.ps1
```

## 3. 双层意图

`IntentProposal` 是主智能体层输出，包含动作、目标、参数、理由、预期结果和置信度。它不能直接进入世界数据库。

`ActionIntent` 是世界引擎接受的最终请求，补充稳定动作 ID、operation ID、状态版本、来源和 nonce。转换后仍经过 B1 世界引擎字段、前置条件和版本校验。

任何意图都不允许包含：

- `event_id`
- `state_changes`
- 关系数值
- 需求数值
- 奖励或成本
- SQL、URL 或工具调用

## 4. 决策规则

当前策略 ID 为 `balanced_curiosity_v1`。

候选基础分优先级：

1. 当前时段的合法课程；
2. 与校刊目标相关且地点可见的公告；
3. 已注册公开活动；
4. 目标推进和在场 NPC 交流；
5. 饥饿、精力等需求动作；
6. 可达地点移动。

同分按稳定的 `candidate_id` 排序。候选分数包含基于 seed 和候选内容的确定性微小变体，不使用宿主时间或未记录的随机数。

拒绝原因使用稳定代码，例如：

```text
unsupported_action
invalid_parameters
unreachable_target
closed_location
npc_not_present
npc_unavailable
target_not_visible
```

## 5. 关系与幂等

B2 不自行修改关系。`talk` 只提交意图和公开话题，世界引擎负责：

- 验证 NPC 在场与知识依据；
- 生成正式事件 ID；
- 把关系变化绑定到该事件 ID；
- 将单次单维变化限制在 `0.08`；
- 同一 operation 重放时返回原事件，不重复加分。

## 6. 失败恢复

- 模型格式错误：记录 `model_format_error`，使用规则候选继续推进；
- 状态过期：丢弃旧快照决策，重新感知和规划同一逻辑 `operation_id`；
- operation 已提交：返回原事件；
- 无合法候选：产生 `no_op`，不伪造动作；
- 校验失败：世界状态不变。

## 7. 测试

统一命令：

```powershell
pwsh -NoProfile -File scripts/test-b2.ps1
```

当前结果：

```text
B1 17 项通过
B2 12 项通过
合计 29 项通过
```

B2 覆盖：

- 提出意图不修改世界；
- 相同 seed 与状态产生相同候选、意图和事件；
- 感知包不包含私有字段；
- 非法动作和不在场 NPC 被过滤；
- 决策轨迹包含分数与理由；
- 关系变化绑定事件 ID；
- 未声明意图字段被拒绝；
- operation 重放不重复事件和关系；
- 模型格式错误后规则降级；
- 状态过期后同一 operation 恢复；
- ActionIntent 字段白名单；
- 候选 ID 跨实例稳定。

## 8. 已知限制

- 当前为确定性规则策略，真实模型只会在 B9 接入；
- 当前快照和 operation 记录仍在内存中，B4/B8 负责持久化、租约与崩溃窗口；
- 课程与公开事件候选仍基于冻结场景；
- 关系规则复用 B1 世界引擎，B3 将补充完整 NPC 运行时的知识、冷却和模板矩阵；
- 未执行服务器、生产数据库或真实用户操作。

## 9. 交接字段

```text
任务 ID：B2 主智能体核心
分支：codex/bx-b2-agent-core
提交哈希：144a768
改动文件：rpg_agent/、tests/test_b2_agent_core.py、scripts/run-b2-demo.ps1、scripts/test-b2.ps1、README.md、docs/handoff-B2.md
实现摘要：最小感知、确定性候选、决策轨迹、双层结构化意图、幂等与过期恢复。
测试命令：pwsh -NoProfile -File scripts/test-b2.ps1
测试结果：B1 17 项、B2 12 项，共 29 项通过
seed / mock：20261028；rule_only；mock provider
已知风险：B4/B8 持久化与检查点提交窗口尚未覆盖；真实模型适配留到 B9。
需要 A 合并的文件：本分支 B2 文件和交接记录
需要 A 在服务器执行的动作：无
```
