# AI World 回滚手册

状态：供 A 在生产环境执行；B 不执行

日期：2026-11-01

## 1. 触发条件

满足任一条件时停止继续发布并评估回滚：

- `/health` 或 `/ready` 连续失败；
- 5xx 比例持续超阈值；
- schema 与运行版本不兼容；
- 数据完整性或授权检查失败；
- scheduler 积压、过期租约持续增长；
- 审核失败导致公开内容异常；
- 安全、密钥或真实用户数据泄漏。

## 2. 先保护证据

1. 停止外部流量或切到维护页；
2. 导出当前发布 manifest、commit 和 schema 版本；
3. 保存 API、scheduler、代理和数据库健康输出；
4. 记录失败时间和操作人；
5. 确认最近数据库备份及其校验值。

## 3. 应用回滚

目标 release 必须先通过：

```powershell
pwsh -NoProfile -File scripts/verify-release.ps1 `
  -Release "C:\AIWorld\releases\<previous>"
```

然后由 A 执行：

```powershell
pwsh -NoProfile -File scripts/rollback-release.ps1 `
  -TargetRelease "C:\AIWorld\releases\<previous>" `
  -CurrentLink "C:\AIWorld\current" `
  -PythonPath "C:\AIWorld\runtime\Python312\python.exe" `
  -ManageTasks `
  -ConfirmRollback
```

该脚本会：

1. 验证目标 release 所有文件哈希；
2. 停止 API 和 scheduler；
3. 通过 junction 切换 `current`；
4. 重新启动任务；
5. 失败时恢复上一 junction。

## 4. 数据库回滚

应用回滚不等于数据库回滚。

- 如果新 schema 向后兼容：保留数据库，仅回滚应用；
- 如果不兼容：先停止所有写入，按 PostgreSQL 迁移/备份手册恢复；
- 不在未验证备份时执行 `rollback`；
- 恢复后运行 schema version、关键行数、外键和索引检查；
- 数据库动作仅由 A 执行。

## 5. 回滚后验证

```powershell
pwsh -NoProfile -File deploy/windows/health-check.ps1 `
  -BaseUrl "http://127.0.0.1:8080"
```

再检查：

- `/health`、`/ready`；
- `/world`、`/agent`、`/timeline`；
- `/chat` 只进入队列，不直接写世界；
- scheduler status；
- Prometheus target；
- 代理 TLS、限流、`/metrics` 外部拒绝；
- 首页、室内图、Spine `idle/walk`；
- 日志没有密钥或私密内容。

## 6. 证据

保存：

```text
原版本 commit / manifest
回滚目标 manifest
数据库备份 ID / 校验值
schema version
健康检查输出
任务状态
代理状态
回滚操作起止时间
```

## 7. 禁止事项

- 不用数据库回滚替代应用配置修复；
- 不在未停止写入时恢复数据库；
- 不删除唯一可用备份；
- 不把生产环境文件或密钥复制回仓库；
- 不由 B 执行生产回滚。
