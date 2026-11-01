# B9 LLM 网关、审核与成本核心

状态：本地实现完成，等待 A 复审

日期：2026-11-01

适用 schema：`rpg_orm` version 3

## 1. 调用链

```text
operation_id 缓存检查
  -> 版本化提示词渲染
  -> 脱敏审计
  -> 硬预算预检
  -> 熔断检查
  -> provider 调用（同一请求最多重试一次）
  -> provider_request_id 去重计费
  -> 审核
  -> 结构化白名单
  -> 业务结果缓存
```

网关只产生文本和候选字段，不提交世界事件、不修改关系或记忆。

## 2. 幂等与计费

- `operation_id` 是逻辑业务键；成功、阻断和规则降级结果都会缓存；
- 同一 `operation_id` 内容不同返回 `duplicate_operation`；
- `provider_request_id` 唯一，传输层重试不会重复写入 usage；
- 一次真正的新模型尝试使用独立 `attempt_id`；
- 重试成功只产生一个世界候选和一个 operation 结果；
- token、审核调用、价格版本和成本写入 `llm_usage`；
- 重试次数和降级原因写入 `llm_operations`。

## 3. 预算

默认硬上限：

```text
模型调用       8 次 / 日
审核调用       12 次 / 日
输入 tokens    24,000 / 日
输出 tokens    6,000 / 日
估算成本       0.10 CNY / 日
单次输入       4,000 tokens
单次输出       1,200 tokens
```

调用前按输入估算和最大输出计算最坏成本。达到任一上限时不会调用 provider，
直接返回规则模板并记录 `budget_exceeded:<metric>`。

价格版本：

```text
mock-price-b9-2026-11-01
输入 4 CNY / 1M tokens
输出 16 CNY / 1M tokens
```

真实供应商上线前必须由 A 按官方价格新建版本，不能覆盖既有价格版本。

## 4. 审核

- `MockReviewAdapter` 用于无网络本地测试；
- `RemoteReviewAdapter` 是失败即关闭的 HTTP 适配骨架；
- 审核拒绝时不返回模型文本，只返回确定性规则模板；
- 审核超时、异常或未知状态按 `unavailable` 处理；
- 不许用重试绕过审核；
- 模型调用的成本在审核失败时仍会记账。

## 5. 熔断与规则模式

- 连续 provider 失败达到阈值后打开熔断；
- 熔断期间不发模型请求，直接进入规则模式；
- 冷却时间结束后允许一个探测请求；
- 探测成功恢复，失败重新打开；
- provider 未配置、预算超限、审核失败和结构化输出非法均不会阻断世界：
  只返回安全模板。

## 6. 结构化输出边界

只允许以下候选字段：

```text
summary
action_type
target_id
parameters
tone
confidence
```

出现 `state_changes`、关系变更、记忆写入或其他未知字段时，整个模型候选被丢弃，
进入规则模式并记录 `invalid_structured_output`。

## 7. 提示词与日志

- 提示词模板有稳定 ID 和版本号；
- 数据库保存 prompt SHA-256，不保存完整 prompt；
- 审计预览脱敏 API key、Bearer token、密码、邮箱和手机号；
- 不记录供应商原始响应、真实用户原文或 API Key；
- `docs/llm-audit-example.json` 提供脱敏格式样例。

## 8. 本地验证

```powershell
pwsh -NoProfile -File scripts/test-b9.ps1
```

成本审计：

```powershell
pwsh -NoProfile -File scripts/run-b9-audit.ps1 `
  -DatabaseUrl "sqlite:///./data/b9.sqlite3" `
  -BudgetDate "2026-11-01"
```

## 9. 生产边界

- 本地测试只使用 mock provider、mock reviewer 和临时数据库；
- 真实 API Key 只能由 A 通过环境变量配置，不进入仓库或日志；
- B9 不连接真实供应商、不执行部署；
- 真实供应商的计费请求 ID、价格版本、审核策略和超时参数仍需 A 在 staging 确认。
