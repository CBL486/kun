# B13 备份恢复、发布证据与总交接

状态：本地实现完成，等待 A 复审

日期：2026-11-01

分支：`codex/bx-b13-release`

## 1. 交付范围

- SQLite 在线备份、恢复和关键行数校验；
- 本地 PostgreSQL `pg_dump/pg_restore` 备份恢复；
- 备份文件 SHA-256、schema 版本和关键表快照；
- 备份新鲜度 `/metrics` 与 36 小时告警；
- Windows 每日 `AIWorld-Backup` 任务脚本；
- SQLite/PostgreSQL 备份恢复手册；
- 最终 7 天 E2E 和成本证据；
- 资产授权、已知风险和未完成项总交接；
- release evidence、版本冻结清单和建议 tag；
- A 的生产整合、部署和回滚动作清单。

## 2. 验证结果

```text
全量测试：170 passed
B13 专项：6 passed
SQLite backup/restore：passed
PostgreSQL backup/restore：passed
7 天 E2E：passed
成本对账：bill_matches=true
release manifest：verified
```

## 3. 备份恢复

```powershell
pwsh -NoProfile -File scripts/backup-database.ps1 `
  -Url "sqlite:///./out/b13/world.sqlite3" `
  -Output "out/b13/backup.sqlite3"
pwsh -NoProfile -File scripts/restore-database.ps1 `
  -Backup "out/b13/backup.sqlite3" `
  -Url "sqlite:///./out/b13/restored.sqlite3" `
  -ConfirmRestore
```

PostgreSQL 本地测试使用 `pg_dump` 和 `pg_restore`，目标必须是隔离数据库。生产恢复只由 A
按独立维护窗口执行。

## 4. 版本冻结

建议版本：

```text
version: 0.1.0-g2-rc1
tag: v0.1.0-g2-rc1
schema: 4
seed: 20261028
```

冻结文件见 `docs/release-freeze-v1.json`。

## 5. 已知风险与未完成项

| 项目 | 状态 | 责任 |
| --- | --- | --- |
| 四名 NPC 独立行走模型 | 未完成 | B/美术 |
| Spine 正式许可证导出 | 未完成 | 项目所有者 |
| 真实 LLM/审核供应商接入 | 未完成 | A |
| 生产 PostgreSQL 迁移与恢复 | 待 A staging | A |
| Nginx/Caddy 实机语法与 TLS | 待 A staging | A |
| DNS、防火墙、证书与计划任务 | 由 A 执行 | A |
| 14 天真实运行与 G3 指标 | 未开始 | A |

## 6. 总交接字段

```text
任务 ID：B13 备份恢复、发布证据与总交接
分支：codex/bx-b13-release
提交哈希：1da065d145d594f47d5efc3fe005aa9ff04c8b1b
改动文件：rpg_release/、scripts/、deploy/、docs/、tests/、app/metrics.py、README.md
实现摘要：SQLite/PostgreSQL 备份恢复、完整性快照、备份告警、最终 E2E、release evidence、冻结与生产清单。
测试命令：pwsh -NoProfile -File scripts/test-all.ps1
测试结果：170 项通过；SQLite/PostgreSQL 恢复及 7 天 E2E 通过
seed / mock：20261028；mock provider/reviewer；临时本地数据库
已知风险：真实供应商、正式 Spine 许可证、四名 NPC 模型和生产部署仍需后续处理
需要 A 合并的文件：完整 B13 分支
需要 A 在服务器执行的动作：按 docs/production-actions-checklist.md 执行 staging、生产迁移、服务注册、监控和回滚演练
```
