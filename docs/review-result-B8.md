# B8 调度、幂等与崩溃恢复评审结果

评审人：Agent A

评审日期：2026-11-01

分支：`codex/bx-b8-scheduler`

实现提交：`476a401f003a13e66300e7a0e6d1b1a651654c13`

最终交接提交：`de451a4bb6d7351bdfd6024ef139cb51cc831290`

基线：`1b57bda627ccc4cf617acf549946b1dc3f5218c8`

## 1. 结论

复审结论：**通过，允许合并 main，允许进入 B9。**

B8 的持久任务队列、幂等入队、worker 租约、超时重试、死信、崩溃恢复、PostgreSQL advisory lock 和观察者留言持久化均已实现并验证。

## 2. 验收证据

### 2.1 测试结果

B8 专项：

```text
10 passed, 1 warning
```

B8 范围测试脚本：

```text
pwsh -NoProfile -File scripts/test-b8.ps1
49 passed, 1 warning
```

全量测试：

```text
123 passed, 1 warning
```

唯一警告为 Starlette/httpx TestClient 弃用提示，不影响 B8 功能和安全边界。

### 2.2 独立持久化验证

使用两个独立 Python 进程访问同一个 SQLite 文件：

```text
进程 1：PersistentMessageQueue.enqueue(...)
进程 2：PersistentMessageQueue.list_messages()
```

进程 2 能读取到进程 1 写入的留言，说明留言不是只存在于进程内。

### 2.3 调度 CLI

执行：

```powershell
pwsh -NoProfile -File scripts/run-b8-scheduler.ps1 `
  -Command status `
  -DatabaseUrl "sqlite:///out/b8-merged-cli.sqlite3"
```

返回：

```json
{
  "backlog": {
    "pending_due": 0,
    "delayed": 0,
    "leased": 0,
    "expired_leases": 0,
    "oldest_pending_seconds": 0.0
  },
  "tasks": []
}
```

## 3. 已确认能力

- `scheduled_tasks` 持久队列表；
- `observer_messages` 留言持久化表；
- `operation_id` 幂等入队与 payload 冲突检测；
- 任务状态：`pending`、`leased`、`succeeded`、`dead_letter`；
- worker 租约、过期回收和旧 worker 拒绝；
- 超时、指数退避重试和死信；
- PostgreSQL `pg_try_advisory_lock` / `FOR UPDATE SKIP LOCKED`；
- 进程重启后的任务恢复扫描；
- API 重启后的留言恢复；
- backlog、delayed、leased、expired lease 状态查询；
- schema version 2 与 SQLite/PostgreSQL 契约测试。

## 4. 接受的设计限制

- SQLite 锁只用于本地单进程验证，不支持多实例生产并发；
- 调度层不替代业务 handler 的幂等键，外部计费和世界写入仍由 B9/B10 保护；
- 本轮验证的是持久化状态和进程外读取，真正的 staging 强制杀进程/重启演练留给 A 的 staging/G2；
- `test-b8.ps1` 是 B4/B5/B6/B8 的范围测试入口，不是全量 123 项入口；全量验收需额外执行 `python -m pytest -q`。

这些限制已记录，不阻断 B8 合并。

## 5. 合并决定

```text
B8 复审：PASS
允许合并 codex/bx-b8-scheduler 到 main
下一批：B9 LLM 网关、审核适配器与成本核心
```

B 不操作服务器；生产迁移、计划任务和 staging 演练仍由 A 执行。