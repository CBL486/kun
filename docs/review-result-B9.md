# B9 LLM 网关、审核与成本核心评审结果

评审人：Agent A

评审日期：2026-11-01

分支：`codex/bx-b9-llm-gateway`

实现提交：`e69bb9e42c69331a8e89abc195cb5bfe8c257d5f`

最终交接提交：`a2a18ad46461237839b0f987b3dda57293e93233`

A 侧当前 main 基线：`4e5cfdaa8f4f75c826de30fe9094c03e97374794`

## 1. 结论

复审结论：**不通过，暂不合并 main，等待 B 修复后复审。**

B9 的 mock、预算、审核、缓存、成本账本、熔断和提示词脱敏大部分实现正确，测试也能通过；但真实 provider 的非 `ProviderError` 网络异常会直接穿透网关，违反“供应商失败不阻断世界”的 B9 契约。

## 2. 测试证据

B9 专项：

```text
11 passed
```

累计专项入口：

```text
30 passed
```

全量测试：

```text
134 passed, 1 warning
```

成本审计 CLI：

```json
{
  "budget_date": "2026-11-01",
  "usage": {
    "calls": 0,
    "review_calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cost_cny": "0"
  },
  "records": []
}
```

测试通过说明现有覆盖项正确，但不能覆盖下面这个真实网络异常路径。

## 3. 阻断问题

### P0：provider 网络异常会直接抛到调用方

`LlmGateway._execute()` 只捕获 `ProviderError`：

```python
try:
    response = self.provider.complete(provider_request)
except ProviderError as error:
    ...
```

`OpenAICompatibleProvider.complete()` 直接调用 `httpx.Client.post()`，没有把 `httpx.ConnectError`、`httpx.TimeoutException`、连接重置和其他运行时异常转换为 `ProviderError`。

独立复现：

```text
BadProvider.complete() -> RuntimeError("network reset")
LlmGateway.generate()  -> RAISED RuntimeError: network reset
```

预期行为：

```text
RuntimeError / httpx connectivity error
  -> 记录 provider_failure
  -> 触发熔断失败计数
  -> 返回规则安全模板
  -> 不抛出到世界循环
```

当前行为会让一次供应商网络波动直接打断主智能体执行，违反 B9 的失败关闭和降级要求。

## 4. 已确认通过的部分

- 无密钥 mock provider 可离线运行；
- `operation_id` 重放与内容冲突检测；
- 输入、输出、调用次数、审核调用和成本硬上限；
- 审核拒绝/不可用时返回安全模板；
- 传输层重试不重复写 usage；
- 结构化世界写入字段被拒绝；
- 熔断阈值和冷却恢复；
- 提示词版本化和敏感信息脱敏；
- 并发调用预算限制；
- 真实 provider 缺少 API Key 时失败关闭；
- SQLite/PostgreSQL schema version 3 契约测试通过。

## 5. B 需要完成的修复

### 必须修复

1. 在 `OpenAICompatibleProvider.complete()` 或网关边界统一捕获 provider 的所有可恢复异常：
   - `httpx.TimeoutException`
   - `httpx.ConnectError`
   - `httpx.NetworkError`
   - 响应 JSON 解析失败
   - provider 返回结构异常

2. 网关捕获 provider 的通用 `Exception` 时仍要：
   - 增加熔断失败计数；
   - 记录 `provider_failure` 或稳定错误码；
   - 返回规则安全模板；
   - 不创建世界事件或记忆；
   - 不让异常穿透 `generate()`。

3. 新增回归测试：
   - fake provider 抛 `RuntimeError`；
   - fake provider 抛 `httpx.ConnectError`；
   - malformed response；
   - 断言 `generate()` 返回 `status=fallback`；
   - 断言调用方不会收到异常；
   - 断言熔断计数增加、没有成功 usage 记录。

### 建议修复

- 为 provider 的重试响应 ID 增加稳定性校验，避免供应商在每次传输重试中返回不同 ID 导致重复计费；
- 为 `budget_lock_busy` 增加缓存或明确返回“稍后重试”的语义，避免同一 operation 在锁竞争时出现不同最终结果。

## 6. 复审门槛

修复后必须提供：

```text
新提交哈希：
改动文件：
测试命令：
真实输出：
provider 异常类型：
降级结果：
熔断计数：
usage 记录：
是否创建世界事件：
```

复审判定标准：

- [ ] provider 网络异常不会抛出到调用方
- [ ] 熔断失败计数正确
- [ ] fallback 使用安全模板
- [ ] provider 异常不创建世界事件或记忆
- [ ] 重试不重复计费
- [ ] 全量测试继续通过
- [ ] 不读取真实 API Key、不连接生产数据库

## 7. 当前处理

```text
B9 复审：BLOCKED
暂不合并 codex/bx-b9-llm-gateway 到 main
下一状态：等待 B 修复网络异常降级路径
```