# B9 LLM 网关、审核与成本核心交接

状态：复审阻断项已修复，等待 A 复审

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
B9 20 passed, 1 warning
累计专项入口 39 passed, 1 warning
全量 143 passed, 1 warning
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
- RuntimeError、ConnectError、TimeoutException 不会穿透 generate；
- malformed JSON 与缺少 choices 转换为 provider_invalid_response；
- HTTP 4xx 不重试；
- 重试响应 ID 不同也只记一笔 usage；
- 预算锁短暂占用不会让同 operation 返回无法解释的不同结果。

## 4. 复审修复

- `OpenAICompatibleProvider` 将网络、超时、连接、HTTP 和响应解析异常统一转换为
  `ProviderError`；
- 网络/超时/5xx 标记可重试，4xx、鉴权错误和非法响应标记不可重试；
- gateway 捕获通用 provider 异常，增加熔断计数并持久化安全模板；
- usage 主键改为逻辑 `operation_id`，防止重试响应 ID 变化导致重复计费；
- budget lock 由立即降级改为有限等待，避免同一 operation 出现非确定结果；
- 新增 provider、JSON、HTTP 4xx、重试 ID 和锁占用回归测试。

## 5. 交接字段

```text
任务 ID：B9 LLM 网关、审核与成本核心
分支：codex/bx-b9-llm-gateway
提交哈希：b9bf10ee2af62cfc5ddb992e1403b2ad6795d1d2
改动文件：rpg_llm/、rpg_orm/、tests/、scripts/、docs/、README.md
实现摘要：provider-neutral 网关、审核失败关闭、预算硬熔断、重试去重计费、规则降级和脱敏审计。
测试命令：pwsh -NoProfile -File scripts/test-b9.ps1
测试结果：B9 20 项通过；累计专项入口 39 项通过；全量 143 项通过
seed / mock：20261028；mock provider；mock reviewer；无真实密钥
已知风险：真实供应商幂等能力、审核协议、价格和超时需 A 在 staging 确认。
需要 A 合并的文件：本分支代码、测试、审计脚本和文档
需要 A 在服务器执行的动作：无；真实供应商配置留到 staging
```
