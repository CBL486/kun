# B12 部署包、反向代理、监控与回滚配置评审结果

评审人：Agent A

评审日期：2026-11-01

分支：`codex/bx-b12-deployment`

实现提交：`9e54c22881932690e46883d4adb16b847bb6eb6d`

最终交接提交：`3643d833da5fa2d1ea20dd31d7e6599c1fe4ff20`

## 1. 结论

复审结论：**通过，允许合并 main，允许进入 B13。**

B12 已提供发布包构建与校验、反向代理模板、监控指标和告警、Windows 任务脚本、健康检查和应用 release 回滚流程。未发现生产密钥、测试数据库或未授权素材进入发布包。

## 2. 验证结果

```text
全量测试：164 passed, 1 warning
B12 专项：7 passed
发布包构建：passed
发布包校验：issues=[]
配置静态检查：passed
```

发布包实测：

```text
release files: 166
schema version: 4
package_sha256: present
sensitive-file exclusion: passed
```

唯一警告为 Starlette/httpx TestClient 弃用提示，不影响 B12。

## 3. 已确认通过

- allowlist 发布包和确定性 manifest；
- SHA-256 校验及篡改检测；
- `.env`、数据库、密钥、日志、备份、测试目录和原始素材包排除；
- `RELEASE_MANIFEST.json` 与 `checksums.sha256`；
- API `/metrics` 运营指标；
- Prometheus 抓取和告警规则；
- Nginx/Caddy 模板中的 HTTPS、安全头和 `/metrics` 外部阻断；
- API、scheduler、日志轮转和健康检查脚本；
- application release junction 切换及失败恢复；
- 部署检查清单和回滚手册；
- 回滚不把数据库回滚伪装成应用回滚。

## 4. 接受限制

- 本机没有 Nginx/Caddy 可执行文件，只做静态模板检查；A 必须在 staging 执行 `nginx -t` 或 `caddy validate`；
- Windows 计划任务注册和 release junction 切换未在测试机执行；
- Prometheus/Grafana 服务和真实 TLS 证书由 A 在 staging/生产配置；
- 数据库 schema 回滚仍属于 B13/备份恢复流程，不由应用 release 回滚替代。

## 5. 合并决定

```text
B12 复审：PASS
允许合并 codex/bx-b12-deployment 到 main
下一批：B13 本地备份恢复、发布证据与总交接
```

生产部署、DNS、TLS、防火墙和计划任务仍由 A 执行，B 不操作服务器。