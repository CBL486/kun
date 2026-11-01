# B12 部署包、反向代理、监控与回滚配置交接

状态：已通过 A 复审

日期：2026-11-01

分支：`codex/bx-b12-deployment`

## 1. 实现范围

- 内部 Prometheus `/metrics`；
- Nginx 与 Caddy 反向代理模板；
- HTTPS、安全头、限流、静态资源缓存和 `/metrics` 外部阻断；
- Windows API、scheduler、日志轮转计划任务脚本；
- API 与 scheduler 本地健康检查；
- Prometheus 抓取和告警规则；
- allowlist 发布包构建、manifest、checksums 和校验器；
- application release junction 回滚脚本；
- 部署检查清单和回滚手册。

B12 不执行服务器注册、TLS、代理重载、数据库迁移或生产发布。

## 2. 代码结构

```text
app/metrics.py
deploy/
  reverse-proxy/
  monitoring/
  windows/
rpg_deploy/
  release.py
  __main__.py
scripts/
  build-release.ps1
  verify-release.ps1
  rollback-release.ps1
  test-b12.ps1
docs/
  deployment-topology-v1.md
  deployment-checklist.md
  rollback-runbook.md
```

## 3. 发布包

构建：

```powershell
pwsh -NoProfile -File scripts/build-release.ps1 `
  -Output "out/b12/aiworld-0.1.0-rc1" `
  -Version "0.1.0-rc1" `
  -BuiltAt "2026-11-01T00:00:00Z"
```

验证：

```powershell
pwsh -NoProfile -File scripts/verify-release.ps1 `
  -Release "out/b12/aiworld-0.1.0-rc1"
```

本地实测：

```text
release files: 166
schema version: 4
manifest verification: issues=[]
package_sha256: present
sensitive-file exclusion: passed
```

发布包明确排除：

- `.env` 和所有环境密钥；
- SQLite/PostgreSQL 测试数据库；
- `tests/`、`out/`、日志、备份和缓存；
- ZIP/RAR/7z/PSD/ASEPRITE 原始素材；
- 证书私钥和 PEM/KEY/P12 文件。

## 4. 监控与代理

- `/metrics` 提供 liveness、database ready、HTTP 计数、5xx、请求时长和 scheduler backlog；
- Nginx 模板提供 `limit_req`、HTTPS、安全头和静态缓存；
- Caddy 模板提供自动 HTTPS、安全头和静态缓存；
- 两个代理模板都阻止外部访问 `/metrics`；
- Prometheus 告警覆盖实例离线、数据库未就绪、5xx、过期租约和 backlog。

## 5. 验证结果

```text
B12 专项：7 passed
全量测试：164 passed
配置静态检查：passed
PowerShell 语法检查：passed
```

唯一警告为 Starlette/httpx TestClient 弃用提示。

本机没有安装 Nginx/Caddy 可执行文件，因此使用静态模板检查；A 在 staging 使用
`nginx -t` 或 `caddy validate` 做最终语法验证。

## 6. 已知限制

- 计划任务注册和 release junction 切换只作为脚本交付，未在本机执行；
- 生产环境文件、证书、DNS、TLS、防火墙和数据库权限由 A 管理；
- Prometheus/Grafana 服务未在本机安装；
- 数据库 schema 回滚不属于应用 release 回滚，必须按 B13 备份恢复流程执行。

## 7. 交接字段

```text
任务 ID：B12 部署包、反向代理、监控与回滚配置
分支：codex/bx-b12-deployment
提交哈希：9e54c22881932690e46883d4adb16b847bb6eb6d
改动文件：app/、rpg_deploy/、deploy/、scripts/、tests/、docs/、README.md
实现摘要：allowlist 发布包、checksums、Windows 任务、代理/监控模板、健康检查和 release 回滚。
测试命令：pwsh -NoProfile -File scripts/test-b12.ps1
测试结果：B12 7 项通过；全量 164 项通过
seed / mock：20261028；本地临时 release；无生产密钥
已知风险：Nginx/Caddy 实际语法、TLS、计划任务和权限需 A 在 staging 验证。
需要 A 合并的文件：本分支部署代码、模板、测试、脚本和文档
需要 A 在服务器执行的动作：
  - 安装/校验反向代理配置；
  - 配置外部环境文件与任务账号；
  - 注册任务、启动服务并执行健康检查；
  - staging 验证后决定生产发布或回滚。
```
