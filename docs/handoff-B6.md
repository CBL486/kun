# B6 本地 FastAPI 与 OpenAPI 交接

状态：本地实现完成，等待 A 验收

批次：B6

日期：2026-10-28

分支：`codex/bx-b6-fastapi-api`

## 1. 实现范围

B6 提供：

- 本地 FastAPI 应用；
- `/health`、`/ready`；
- `/world`、`/agent`、`/timeline`、`/chat`、`/memory`；
- OpenAPI 3.1 和静态 `docs/openapi-v1.json`；
- Pydantic 请求/响应模型；
- 稳定错误信封和 request ID；
- 公开字段白名单；
- mock LLM 观察者回复和 mock 审核；
- 数据库 ready/unready 注入测试；
- B7 所需字段冻结文档。

B6 不连接生产 API、生产数据库、真实模型或真实用户数据。

## 2. 数据来源

API 使用冻结 `seed=20261028` 的本地七日场景：

- 世界和角色来自 B1 快照；
- 时间线来自已提交公开事件与分享；
- 记忆摘要来自安全作用域；
- 日记只暴露安全摘要；
- 留言只排队，不直接改变世界。

## 3. 代码结构

```text
app/
  api_models.py   Pydantic 公开响应与错误模型
  local_state.py  本地世界、公开投影和留言队列
  main.py         FastAPI 应用、路由、错误处理器
  db.py           数据库 ready 探针
  settings.py     本地设置
tests/
  test_b6_api.py
  test_health.py
  test_ready.py
docs/
  openapi-projection.md
  openapi-v1.json
scripts/
  run-b6-api.ps1
  test-b6.ps1
  export-openapi.ps1
```

## 4. 启动与导出

安装本地依赖：

```powershell
python -m pip install --target .b6-deps -r requirements-b6-dev.txt
```

启动：

```powershell
pwsh -NoProfile -File scripts/run-b6-api.ps1
```

重新导出静态 OpenAPI：

```powershell
pwsh -NoProfile -File scripts/export-openapi.ps1
```

测试：

```powershell
pwsh -NoProfile -File scripts/test-b6.ps1
```

## 5. 验收结果

当前结果：

```text
B1-B5：75 项通过
B6 API、health、ready：17 项通过
合计：92 项通过
```

实际验证：

- `/health` 在数据库不可用时仍为 200；
- `/ready` 数据库不可用返回 `503 database_unavailable`；
- 七个端点均进入 OpenAPI；
- 公开响应不包含 tick、prompt、action、score、state、私有记忆和数据库信息；
- 时间线分页稳定且仅含公开事件/分享；
- 留言不能创建世界事件；
- 审核失败不返回原留言；
- 静态 OpenAPI 与运行时一致；
- 相同 seed 的本地世界投影一致。

## 6. 已知限制

- B6 使用本地冻结世界数据，不包含真实数据库写入；
- 留言队列仅在进程内，持久化留给 B8；
- 回复和审核是 mock，真实供应商留给 B9；
- B6 不提供 Web 页面和正式美术；
- FastAPI TestClient 当前对 httpx 发出上游弃用警告，不影响端点测试；
- 未执行服务器、反向代理、DNS、TLS 或生产部署操作。

## 7. 交接字段

```text
任务 ID：B6 本地 FastAPI 与 OpenAPI
分支：codex/bx-b6-fastapi-api
提交哈希：cf313b1
改动文件：app/api_models.py、app/local_state.py、app/main.py、tests/test_b6_api.py、tests/test_health.py、tests/test_ready.py、scripts/test-b6.ps1、scripts/run-b6-api.ps1、scripts/export-openapi.ps1、scripts/export_openapi.py、requirements-b6.txt、requirements-b6-dev.txt、docs/openapi-projection.md、docs/openapi-v1.json、README.md、docs/handoff-B6.md
测试命令：pwsh -NoProfile -File scripts/test-b6.ps1
测试结果：B1-B5 75 项、B6 17 项，合计 92 项通过
seed / mock：20261028；rule_only；mock LLM；mock 审核
素材许可证：B6 未引入正式美术素材
已知风险：留言队列和业务 API 的持久化接线由 B8/后续集成完善；真实模型由 B9 接入
需要 A 合并的文件：本分支 B6 文件和 OpenAPI/投影契约
需要 A 在服务器执行的动作：无；B6 仅本地交付
```
