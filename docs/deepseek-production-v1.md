# DeepSeek 真实模型接入 V1

日期：2026-11-02

状态：隔离 staging live smoke 已通过，生产 `.env` 已准备（未重启服务、未切换 current）

## 1. 选型

- 供应商：DeepSeek
- API 协议：OpenAI-compatible
- Base URL：`https://api.deepseek.com`
- 模型：`deepseek-flash`
- 当前模型版本：DeepSeek-V4.1-Flash-1017
- Thinking：关闭
- JSON 模式：用于 `daily_share` 和 `action_candidate`

`deepseek-flash` 是 DeepSeek 当前正式模型名；旧项目默认值 `deepseek-chat` 不再作为新部署默认值。

## 2. 价格版本

保守使用峰值、cache-miss 价格：

```text
输入  $0.30 / 1M tokens
输出  $1.20 / 1M tokens
汇率  7.2 CNY/USD
版本  deepseek-flash-peak-cny-2026-11-02
输入  2.16 CNY / 1M tokens
输出  8.64 CNY / 1M tokens
```

峰谷价和 cache-hit 会降低实际成本；预算计算按较保守的峰值价格执行。

## 3. 环境变量

```text
AIWORLD_LLM_PROVIDER=deepseek
AIWORLD_LLM_BASE_URL=https://api.deepseek.com
AIWORLD_LLM_MODEL=deepseek-flash
AIWORLD_LLM_API_KEY=<server-private-secret>
AIWORLD_LLM_REVIEW_PROVIDER=local
AIWORLD_LLM_PRICE_VERSION=deepseek-flash-peak-cny-2026-11-02
AIWORLD_LLM_MAX_COST_CNY=0.10
```

API Key 服务器私有文件：

```text
C:\AIWorld\data\secrets\deepseek_api_key.txt
```

该文件只允许 `Administrator` 和 `SYSTEM` 读取。不得放入仓库、日志、发布包或聊天记录。

## 4. Staging live smoke 结果

```powershell
python -m rpg_llm.smoke `
  --url "postgresql+psycopg://..." `
  --budget-date "2026-11-02" `
  --output "C:\AIWorld\staging\evidence\deepseek-smoke.json"
```

- 实测：`succeeded` / `run_mode=model` / `provider=deepseek` / `model=deepseek-flash`
- 输入 112 tokens，输出 81 tokens，成本 `0.00094176 CNY`
- 审核 `approved`，账本写入 1 条 usage 记录
- 证据：`docs/deepseek-smoke-evidence-2026-11-02.json`

要求：

- `status=succeeded`
- `run_mode=model`
- `provider=deepseek`
- `model=deepseek-flash`
- `review.status=approved`
- 有输入/输出 token 和成本记录
- 结果写入 `llm_operations` 与 `llm_usage`

## 5. 降级与回滚

- 无 Key、401/403、超时、5xx、非法 JSON、审核失败和预算超限均保留规则模板；
- 临时回滚到无网络模式：

```text
AIWORLD_LLM_PROVIDER=mock
```

- 回滚不修改数据库 schema，不删除既有 LLM 账本记录。

## 6. 生产环境准备

- 生产 `.env` 已写入 DeepSeek provider、模型、价格版本和私有 API Key；
- 修改前已备份到 `data/secrets/app-env-before-deepseek-*.env`；
- 未重启生产 API/scheduler，未切换生产 `current`；
- 证据见 `docs/production-env-deepseek-2026-11-02.json`。

## 7. 边界

主智能体的世界动作仍由规则规划器和世界引擎裁决；DeepSeek 负责生成公开文字与候选内容，不得直接提交世界事件、修改关系或写入记忆。
