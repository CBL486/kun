# B5 评审结果

评审人：Agent A

评审日期：2026-10-28

结论：**通过，允许进入 B6**

## 1. 审查基线

- B5 实现分支：`codex/bx-b5-postgres-contract`
- B5 实现提交：`9983e0f`
- 交接回填提交：`c40ad0e`
- A 整合分支：`codex/g2-b5-integration`

## 2. 验收证据

```text
B1-B4 unittest：66 项通过
B5 unittest：9 项通过
B1-B5 合计：75 项通过
```

实际验证了：

- SQLite 临时数据库迁移和回滚；
- 临时 PostgreSQL 迁移和回滚；
- JSONB、时区、空值、枚举、索引和约束差异；
- 同一夹具在 SQLite 与 PostgreSQL 上产生相同业务摘要哈希：

```text
7dd8a4b34eb72b64c2766165ca7e589238f0fc4b6516886522f8cfb162a81f74
```

- PostgreSQL 上的 operation 重放；
- PostgreSQL 上的投影失败和核对恢复。

首次运行时，B5 测试环境未安装 `.b5-deps`，导致 `sqlalchemy` 导入失败；按依赖文件安装到 `.b5-deps` 后，75 项测试全部通过。A 已把交接和 README 中的安装命令修正为：

```powershell
python -m pip install --target .b5-deps -r requirements-b5-dev.txt
```

## 3. 已确认通过

- SQLAlchemy 2 声明式模型可用。
- SQLite 与 PostgreSQL 表名、字段和约束映射一致。
- PostgreSQL 使用 JSONB 和时区感知时间。
- 迁移和回滚可重复执行。
- 同一业务夹具双后端结果一致。
- operation 重放幂等。
- 投影失败可保留并核对恢复。
- 未连接生产数据库或生产账号。

## 4. 接受的有意限制

- 当前 schema 版本为 1，后续只能追加编号迁移。
- `drop_all` 回滚只适用于首版和隔离测试。
- 临时 `pgserver` 不等同于生产权限、网络、锁等待和参数配置。
- 生产迁移和恢复必须由 A 在维护窗口执行。
- B5 尚未实现 API、调度器或部署。

## 5. 流程问题

B5 实现基于 B4 分支而不是 A 的最新 `main`。A 已将 B5 文件单独 graft 到当前 B4 主线上，没有覆盖服务器安全配置和既有 B1-B4 集成文件。

B6 开始前必须：

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/bx-b6-fastapi-api
```

## 6. 允许的下一批

允许 B 开始 **B6 本地 FastAPI 与 OpenAPI**。

B6 继续遵守：

- 不登录服务器；
- 不连接生产 PostgreSQL；
- 使用 mock LLM、mock 审核器和本地测试数据库；
- `/health`、`/ready`、`/world`、`/agent`、`/timeline`、`/chat`、`/memory` 必须有稳定 schema、错误码和脱敏投影；
- 完成后提交独立分支和交接记录，等待 A 评审。
