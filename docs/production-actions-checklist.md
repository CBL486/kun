# A 侧整合与生产动作清单

状态：供 A 执行；B 不操作服务器

日期：2026-11-01

## 1. 合并与冻结

1. 确认 B13 分支包含 B8～B12 所需提交；
2. 在干净 clone 运行 `scripts/test-all.ps1`；
3. 校验 `docs/release-evidence.json`、`docs/e2e-7day-summary.json`、
   `docs/b11-cost-report.json` 和资产授权；
4. 选择最终 commit，建议 tag：`v0.1.0-g2-rc1`；
5. 不把私密素材包、测试数据库或服务器环境文件加入仓库。

## 2. staging 预演

- 构建 `scripts/build-release.ps1` 发布包并运行 `verify-release.ps1`；
- 在隔离 PostgreSQL 执行 schema 4 迁移；
- 注册 API、scheduler、backup 和日志轮转任务；
- 启动 Nginx/Caddy，执行 `nginx -t` 或 `caddy validate`；
- 验证 `/health`、`/ready`、`/metrics`、室内图与 Spine；
- 执行 7 天压缩模拟和成本压力报告；
- 执行 SQLite/PostgreSQL 备份恢复演练；
- 执行 application release junction 回滚演练。

## 3. 生产发布

1. 获取发布批准和维护窗口；
2. 完成最新 PostgreSQL 备份并验证恢复；
3. 部署 release 到新的版本目录；
4. 切换 `current` junction；
5. 启动 API 和 scheduler；
6. 检查数据库 schema 4、scheduler backlog 和 API readiness；
7. 重载反向代理；
8. 启动 Prometheus 抓取和告警；
9. 执行桌面和手机 smoke test；
10. 记录 commit、manifest、备份 ID、健康结果和操作人。

## 4. 运行中检查

- `/ready` 或数据库不可用告警；
- 5xx、请求延迟和进程存活；
- scheduler 过期租约和 pending backlog；
- 最新数据库备份不超过 36 小时；
- 审核/模型降级和规则模式；
- 日志轮转、磁盘空间和代理错误；
- 无密钥或私密内容进入日志。

## 5. 回滚

- 应用回滚使用 `docs/rollback-runbook.md`；
- 数据库回滚只按已验证备份和独立 runbook 执行；
- schema 4 不自动回退为 schema 3；
- 回滚后再次执行健康检查和 7 天数据只读核验；
- 保存完整证据。

## 6. 禁止事项

- B 不登录服务器、VNC、RDP、SSH 或云控制台；
- B 不执行生产迁移、DNS、TLS、防火墙或任务注册；
- 不提交真实密钥或生产数据；
- 不在无备份时执行数据库恢复或回滚。
