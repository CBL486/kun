# A 侧 staging 验证记录 V1

状态：已通过隔离 staging；生产未变更

日期：2026-11-01

候选版本：`0.1.0-g2-rc1`

数据库 schema：4

seed：`20261028`

## 1. 隔离边界

本次验证只使用：

- `C:\AIWorld\staging\`；
- SQLite 端口 `18080`；
- PostgreSQL staging 端口 `18081`；
- 独立 PostgreSQL 实例端口 `55433`；
- staging 数据库 `aiworld_staging` / `aiworld_staging_restore`。

未修改：

- 生产 API `127.0.0.1:8080`；
- 生产 PostgreSQL `127.0.0.1:55432`；
- 生产计划任务 `AIWorldAPI`、`AIWorldPostgreSQL`、`AIWorldPostgresBackup`；
- 生产 `current`、生产数据和生产环境文件。

## 2. 验证结果

| 项目 | 结果 |
| --- | --- |
| 全量测试 | `179 passed` |
| 七日 E2E | `passed`，49 个事件，0 错误，1 警告 |
| 成本对账 | `bill_matches=true` |
| SQLite staging | 健康、就绪、世界、角色、指标、Web、素材、调度器通过 |
| PostgreSQL staging | schema 4、健康、就绪、指标、调度器、备份、恢复通过 |
| API 烟测 | timeline、memory、OpenAPI、室内图、Spine、留言排队与持久化通过 |
| release junction | A→B→A 切换和回滚通过 |
| 发布工具自校验 | `issues=[]` |
| DeepSeek live smoke | `succeeded`，112/81 tokens，0.00094176 CNY，审核通过 |

## 3. 本轮修复

1. 发布包现在包含 `rpg_deploy/`，服务器可直接执行发布校验和回滚脚本；
2. `server` 可选依赖补充 `psycopg[binary]`，满足 scheduler 同步 PostgreSQL 驱动；
3. release verifier 忽略运行时生成的 `__pycache__` / `.pyc`；
4. `Switch-AIWorldRelease.ps1` 通过显式 Python 引导代码加载发布包内校验器，不再依赖服务器当前目录或 `PYTHONPATH`。

## 4. 仍需完成

- 安装正式服务器依赖时必须包含 `asyncpg` 与 `psycopg[binary]`；
- Nginx/Caddy、域名、TLS、证书和公网访问策略实机验证；
- staging 计划任务注册与自动恢复演练；
- 真实审核供应商和故障切换；
- 生产前最新 PostgreSQL 备份与独立恢复窗口；
- 14 天真实运行与 G3 指标。

## 5. 结论

当前候选版本已具备进入生产发布准备的条件，但生产切换仍需单独审批、维护窗口、最新备份和代理/TLS 验证。
