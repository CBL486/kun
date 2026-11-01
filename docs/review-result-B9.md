# B9 LLM 网关、审核与成本核心复审结果

评审人：Agent A

初评日期：2026-11-01

复审日期：2026-11-01

分支：`codex/bx-b9-llm-gateway`

原阻断提交：`a2a18ad46461237839b0f987b3dda57293e93233`

修复提交：`b9bf10ee2af62cfc5ddb992e1403b2ad6795d1d2`

最终交接提交：`338cbaa4caf32519149cf10ff613c5b672b9040f`

## 1. 结论

复审结论：**通过，允许合并 main，允许进入 B10。**

上次指出的 provider 网络异常穿透问题已修复。provider 的 `RuntimeError`、`httpx.ConnectError`、`httpx.TimeoutException`、malformed response 和 HTTP 4xx 路径均已覆盖测试；异常会转换为稳定错误并返回安全规则模板。

## 2. 修复验证

### 2.1 独立复现

使用抛 `RuntimeError("network reset")` 的 fake provider 复测：

```text
status=fallback
run_mode=rule
reason=provider_failure
attempts=1
usage=None
circuit_failures=1
```

调用方不再收到异常，符合失败关闭和降级要求。

### 2.2 测试结果

B9 专项：

```text
20 passed, 1 warning
```

B9 范围入口：

```text
39 passed, 1 warning
```

全量测试：

```text
143 passed, 1 warning
```

唯一警告为 Starlette/httpx TestClient 弃用提示，不阻塞 B9。

### 2.3 新增覆盖

- `RuntimeError` 不会穿透 `generate()`；
- `httpx.ConnectError` 会进入 fallback；
- `httpx.TimeoutException` 会进入 fallback；
- malformed JSON、缺少 choices/message/content 会转换为 provider 错误；
- HTTP 4xx 不重试；
- 重试响应 ID 变化只写入一笔 usage；
- budget lock 短时占用不会让同一 operation 出现非确定结果；
- provider 异常不创建世界事件、关系或记忆写入；
- fallback、熔断计数和 usage 记录可观察。

## 3. 已确认通过

- provider-agnostic 接口与 mock provider；
- OpenAI-compatible provider 骨架；
- 审核拒绝、审核不可用和失败关闭；
- 输入、输出、审核、调用次数和成本硬上限；
- operation 缓存与内容冲突；
- 传输异常分类、重试和熔断；
- usage 去重计费；
- 结构化输出白名单；
- 提示词版本和脱敏审计；
- schema version 3 契约；
- 成本审计 CLI。

## 4. 接受的限制

- 真实供应商的幂等请求 ID、实际价格、审核协议和超时仍需 A 在 staging 验证；
- B9 只做本地 mock 和临时数据库测试，不读取真实 API Key，不连接生产数据库；
- staging 的真实网络故障和供应商行为测试留给后续 A/G2 验收。

## 5. 合并决定

```text
B9 复审：PASS
允许合并 codex/bx-b9-llm-gateway 到 main
下一批：B10 集成、CI、E2E 与穿帮检测
```

B 不操作服务器；真实模型和审核供应商配置仍由 A 执行。