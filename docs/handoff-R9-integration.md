# R9 最终集成交接

任务 ID：R9  
状态：代码、真实 DeepSeek smoke 和 A 最终验收完成；等待 staging/生产部署
日期：2026-11-08

## 1. 分支与提交

- B 分支：`codex/product-r9-integration`
- A 验收分支：`codex/gate-r9-review`
- 基线：`296ceee58fb360f640191759e70a26ef1497b043`
- 功能提交：`06b22de`
- 交接提交：`c3f9436`
- A 最终修复：中文 token 估算与记忆幻觉约束
- 生产任务未注册，生产目录未触碰

## 2. 改动文件

核心代码：

```text
app/api_models.py
app/local_state.py
app/main.py
app/self_awareness.py
rpg_llm/fallback.py
rpg_llm/prompts.py
rpg_llm/providers.py
rpg_orm/product_repository.py
web/app.js
web/index.html
```

测试与证据脚本：

```text
tests/test_r9_integration.py
scripts/run_r9_chat_smoke.py
scripts/run_r9_public_media_smoke.py
scripts/run_r9_schema_evidence.py
scripts/run_r9_study_evidence.py
scripts/capture-r6-evidence.js
```

同步更新的测试、OpenAPI 与当前产品文档：

```text
tests/test_b6_api.py
tests/test_b7_web.py
tests/test_b8_scheduler.py
tests/test_r6_self_awareness.py
docs/openapi-v2.json
docs/openapi-projection.md
docs/self-awareness-r6-v1.md
docs/web-ux-spec.md
README.md
```

## 3. 实现摘要

### 聊天语义

- 公开状态由 `queued` 统一改为 `delivered`；
- 页面显示“审核后送达”和“已送达”；
- 文案明确角色会按自己的节奏即时回应，不再同时显示排队与即时回复；
- 内部持久消息表继续保留，用于审计与重启恢复，不暴露为公开状态。

### 真实 runtime

- `/chat` 在数据库 Persona 模式中使用同一个既有 `LlmGateway`；
- 内部上下文组装 PersonaBaseline、PersonaState、当前关系、当前情绪和最多五条
  近期正式事件摘要；
- 关系与情绪先转换为自然语言，不把内部数值直接交给公开响应；
- provider 调用经过输出 moderation、每日硬预算、成本归集、重试、熔断和 operation
  幂等；
- provider、审核、预算或意外失败都返回世界内安全 fallback；
- 公共 `ChatResponse` 仍只有五个字段，不包含 prompt、usage、provider 或内部状态；
- 聊天不创建世界事件、关系变化或记忆。

### 沉浸与安全

- 系统安全边界保留在 `app/persona_policy.py` 和 `persona_reply` 系统模板；
- 正常回复允许第一人称主观体验、情绪和连续记忆；
- 不机械复述策略，不声称现实身体、地址、联系方式或现实行动能力；
- 高风险输入使用自然安全打断；身份追问保持林澄世界内身份；
- `PersonaBaseline` 没有新增模型可覆盖路径。

## 4. 测试结果

