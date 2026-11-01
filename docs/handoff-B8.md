# B8 调度、幂等与崩溃恢复交接

状态：本地实现完成，等待 A 复审

日期：2026-11-01

分支：`codex/bx-b8-scheduler`

## 1. 实现范围

- 持久任务队列和优先级调度；
- `operation_id` 幂等入队与冲突检测；
- 任务租约、worker 身份和过期回收；
- PostgreSQL advisory lock 适配；
- 任务超时、指数退避重试和死信；
- 积压、卡死和租约状态查询；
- 进程重启后的未完成任务扫描；
- 观察者留言持久化和 API 重启恢复；
- 本地调度运维 CLI。

B8 不连接生产数据库，不创建服务器计划任务，不执行部署。

## 2. 代码结构

```text
rpg_scheduler/
  models.py      任务规格、状态和执行结果
  repository.py  持久队列、租约、重试和恢复
  locks.py       PostgreSQL advisory lock / SQLite fallback
  service.py     handler 调度、超时和运行循环
  messages.py    观察者留言持久化
  __main__.py    状态、恢复和入队 CLI
rpg_orm/
  models.py      scheduled_tasks、observer_messages
  migrations.py  schema version 2
tests/test_b8_scheduler.py
scripts/
  test-b8.ps1
  run-b8-api.ps1
  run-b8-scheduler.ps1
docs/
  scheduler-recovery-v1.md
  handoff-B8.md
```

## 3. 验证

```powershell
pwsh -NoProfile -File scripts/test-b8.ps1
```

专项结果：

```text
10 passed, 1 warning
```

全量结果：

```text
123 passed, 1 warning
```

唯一警告为 `Starlette/httpx` 弃用提示，不阻塞 B8。

验证覆盖 SQLite 与临时 `pgserver` PostgreSQL，不使用生产数据库和真实凭据。

## 4. 交接字段

```text
任务 ID：B8 调度、幂等与崩溃恢复
分支：codex/bx-b8-scheduler
提交哈希：476a401f003a13e66300e7a0e6d1b1a651654c13
改动文件：rpg_scheduler/、rpg_orm/、app/、tests/、scripts/、docs/、README.md
实现摘要：schema 2 持久任务队列、租约、advisory lock、超时重试、崩溃恢复和留言持久化。
测试命令：pwsh -NoProfile -File scripts/test-b8.ps1
测试结果：B8 10 项通过；全量 123 项通过
seed / mock：20261028；SQLite；临时 PostgreSQL；无真实供应商
已知风险：SQLite 不支持多实例生产并发；外部任务效果仍需在 B9 使用业务幂等键。
需要 A 合并的文件：本分支代码、测试、运维脚本和文档
需要 A 在服务器执行的动作：无；生产迁移与计划任务留到部署批次
```
