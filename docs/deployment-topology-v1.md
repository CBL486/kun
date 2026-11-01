# B12 本地部署拓扑

状态：配置模板，A 负责执行

日期：2026-11-01

## 1. 组件

```text
internet
  -> Nginx/Caddy
  -> FastAPI 127.0.0.1:8080
       -> PostgreSQL
       -> scheduler worker
       -> local web/assets

Prometheus -> 127.0.0.1:8080/metrics
```

## 2. 启动顺序

1. 验证发布包 `RELEASE_MANIFEST.json` 和所有文件 SHA-256；
2. 确认外部环境文件权限和数据库连接；
3. 检查数据库 `/ready` 前的 schema 版本为 4；
4. 启动 API；
5. 启动 scheduler worker；
6. 通过本地健康检查；
7. 启动或重载反向代理；
8. 启动 Prometheus 抓取。

停止顺序反向执行：停止外部流量 → 停止 scheduler → 停止 API → 保留日志和备份证据。

## 3. 网络暴露

- API 仅监听 `127.0.0.1:8080`；
- 公网只开放反向代理的 443；
- 80 仅重定向 HTTPS；
- `/metrics` 不允许公网访问；
- Prometheus 直接抓取 `127.0.0.1:8080/metrics`；
- 数据库不暴露公网。

## 4. 静态资源

- `/assets/`：`Cache-Control: public, max-age=604800, immutable`；
- `/static/`：`public, max-age=604800`；
- HTML 不绑定长期缓存；
- 发布切换通过 `current` junction，缓存失效依赖版本目录切换或代理缓存清理；
- 原始素材压缩包不进入发布包。

## 5. 本地验证

```powershell
pwsh -NoProfile -File scripts/test-b12.ps1
```

验证不启动生产任务、不修改 DNS/TLS，只构建临时 release 并检查 manifest、敏感文件、
代理模板、监控指标和启动前置条件。
