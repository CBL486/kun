# R9 最终集成审查结果

状态：PASS（代码候选通过，生产部署仍由 A 执行）  
审查人：Agent A  
审查日期：2026-11-08  
分支：`codex/gate-r9-review`

## 1. 审查范围

R9 分支 `codex/product-r9-integration`：

- 功能提交：`06b22de`
- 交接提交：`c3f9436`
- 基线：`296ceee`

已完成合并、代码审查、真实 DeepSeek smoke、浏览器证据和完整回归。

## 2. 已确认实现

### 聊天语义

- 公共状态统一为 `delivered`；
- 页面显示“审核后送达”和“已送达”；
- 不再同时显示“已排队”和即时回复；
- OpenAPI 与前端测试已更新。

### 真实模型 runtime

- `/chat` 通过既有 LlmGateway 调用 DeepSeek；
- 组装 PersonaBaseline、PersonaState、关系、情绪和近期事件；
- 经 moderation、每日预算、成本归集、重试、熔断和 operation 幂等；
- provider、审核或预算失败返回世界内安全 fallback；
- 聊天不写世界事件、关系或人格变更。

### 沉浸和安全

- 正常回复使用世界内第一人称体验；
- 身份追问不切成系统客服播报；
- 高风险请求有自然拒绝路径；
- PersonaBaseline 不可被模型直接覆盖；
- 系统安全策略不进入玩家可读的基线文本。

### R7/R8

- R7 每日学校、30 分钟学习、token 预算、私有反思、study 动画和 WorldTick 已集成；
- R8 公开媒体白名单、跳转复验、审核、预算、去重和私有媒体事件已集成；
- 媒体接口、`/world`、`/agent`、`/timeline`、`/chat` 均受 setup gate 保护；
  未配置 Key 和人设时统一返回 `setup_required`。

## 3. A 额外修复

### 中文 prompt token 估算

真实 DeepSeek smoke 第一次暴露：

```text
token_limit_exceeded
```

原因是 gateway 使用“字符数 / 4”估算中文 prompt token，导致正常中文输入被误判。已改为中文感知估算，并按预算策略检查真实 usage。

### 记忆幻觉

真实 smoke 曾生成没有上下文中对应事件的“旧书区潮汐谈话”。已补充：

- 系统提示词明确禁止无依据编造具体回忆；
- reply context 增加记忆约束；
- 真实 smoke 复查不再复现该问题。

## 4. 真实 DeepSeek smoke

证据：`docs/r9-chat-smoke-deepseek.json`

```text
provider=deepseek
model=deepseek-flash
api_key_configured=true
reply_kind=model
operation.status=succeeded
operation.run_mode=model
degradation_reason=null
key_leak=false
```

未打印或写入完整 Key、prompt、usage 以外的内部字段。

## 5. 完整验证

```text
pytest：253 passed, 9 skipped, 1 warning
七日 E2E：passed，49 events，0 errors，1 warning
成本对账：bill_matches=true
config-check：issues=[]
release build：231 files
release verify：issues=[]
package_sha256：3e12fecdd9276dc7cb71bd5b3d7585b87908e1ed2e0dd951866365a7d58e0871
```

setup 与 R9 定向回归：19 passed

浏览器证据：

- `docs/screenshots/r9-chat-delivered-desktop.png`
- `docs/screenshots/r9-chat-delivered-mobile.png`
- `docs/screenshots/r7-study-desktop.png`
- `docs/screenshots/r7-study-mobile.png`
- `docs/screenshots/r2-idle-desktop.png`
- `docs/screenshots/r2-walk-desktop.png`

## 6. 生产前仍需 A 执行

1. schema 5 生产迁移、Persona JSON 导入和基于备份的回滚演练；
2. 注册 `AIWorld-WorldTick` 并验证 10 分钟节奏；
3. 在目标中文 Windows 验证 setup ACL 和 release 外数据目录；
4. 做一次真实公开 B站链接 smoke，确认热门列表失败时安全降级；
5. 部署新 release 后重新启动 G3 14 天观察；
6. 外部内容审核供应商仍需接入，或由项目所有者明确接受本地审核边界。

## 7. 已知非阻塞项

- R2 是轻量原创像素风第一版，后续仍可提升细节和表情；
- R8 仅读取公开 OG 元数据，不做完整视频/ASR；
- 真实媒体热门接口可能受地区/反爬影响，必须保持安全失败；
- G3 当前观察基于旧 rc7，新版本部署后必须重新起算。

## 8. 合并决定

```text
R9：PASS
代码候选：允许合并到 main
生产部署：仍需 A 执行
下一步：构建新 release、staging smoke、生产切换、重启 G3
```
