# B9 LLM 网关、审核与成本核心交接

状态：本地实现完成，等待 A 复审

日期：2026-11-01

分支：`codex/bx-b9-llm-gateway`

## 1. 实现范围

- provider-agnostic LLM 接口；
- 离线 mock provider；
- OpenAI-compatible 真实 provider 适配骨架；
- mock 与远程审核适配器；
- 持久 operation 缓存和 usage 账本；
- 输入/输出/审核/成本硬上限；
- 传输重试与新尝试独立标识；
- 熔断、规则降级和安全模板；
- 版本化提示词和脱敏审计；
- 并发调用预算验证；
- 成本审计 CLI。

B9 不调用真实供应商，不读取真实 API Key，不连接生产数据库。

## 2. 代码结构

```text
rpg_llm/
  models.py      请求、响应、审核和审计模型
  providers.py   mock / OpenAI-compatible provider
  review.py      审核适配器
  pricing.py     价格版本和硬预算
  prompts.py     提示词版本与脱敏
  circuit.py     熔断器
  fallback.py    规则模式安全模板
  repository.py  operation 缓存和 usage 去重
  gateway.py     完整调用链
  __main__.py    成本审计 CLI
rpg_orm/
  models.py      llm_operations、llm_usage
  migrations.py  schema version 3
tests/test_b9_gateway.py
scripts/test-b9.ps1
scripts/run-b9-audit.ps1
docs/llm-gateway-v1.md
docs/llm-audit-example.json
```

## 3. 验证

```powershell
pwsh -NoProfile -File scripts/test-b9.ps1
```

专项结果：

```text
B9 11 passed
累计专项入口 30 passed
全量 134 passed
```

测试覆盖：

- 无密钥 mock 运行；
- operation 重放和内容冲突；
- 预算硬上限预检；
- 审核拒绝和不可用；
- 传输重试只计费一次；
- 非法结构化写入字段拒绝；
- 熔断打开和冷却恢复；
- 提示词脱敏；
- 并发调用预算；
- 真实 provider 缺少密钥时失败关闭。

## 4. 交接字段

```text
任务 ID：B9 LLM 网关、审核与成本核心
分支：codex/bx-b9-llm-gateway
提交哈希：e69bb9e42c69331a8e89abc195cb5bfe8c257d5f
改动文件：rpg_llm/、rpg_orm/、tests/、scripts/、docs/、README.md
实现摘要：provider-neutral 网关、审核失败关闭、预算硬熔断、重试去重计费、规则降级和脱敏审计。
测试命令：pwsh -NoProfile -File scripts/test-b9.ps1
测试结果：B9 11 项通过；累计专项入口 30 项通过；全量 134 项通过
seed / mock：20261028；mock provider；mock reviewer；无真实密钥
已知风险：真实供应商幂等能力、审核协议、价格和超时需 A 在 staging 确认。
需要 A 合并的文件：本分支代码、测试、审计脚本和文档
需要 A 在服务器执行的动作：无；真实供应商配置留到 staging
```
