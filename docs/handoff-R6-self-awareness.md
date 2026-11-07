# R6 自我认知与人设演化交接

状态：待审查

日期：2026-11-07

分支：`codex/product-r6-self-awareness`

基线：`0f936d9c3cb636e15c10f5af28bc4a495730b97b`

## 1. 交付

- `SelfAwarenessService` 事件驱动 PersonaState 演化；
- Baseline 不可由模型覆盖；
- 变化上限、6 小时冷却、事件去重和 change log；
- schema 5 EmotionState 联动；
- 系统安全策略与角色 profile 分离；
- `persona_reply` 提示模板；
- `/chat` 已配置 Persona 时返回世界内回应；
- 高风险自然拒绝、AI 身份问题保持角色人格；
- QQ 参考只采用 SelfState/心流边界思想，不复制提示词或代码。

## 2. 测试

```text
pytest：238 passed, 1 warning
七日 E2E：待最终 test-all 复核
```

覆盖：

- 事件驱动演化；
- Baseline 不变；
- 幂等和冷却；
- 事件外变化拒绝；
- 系统 profile 分离；
- 世界内普通/身份/高风险回复；
- chat 不创建 MemoryEvent；
- PromptTemplate 固定系统边界。

## 3. 浏览器证据

```text
桌面 1440×1000：无横向溢出
手机 390×844：无横向溢出
普通回复：世界内第一人称
身份问题：保持林澄人格
控制台错误：[]
```

截图：

```text
docs/screenshots/r6-in-world-chat-desktop.png
docs/screenshots/r6-in-world-chat-mobile.png
```

复现：

```text
scripts/run_r6_evidence_api.py
scripts/capture-r6-evidence.js
```

## 4. 已知风险

- 当前 `/chat` 使用 deterministic in-world responder；真实 LLM 生成在 R9 接入，
  但 prompt template 已保留系统安全边界；
- R6 的 `evolve_from_event()` 尚未由 R7 自动调度；
- 外部高风险请求仍建议 A 在集成审查中确认医疗/法律/财务话术；
- 不新增 schema，符合 Gate 2 约束。

## 5. 需要 A 做

1. 审查 Persona 演化上限、冷却和 change log；
2. 审查系统策略与角色设定的分离；
3. 在 R7/R9 将正式事件触发接入自动行动链；
4. 核实不把安全策略变成常规角色台词。
