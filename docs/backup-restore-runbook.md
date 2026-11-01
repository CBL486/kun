# AI World 数据库备份与恢复手册

状态：本地工具已验证；生产动作由 A 执行

日期：2026-11-01

## 1. 备份内容

`rpg_release` 为每个备份生成：

```text
数据库备份文件
同名 .json 元数据
文件大小和 SHA-256
schema 版本
关键表行数
创建时间
```

关键表覆盖世界、动作、事件、记忆、调度、留言和 LLM 成本数据。

## 2. SQLite 本地备份

```powershell
pwsh -NoProfile -File scripts/backup-database.ps1 `
  -Url "sqlite:///./out/b13/world.sqlite3" `
  -Output "out/b13/backups/world.sqlite3"
```

验证：

```powershell
python -m rpg_release verify-backup `
  --backup "out/b13/backups/world.sqlite3"
```

恢复到新路径：

```powershell
pwsh -NoProfile -File scripts/restore-database.ps1 `
  -Backup "out/b13/backups/world.sqlite3" `
  -Url "sqlite:///./out/b13/restored.sqlite3" `
  -ConfirmRestore
```

目标已存在时会先保留为 `.before-restore`，不会静默覆盖。

## 3. PostgreSQL

```powershell
pwsh -NoProfile -File scripts/backup-database.ps1 `
  -Url $env:AIWORLD_BACKUP_DATABASE_URL `
  -Output "D:\AIWorld\backups\aiworld.dump" `
  -PgBin "D:\AIWorld\runtime\PostgreSQL\bin"
```

恢复到隔离数据库：

```powershell
pwsh -NoProfile -File scripts/restore-database.ps1 `
  -Backup "D:\AIWorld\backups\aiworld.dump" `
  -Url $env:AIWORLD_RESTORE_DATABASE_URL `
  -PgBin "D:\AIWorld\runtime\PostgreSQL\bin" `
  -ConfirmRestore
```

恢复命令使用 `pg_restore --clean --if-exists --no-owner`。禁止指向生产库做演练。

## 4. 自动任务

`deploy/windows/Invoke-AIWorldBackup.ps1` 读取环境变量
`AIWORLD_BACKUP_DATABASE_URL`，备份到 `backups/`，随后执行元数据校验。

B12/B13 计划任务：

```text
03:00 AIWorld-Backup
03:30 AIWorld-LogRotation
```

日志和备份目录不进入 release 包。

## 5. 恢复验收

恢复工具自动检查：

- 备份 SHA-256；
- schema 版本；
- 关键表存在；
- 关键表行数和备份元数据一致。

A 还需检查：

- 事件、动作和记忆的来源关系；
- scheduler 无过期租约且 backlog 可控；
- 最新备份年龄小于 36 小时；
- API `/ready`；
- 只读业务查询；
- 审核和成本表没有明显缺口。

## 6. 保留策略

- 本地默认保留 14 天，生产期限由 A 和合规要求确定；
- 不删除唯一可用备份；
- 备份和恢复证据单独记录校验值；
- 恢复操作必须保存开始/结束时间、操作人、schema 版本和恢复结果。
