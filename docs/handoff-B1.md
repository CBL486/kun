# B1 确定性七日模拟交接

状态：首版已实现并通过本地验收

批次：B1

日期：2026-10-28

## 1. 实现范围

B1 提供 `rule_only` 模式下的七天单镇模拟：

- 固定场景 `slice-seven-day-v1`；
- 固定 seed `20261028`、固定时钟和北京时间；
- 确定性 mock LLM 与 mock 审核器；
- 林澄与四名脚本 NPC；
- 六个地点和公开连通图；
- 九个注册动作；
- 十二个已审核导演模板；
- 每日世界事件、分享、日记、模型调用、token 与 mock 成本硬上限；
- 结构化终端摘要、完整 JSON 报告和确定性世界快照；
- 每个动作后原子写入的检查点，以及暂停、重启、继续和恢复测试；
- 动作重放、过期状态、未知动作和 operation 冲突测试。

B1 不包含 B2 的完整模型候选规划、B4 的数据库持久化、B5 API、B6 Web 或真实模型调用。

## 2. 代码结构

```text
rpg_sim/
  budget.py       每日预算和 mock 成本
  engine.py       世界状态验证、事务式事件提交和日切
  ids.py          稳定 ID 与规范 JSON 哈希
  scenario.py     七日路线、实体、日程、地点和模板注册表
  simulator.py    编排、记忆记录、分享、报告与快照
  __main__.py     CLI
tests/
  test_b1_simulator.py
scripts/
  run-b1.ps1
  test-b1.ps1
```

## 3. 运行和验收

```powershell
pwsh -NoProfile -File scripts/test-b1.ps1
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1
```

不依赖真实 API Key、网络、服务器或生产数据库。没有系统 `python` 时，本地脚本会尝试使用 Codex 桌面运行包中的 Python。

验收命令输出：

```text
B1 七日规则模拟完成
关键事件：9/9（通过）
实体：4 名 NPC，6 个地点，9 个动作，12 个导演模板
事件：41 个世界事件，7 次分享，2 篇私密日记
拒绝：0 个类型化动作失败
```

实际业务哈希以每次生成的 `replay-manifest.json` 为准。相同代码、seed、场景和规则运行两次时，`business_result`、`snapshot_before`、`snapshot_after` 必须相同。

暂停与恢复：

```powershell
python -m rpg_sim seven-day --scenario slice-seven-day-v1 --seed 20261028 --mode rule_only --frozen-clock --output out/b1-checkpoint --pause-after 12
python -m rpg_sim seven-day --scenario slice-seven-day-v1 --seed 20261028 --mode rule_only --frozen-clock --output out/b1-checkpoint --resume
```

检查点使用临时文件加原子替换写入。恢复时会还原世界状态、operation 结果、预算、候选、记忆、分享和路线进度。

## 4. 测试证据

本地 `unittest` 共 17 项通过，覆盖：

- 必需报告字段；
- 两次运行的确定性；
- 七日关键事件；
- 九个动作全部使用；
- 每日硬预算；
- 事件与状态变化可追溯；
- 分享三层结构和 3 至 5 个来源事件；
- 私密日记不进入公开投影；
- NPC 知识边界和反应去重；
- 导演候选来自注册表且不能写状态；
- 周分享跨日召回；
- mock LLM 和 mock 审核器的离线确定性；
- 两次暂停、丢弃进程对象后从检查点恢复，并得到相同业务结果；
- 未知动作、过期状态、operation 重放和冲突拒绝。

## 5. 当前有意保留的限制

- B1 世界保存在内存中，尚无 B4 的 SQLite/PostgreSQL 持久化。
- B1 检查点只保证已写盘边界的恢复；提交与检查点之间的进程强制终止窗口由 B8 的任务租约和对账机制处理。
- B1 使用固定规则路线；真实 LLM 文字和审核供应商不在本批范围。
- 日终回宿舍是一个有稳定 ID、可追溯的内部系统事件，不计入六个角色世界事件。
- 为满足冻结路线的跨地点移动，B1 会沿公开连通图选择确定性的最短路径；B2 将把模型可见候选收敛为单跳移动。
- 河边活动自带午餐、日终日记位置仍使用场景夹具；后续资源与库存批次需要正式建模。

## 6. 停止点

B1 到此停止。数据库迁移、API、Web、集成和服务器动作留给后续批次及 A 的评审授权。

## 7. V6 交接字段

```text
任务 ID：B1 单镇模拟器
分支：codex/bx-b0-v5-contracts-fix
提交哈希：待回填
改动文件：README.md、.gitignore、rpg_sim/、tests/、scripts/、docs/handoff-B1.md
实现摘要：确定性七日规则模拟、mock LLM/审核、预算、快照、暂停、重启和恢复。
测试命令：pwsh -NoProfile -File scripts/test-b1.ps1
测试结果：17 项通过
seed / mock：20261028；rule_only；mock provider
已知风险：检查点提交间隙、跨地点最短路径和河边午餐夹具需由后续批次收敛。
需要 A 合并的文件：本分支全部 B1 文件
需要 A 在服务器执行的动作：无
```
