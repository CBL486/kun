# B9 修复任务单

状态：BLOCKED，等待 B 修复后复审

分支：`codex/bx-b9-llm-gateway`

当前实现提交：`e69bb9e42c69331a8e89abc195cb5bfe8c257d5f`

当前最终交接：`a2a18ad46461237839b0f987b3dda57293e93233`

## 1. 为什么不通过

B9 的 mock 测试、预算、审核、缓存、成本和脱敏都基本正确，但真实 provider 的网络异常没有进入降级链路。

当前代码：

```python
# rpg_llm/gateway.py
try:
    response = self.provider.complete(provider_request)
except ProviderError as error:
    ...
```

只捕获 `ProviderError`。但 `OpenAICompatibleProvider.complete()` 直接调用：

```python
response = self.client.post(...)
```

真实网络可能抛出：

- `httpx.ConnectError`
- `httpx.TimeoutException`
- `httpx.NetworkError`
- `httpx.HTTPError`
- 响应 JSON 解析异常
- provider 返回结构错误
- 其他 provider 运行时异常

这些异常会直接穿透 `LlmGateway.generate()`，导致主智能体循环中断。

## 2. 已复现

```text
BadProvider.complete()
  -> RuntimeError("network reset")

LlmGateway.generate()
  -> RAISED RuntimeError: network reset
```

预期：

```text
provider 失败
  -> 记录 provider_failure
  -> 熔断失败计数增加
  -> 返回规则安全模板
  -> 不创建世界事件或记忆
  -> 不向调用方抛异常
```

## 3. B 必须修改

### 3.1 在 provider 边界统一异常

文件：

```text
rpg_llm/providers.py
```

`OpenAICompatibleProvider.complete()` 至少应捕获并转换：

```python
httpx.TimeoutException
httpx.ConnectError
httpx.NetworkError
httpx.HTTPError
json.JSONDecodeError
KeyError
ValueError
```

建议：

- 网络/超时/连接错误：转换为可重试的 `ProviderError(..., transient=True)`
- HTTP 4xx 或鉴权失败：转换为不可重试的 provider 错误
- 非法的响应结构/JSON：转换为 provider 响应错误
- 保留原有 HTTP 状态判断

### 3.2 在网关增加防御性边界

文件：

```text
rpg_llm/gateway.py
```

围绕 `provider.complete()` 的异常处理必须保证任何 provider 异常都不会穿透：

- `ProviderError`：保留已有重试和熔断逻辑；
- `Exception`：记录 provider failure，增加熔断失败计数，然后走安全 fallback；
- fallback 必须经过 `_save_fallback()` 持久化；
- 不允许静默返回模型文本；
- 不允许创建世界事件或记忆。

必须确保重试耗尽后：

```text
status = fallback
run_mode = rule
degradation_reason = provider_failure 或稳定错误码
```

### 3.3 增加回归测试

文件：

```text
tests/test_b9_gateway.py
```

新增至少以下测试：

1. fake provider 抛 `RuntimeError`；
2. fake provider 抛 `httpx.ConnectError`；
3. fake provider 抛 `httpx.TimeoutException`；
4. provider 返回 malformed JSON/缺少 `choices`；
5. 断言 `generate()` 不抛异常；
6. 断言结果 `status=fallback`、`run_mode=rule`；
7. 断言熔断失败计数增加；
8. 断言没有成功 usage 记录；
9. 断言没有创建世界事件或记忆。

### 3.4 建议同时检查

- provider 重试时 `provider_request_id` 是否稳定；
- 不该因为重试响应 ID 不同而重复写入 usage；
- `budget_lock_busy` 的 fallback 是否应该缓存或明确返回稍后重试；
- 以上项目可以记录为限制，但不要引入未测试的静默行为。

## 4. 修复后的提交要求

```text
新提交哈希：
改动文件：
provider 异常处理位置：
fallback 持久化位置：
新增测试名称：
测试命令：
测试真实输出：
熔断失败计数证据：
usage 记录证据：
是否创建世界事件：
```

## 5. 复审标准

- [ ] provider 网络异常不抛出到调用方
- [ ] `status=fallback` 且 `run_mode=rule`
- [ ] 熔断失败计数正确
- [ ] fallback 被持久化
- [ ] 没有错误 usage 记录
- [ ] 没有世界事件、关系或记忆写入
- [ ] 全量测试继续通过
- [ ] 不读取真实 API Key
- [ ] 不连接生产数据库
- [ ] 不操作服务器

```text
结论：BLOCKED
暂不合并 codex/bx-b9-llm-gateway
等待 B 修复并重新提交验收
```