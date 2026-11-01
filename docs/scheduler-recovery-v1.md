# B8 调度、幂等与崩溃恢复

状态：本地实现完成，等待 A 复审

日期：2026-11-01

适用 schema：`rpg_orm` version 2

## 1. 调度模型

B8 使用确定性的持久任务队列，等价于 APScheduler 的触发器与执行器封装：

- 任务按 `available_at`、优先级和稳定任务 ID 排序；
- worker 从数据库领取任务，不依赖进程内队列；
- 单个任务执行受超时限制；
- 进程退出后，未完成任务仍保存在数据库；
- 同一 `operation_id` 只能对应一个任务和一份任务指纹。

任务状态：

```text
pending -> leased -> succeeded
                   -> pending（可重试失败或租约过期）
                   -> dead_letter（重试次数耗尽）
```

## 2. 幂等规则

`operation_id` 是业务幂等键：

- 相同任务再次入队返回原任务，标记 `replayed=true`；
- 相同 `operation_id`、不同 payload 或执行参数返回 `duplicate_operation`；
- worker 成功提交后任务进入 `succeeded`，再次轮询不会执行 handler；
- 世界事件仍由 B4/B5 的 `commit_step` 唯一约束和 operation 指纹二次保护。

专项测试使用真实 `OrmRepository.commit_step` 验证同一任务只产生一条动作和一条正式事件。

## 3. 租约与多进程互斥

任务领取时写入：

```text
lease_owner
lease_expires_at
attempts += 1
```

只有当前 `worker_id` 且租约未过期的进程可以标记成功或失败。旧 worker 在租约失效后
提交会得到 `lease_lost`，不能覆盖新 worker 的结果。

数据库后端：

- PostgreSQL 使用 `pg_try_advisory_lock(namespace, key)`，namespace 固定为 `1834`；
- SQLite 使用进程内非阻塞锁，仅用于本地单进程验证；
- SQLite 不声明支持多实例生产并发。

任务领取和同 operation 入队都经过 advisory lock；PostgreSQL 行锁使用
`SELECT ... FOR UPDATE SKIP LOCKED` 避免多个 worker 领取同一任务。

## 4. 超时、重试与死信

- handler 在独立线程中执行；
- 超过 `timeout_seconds` 后任务进入失败路径，不标记成功；
- 默认指数退避：`1s, 2s, 4s ...`，最大 `60s`；
- `attempts >= max_attempts` 时进入 `dead_letter`；
- 缺失 handler 同样进入失败路径；
- 超时线程可能继续运行，但租约和条件更新保证它不能提交任务成功状态。

生产接入时，handler 内的外部计费和世界写入仍必须使用各自的幂等键；调度层不能替代
B9 的计费幂等。

## 5. 崩溃恢复

进程退出后运行恢复扫描：

```powershell
pwsh -NoProfile -File scripts/run-b8-scheduler.ps1 `
  -Command recover `
  -DatabaseUrl "sqlite:///./data/b8.sqlite3"
```

扫描规则：

- 只处理 `status=leased AND lease_expires_at <= now`；
- 剩余尝试次数大于 0：清除 lease，恢复为 `pending`；
- 尝试次数耗尽：转为 `dead_letter`；
- 已成功任务和已提交世界事件不重建、不重放。

状态检查：

```powershell
pwsh -NoProfile -File scripts/run-b8-scheduler.ps1 `
  -Command status `
  -DatabaseUrl "sqlite:///./data/b8.sqlite3"
```

输出包含：

```text
pending_due
delayed
leased
expired_leases
oldest_pending_seconds
```

## 6. 留言持久化

观察者留言写入 `observer_messages`：

```text
message_id  主键
content
status
created_at
updated_at
```

API 启动脚本可把留言库设为本地 SQLite 或隔离 PostgreSQL：

```powershell
pwsh -NoProfile -File scripts/run-b8-api.ps1 `
  -DatabaseUrl "sqlite:///./data/b8.sqlite3"
```

API 与调度任务共用同一 schema，但留言不会直接创建世界事件。

## 7. 本地验证

```powershell
pwsh -NoProfile -File scripts/test-b8.ps1
```

覆盖：

- schema 2 新增表；
- operation 重复入队与内容冲突；
- 真实世界事件只提交一次；
- 租约占用、过期回收和旧 worker 拒绝；
- 超时、退避重试、死信；
- 积压和过期租约计数；
- API 重启后的留言恢复；
- PostgreSQL advisory lock 互斥。

## 8. 生产边界

- B8 只在本地 SQLite 和 `pgserver` 临时 PostgreSQL 上验证；
- 不连接生产数据库、不修改服务器计划任务；
- 生产迁移、系统计划任务、日志轮转和监控由 A 按后续部署批次执行；
- 生产关停/重启前应先停止新任务领取，再等待租约自然过期或执行恢复扫描。
