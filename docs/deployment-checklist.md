# AI World 部署检查清单

状态：供 A 在 staging/生产执行；B 不执行部署

日期：2026-11-01

## 1. 发布前

- [ ] 确认目标 commit 已通过 `scripts/test-all.ps1`；
- [ ] 确认 B10 7 天 E2E 和 B11 成本矩阵通过；
- [ ] 确认工作树干净且目标提交已推送；
- [ ] 确认数据库 schema 版本为 4；
- [ ] 确认最近备份可恢复；
- [ ] 在仓库外准备环境文件并设置最小 ACL；
- [ ] 确认 `.env`、密钥、数据库文件和测试夹具不在发布包；
- [ ] 确认素材授权和署名材料有效。

## 2. 构建发布包

```powershell
pwsh -NoProfile -File scripts/build-release.ps1 `
  -Output "dist/aiworld-0.1.0-rc1" `
  -Version "0.1.0-rc1"
pwsh -NoProfile -File scripts/verify-release.ps1 `
  -Release "dist/aiworld-0.1.0-rc1"
```

发布包包含 `RELEASE_MANIFEST.json` 和 `checksums.sha256`，不得包含：

```text
.env / 密钥 / token / 证书私钥
*.db / *.sqlite / *.sqlite3
tests/
out/ / logs/ / backups/ / data/
ZIP/RAR/7z/PSD/ASEPRITE 原始素材
```

## 3. 配置代理

Nginx 主方案：

```text
deploy/reverse-proxy/nginx.conf.template
```

替换 `__DOMAIN__`、`__TLS_CERT__`、`__TLS_KEY__` 后执行 A 控制的配置检查：

```text
nginx -t
```

Caddy 备选：

```text
deploy/reverse-proxy/Caddyfile.template
```

设置 `AIWORLD_DOMAIN` 后使用 `caddy validate`。

代理必须：

- 外部拒绝 `/metrics`；
- API 保持 `127.0.0.1:8080`；
- 启用 HTTPS、安全响应头、请求 ID 和限流；
- `/assets` 与 `/static` 使用版本化缓存策略。

## 4. 注册 Windows 任务

```powershell
pwsh -NoProfile -File deploy/windows/Register-AIWorldTasks.ps1 `
  -RootPath "D:\AIWorld\current" `
  -PythonPath "D:\AIWorld\runtime\Python312\python.exe" `
  -EnvironmentFile "D:\AIWorld\config\production.env" `
  -ConfirmRegistration
```

任务：

```text
AIWorld-API
AIWorld-Scheduler
AIWorld-Backup
AIWorld-LogRotation
```

环境文件只由 A 保存，不得放进 release 目录或源码仓库。

## 5. 启动与检查

启动顺序：

1. PostgreSQL 可连接；
2. API；
3. scheduler；
4. 本地健康检查；
5. 反向代理；
6. Prometheus。

```powershell
pwsh -NoProfile -File deploy/windows/health-check.ps1 `
  -BaseUrl "http://127.0.0.1:8080" `
  -SchedulerDatabaseUrl $env:AIWORLD_SCHEDULER_DATABASE_URL
```

要求：

- `/health` 返回 ok；
- `/ready` 返回 ready；
- `/metrics` 显示 `aiworld_database_ready 1`；
- scheduler 无过期租约，积压低于阈值；
- 最新数据库备份不超过 36 小时；
- 浏览器控制台无错误。

## 6. 监控与日志

- Prometheus 配置：`deploy/monitoring/prometheus.yml`
- 告警：`deploy/monitoring/alerts.yml`
- 日志轮转：`deploy/windows/Rotate-AIWorldLogs.ps1`
- 备份任务：`deploy/windows/Invoke-AIWorldBackup.ps1`
- 默认日志保留 14 天，单文件达到 20 MB 时轮转；
- `/metrics` 仅内网访问；
- 不记录 API Key、完整 prompt 或真实用户原文。

## 7. 停止

```powershell
pwsh -NoProfile -File deploy/windows/Unregister-AIWorldTasks.ps1 `
  -ConfirmRemoval
```

生产停服由 A 执行，并保存任务状态、API/scheduler 日志、健康检查和数据库备份证据。

## 8. 回滚

按 `docs/rollback-runbook.md` 执行。数据库 schema 回滚独立于应用目录回滚，必须先确认
备份和兼容性，不允许把应用切换当作数据库回滚。

## 9. 配置 DeepSeek

1. 将 API Key 写入服务器私有文件 `C:\AIWorld\data\secrets\deepseek_api_key.txt`；
2. 运行 `scripts/write_runtime_env.py` 生成生产环境文件；
3. 执行 `python -m rpg_llm.smoke`；
4. 确认 `provider=deepseek`、`model=deepseek-flash`、`run_mode=model`；
5. 任一项不满足时，保持 `AIWORLD_LLM_PROVIDER=mock`，不得进入生产发布。