完整命令：

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
```

结果：

```text
pytest: 253 passed, 9 skipped, 1 warning
七日 E2E: passed, 49 events, 0 errors, 1 quality warning
成本对账: bill_matches=true, cost_cny=0.36320000
config-check: issues=[]
release build: 231 files
release verify: issues=[]
JavaScript syntax check: passed
```

唯一 warning 为既有 `StarletteDeprecationWarning`，不影响结果。质量 warning 为既有
单个 NPC 同日重复台词，不是 R9 回归。

`tests/test_r9_integration.py` 覆盖：

- 中文 prompt 不再被“字符数 / 4”低估并误触发预算拒绝；
- Persona、关系、情绪和近期事件进入模型上下文；
- `/chat` 状态为 `delivered`；
- 成功调用写 usage，但不写事件、关系或情绪；
- provider 不可用返回安全 fallback，operation 为 `fallback`，无 usage；
- 模型输出审核拒绝时不泄漏被拒文本，operation 为 `blocked`；
- 预算拒绝不调用 provider、无 usage，只返回安全 fallback；
- 页面和 OpenAPI 不再出现公开“排队”语义；
- prompt 明确禁止在没有上下文证据时编造具体回忆。

## 5. 截图与证据

聊天桌面 1440×1000：

```text
docs/screenshots/r9-chat-delivered-desktop.png
```

聊天手机 390×844：

```text
docs/screenshots/r9-chat-delivered-mobile.png
```

R7 学习状态回归：

```text
docs/screenshots/r7-study-desktop.png
docs/screenshots/r7-study-mobile.png
```

浏览器证据确认：

- 观察者消息标签为“已送达”；
- 林澄即时回应；
- 无横向溢出；
- 浏览器控制台错误为 0；
- 身份追问未出现“我是 AI”或系统播报。

## 6. 失败 fallback

可复现命令：

```powershell
python scripts/run_r9_chat_smoke.py
```

当前仓库内 fake 结果：

```text
docs/r9-chat-smoke-fake-2026-11-08.json
```

真实 DeepSeek chat smoke 已由 A 执行并通过：

```text
docs/r9-chat-smoke-deepseek.json
provider=deepseek
model=deepseek-flash
api_key_configured=true
reply_kind=model
operation.status=succeeded
operation.run_mode=model
degradation_reason=null
```

该 smoke 首次暴露了中文 prompt token 低估问题；修复后重新执行通过。证据文件经检查
不包含完整 Key、prompt 或 usage 内部字段。

## 7. R7 学习与预算

可复现证据：

```text
docs/r9-study-evidence-2026-11-08.json
```

本次状态链：

```text
walking -> running -> completed -> completed
token_budget=1200
input_tokens=80
output_tokens=80
school_reflection event count=1
```

同日重复 tick 未创建第二个 session，也未重复生成反思。学习摘要和 reflection memory
ID 不进入公开页面。

## 8. R8 公开媒体

fixture 证据：

```text
docs/r8-evidence-2026-11-07.json
```

真实公开 B站 OG 只读 smoke：

```text
docs/r9-public-media-smoke-2026-11-08.json
```

结果：`status=reviewed`，写入一条私有 `importance=0.3` 媒体事件；请求不携带
Cookie/Authorization，不登录，不自动点赞、评论、关注、私信或投币。

当前网络下 B站公开热门 API 曾返回非 JSON，热门列表仍按安全失败处理；直接公开视频
OG 读取成功。A 在 staging 可重试热门列表，但失败不应写记忆。

## 9. Schema 5

可复现证据：

```text
docs/r9-schema-evidence-2026-11-08.json
```

结果：

```text
migrate -> schema 5
Persona JSON import -> revision 2, baseline=潮汐, change_log=1
rollback -> schema 0, tables 25 -> 0
```

该 rollback 是隔离测试库的完整演练。生产回滚必须按
`docs/rollback-runbook.md` 和已验证备份执行，不能把测试 drop 命令当生产步骤。

## 10. 已知风险

- DeepSeek smoke 已通过，但生产服务器仍需使用服务器自己的 Key 再执行一次部署后 smoke；
- B站热门 API 可能受网络、地区或反爬策略影响，必须保持安全失败；
- 默认聊天单日预算沿用 `LlmGateway` 的每日硬上限，达到上限后会返回安全 fallback；
- `AIWorld-WorldTick` 仍需 A 在目标机注册并观察 10 分钟节奏；
- Windows ACL 的 `icacls` 分支仍需真实中文 Windows 目标机由 A 验证；
- R2 角色美术仍是轻量原创像素第一版，不阻塞 R9，但后续可继续提升动作与表情。

## 11. 需要 A 执行或决策

1. 在 staging 验证保存 Key、重启、清除 Key 后重新门禁，以及日志、浏览器存储和
   响应中均无完整 Key。
2. 在目标 Windows 机验证 setup ACL 和 release 外数据目录持久性。
3. 注册并确认 `AIWorld-WorldTick` 为 10 分钟节奏。
4. 执行生产 schema 5 迁移、Persona JSON 导入和基于备份的回滚演练。
5. 重试一次真实 B站公开热门接口；失败时确认不写记忆且页面安全降级。
6. 部署新 release 后使用生产服务器 Key 执行一次 chat smoke。
7. 重新启动 G3 14 天观察；当前旧 rc7 观察不计入新版本。
8. 完成公开入口代理保护验证后，再决定是否进入公开试用。
