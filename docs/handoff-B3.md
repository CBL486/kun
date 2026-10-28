# B3 NPC 脚本运行时交接

状态：本地实现完成，等待 A 验收

批次：B3

日期：2026-10-28

分支：`codex/bx-b3-npc-runtime`

## 1. 实现范围

B3 在 B1/B2 之上提供四名确定性脚本 NPC：

- 陈岚：图书馆员兼校刊指导；
- 苏晚：视觉传达学生、校刊版面成员；
- 高原：食堂经营者；
- 顾言：摄影专业学生、校刊摄影。

实现内容：

- 工作日、周末日程和地点；
- `SCHEDULED`、`COMMUTING`、`AVAILABLE`、`BUSY`、`CLOSED`、`ASLEEP`、`REACTION_PENDING`、`INTERACTION_COOLDOWN` 状态；
- 固定状态迁移表；
- 最小知识上下文和私有事实隔离；
- 已审核反应模板；
- 同一事件、NPC、模板去重；
- 同一 NPC 48 小时重复台词控制；
- 每个事件最多两个 NPC 反应；
- 每名 NPC 最多 8 个有限记忆槽；
- 普通槽确定性淘汰，重要槽不静默覆盖；
- 关系变化仅生成候选，必须绑定正式事件 ID，单维度变化不超过 `0.08`；
- 未知、拒绝、关系门限和模板缺失标准回应；
- 三份原创课程包和十二个冻结事件包。

B3 不调用 LLM，不连接服务器、真实模型、生产数据库或真实用户数据。

## 2. 代码结构

```text
rpg_npc/
  runtime.py      日程、知识、反应、记忆和关系候选
  schedules.py    四名 NPC 日程与状态迁移
  templates.py    审核台词模板和标准回应
  models.py       NPCReaction、RelationshipProposal、ScheduleState
  content.py      课程包和事件包加载校验
  __main__.py     日程演示 CLI
content/b3/
  course-pack.json
  event-pack.json
tests/
  test_b3_npc_runtime.py
scripts/
  run-b3-demo.ps1
  test-b3.ps1
```

## 3. 知识与隐私

NPC 上下文只包含：

- 自身当前时间、地点和运行时状态；
- 同地点可见角色；
- 同地点公开事件摘要；
- 自身 `knowledge_ids`；
- 自身有限记忆槽；
- 自己与主角色的关系快照。

`internal` 事件会抛出 `npc_scope_violation`。其他 NPC 的记忆槽不会进入上下文。

## 4. 反应和记忆

反应选择顺序：

1. 检查 NPC 可用性和事件地点；
2. 过滤 `internal`、禁用事实和关系门限不满足的模板；
3. 按优先级和 `template_id` 确定性排序；
4. 检查事件/NPC/模板去重；
5. 检查同一 NPC 48 小时重复；
6. 生成关系候选和记忆槽写入；
7. 记录审核通过的候选反应，不直接修改世界关系。

普通记忆槽满载时，按过期时间、最后使用时间和槽 ID 确定性淘汰。重要槽不会被普通新记忆覆盖；重要槽满载时返回 `npc_memory_full`。

## 5. 关系绑定

每个 `RelationshipProposal` 都包含：

```text
relationship_id
npc_id
source_event_id
dimension
delta
reason_code
```

`source_event_id` 缺失或不是正式 `evt_` ID 时拒绝。单维度绝对值超过 `0.08` 时拒绝。相同事件和维度重放返回原结果，不重复加分。

## 6. 内容包

课程包包含 3 个原创合成课程夹具；事件包包含 12 个 B0 冻结事件模板。所有条目包含来源、`rights_status` 和 `review_status=approved`。

B3 不直接复读未授权作品。

## 7. 测试

统一命令：

```powershell
pwsh -NoProfile -File scripts/test-b3.ps1
```

当前结果：

```text
B1 17 项通过
B2 12 项通过
B3 21 项通过
合计 50 项通过
```

B3 新增测试覆盖：

- 四名 NPC 无 LLM 完成一天；
- 状态迁移表拒绝未登记跳转；
- 日程地点与冻结场景一致；
- 内部事件和他人记忆不进入 NPC 上下文；
- 不知道与拒绝回应；
- 模板缺失安全降级；
- 禁用事实阻止模板；
- 同事件/模板不重复；
- 48 小时重复台词控制；
- 普通记忆淘汰和重要记忆保护；
- 关系事件绑定与重放；
- 单次关系变化上限；
- 单事件最多两个 NPC 反应；
- 内容包授权与审核状态。

## 8. 已知限制

- 当前 NPC 状态和记忆仍在内存中，B4 负责 SQLite 持久化与投影核对；
- 关系提交目前由独立测试适配器执行，后续由统一世界事务接入；
- 事件包复用 B0 冻结模板，不新增剧情；
- 真实模型不参与 NPC 日常行为；
- 并发租约和崩溃恢复留给 B8。

## 9. 交接字段

```text
任务 ID：B3 NPC 脚本运行时
分支：codex/bx-b3-npc-runtime
提交哈希：86b2f41
改动文件：rpg_npc/、content/b3/、tests/test_b3_npc_runtime.py、scripts/run-b3-demo.ps1、scripts/test-b3.ps1、README.md、docs/handoff-B3.md
实现摘要：四名 NPC 的日程状态机、知识隔离、模板反应、有限记忆、关系候选和内容包。
测试命令：pwsh -NoProfile -File scripts/test-b3.ps1
测试结果：B1 17 项、B2 12 项、B3 21 项，共 50 项通过
seed / mock：20261028；rule_only；NPC 不调用 LLM
已知风险：B4/B8 持久化、统一世界事务和崩溃窗口尚未覆盖。
需要 A 合并的文件：本分支 B3 文件和交接记录
需要 A 在服务器执行的动作：无
```
