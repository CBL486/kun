# B11 安全、失败与成本压力测试交接

状态：已通过 A 复审

日期：2026-11-01

分支：`codex/bx-b11-stress`

## 1. 实现范围

- 正常日、异常日、长对话、连续重试和并发成本模型；
- 每个场景独立的每日硬预算；
- 按日期、事件、角色和接口聚合成本；
- mock bill 与成本报告对账；
- 滑动窗口限流；
- 人工确认门禁；
- 任务积压、并发领取和租约恢复验证；
- 数据库、模型、审核、网络、队列和预算失败矩阵。

B11 不连接生产数据库、真实模型、审核供应商或真实用户数据。

## 2. 代码结构

```text
rpg_stress/
  cost_model.py         最坏成本矩阵与聚合账单
  rate_limit.py         线程安全滑动窗口限流
  manual_confirmation.py 高风险动作人工确认
  __main__.py           成本矩阵 CLI
tests/test_b11_stress.py
scripts/test-b11.ps1
scripts/run-b11-stress.ps1
scripts/test-all.ps1
docs/security-failure-matrix-v1.md
docs/b11-cost-report.json
```

## 3. 验证结果

```text
157 passed, 1 warning
B11 专项 6 passed
七日 E2E: passed
成本对账: bill_matches=true
```

唯一警告为 Starlette/httpx TestClient 弃用提示。

成本矩阵独立日结果：

```text
正常日      0.04800000 CNY
异常日      0.07040000 CNY
长对话      0.09440000 CNY
连续重试    0.08640000 CNY
并发突发    0.06400000 CNY
```

所有独立日都不超过 `0.10 CNY`。报告与 mock bill 总额一致。

## 4. 安全与失败验证

- 达到预算硬上限后不再调用 provider；
- 模型、审核和数据库失败不产生半条事件；
- 审核不可用只返回安全模板，不泄漏原始内容；
- 滑动窗口在并发下不超过限额；
- pending/rejected 人工确认不能执行高风险回调；
- 任务积压可观察，租约过期可回收；
- 成本报告支持日期、事件、角色和接口聚合；
- 不读取密钥、生产数据库或真实用户数据。

同时修正 B10 文档中的角色名称：重复台词警告属于顾言 `npc_gu`。

## 5. 已知限制

- 真实供应商价格、幂等能力和审核 SLA 未在本地确认；
- 限流器为单进程内存实现，生产跨实例限流需在 B12 网关/反向代理层配置；
- 人工确认门禁暂未接入正式管理 UI；
- SQLite 不适合作多实例生产并发；
- B11 不执行服务器、TLS、网络或部署操作。

## 6. 交接字段

```text
任务 ID：B11 安全、失败与成本压力测试
分支：codex/bx-b11-stress
提交哈希：983d17ca0d13006d9b01f2153104431776f0d792
改动文件：rpg_stress/、rpg_llm/、rpg_orm/、tests/、scripts/、docs/、README.md
实现摘要：五类成本压力场景、成本归因、mock 对账、滑动限流、人工确认和失败矩阵。
测试命令：pwsh -NoProfile -File scripts/test-all.ps1
测试结果：157 项通过；B11 专项 6 项通过；7 天 E2E passed
seed / mock：20261028；mock provider/reviewer；临时数据库
已知风险：真实价格和供应商幂等需 staging 确认；跨实例限流待 B12。
需要 A 合并的文件：本分支压力层、归因账本、测试、脚本和文档
需要 A 在服务器执行的动作：无
```
