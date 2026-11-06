# R4 默认与自定义 Persona 交接

状态：待 Gate 1 审查

日期：2026-11-06

分支：`codex/product-r4-persona`

基线：`codex/product-r3-setup-key`（包含 Gate 0 `d84501a` 与 R3 提交）

## 1. 交付

- 默认原创蓝鲸少女人设 `persona_default_whale`；
- 自定义 PersonaBaseline 表单和持久化；
- `PersonaBaseline` 与 `PersonaState` 分离；
- 基础人设 revision、修订历史和变更记录；
- `/api/persona/*` 状态、读取、默认和自定义接口；
- 启动页先完成 Key，再选择默认或自定义人设，最后进入世界；
- 自定义名称和身份投影到 `/agent` 与世界人物列表；
- 角色 ID 保持 `char_lin_cheng`；
- 修改基础人设不重置世界、关系、记忆或位置；
- 玩家不能直接写 PersonaState。

## 2. 校验与边界

- 年龄限制为 18～120；
- 字段有长度和列表数量限制；
- 拒绝控制字符、脚本标签和明显提示注入；
- 用户修改基础人设会生成新 revision；
- `PersonaState` 和 change log 继续保留；
- 不提供“换人设时自动清空世界”的隐式行为。

## 3. 测试

```text
pwsh -NoProfile -File scripts/test-b6.ps1
200 passed, 1 warning
```

`tests/test_r4_persona.py` 覆盖：

- 默认人设保存、重启读取和进入世界；
- 自定义人设 revision 2；
- 修改人设前后世界状态摘要一致；
- `/agent` 名称和身份更新；
- 提示注入、控制字符和未成年人年龄拒绝；
- PersonaState 直写返回 404；
- 前端不包含 PersonaState 编辑器或系统提示词。

## 4. 浏览器证据

使用隔离 fake Key API 和 Edge：

```text
桌面 1440×1000：无横向溢出
手机 390×844：无横向溢出
localStorage=[]，sessionStorage=[]，cookie=""
自定义人设保存后进入世界
世界角色名：潮汐
世界角色身份：青禾镇夜间图书馆管理员
控制台错误=[]
```

截图：

```text
docs/screenshots/r4-persona-choice-desktop.png
docs/screenshots/r4-persona-form-desktop.png
docs/screenshots/r4-persona-form-mobile.png
docs/screenshots/r4-persona-summary-desktop.png
```

复现工具：

```text
scripts/run_r4_evidence_api.py
scripts/capture-r4-evidence.js
```

## 5. 已知风险

- R4 基于 R3 分支，最终 Gate 1 仍需与 R1 观察者分支集成；
- PersonaState 当前只有初始结构和 revision 记录，事件驱动的演化在 R6；
- “开始新世界/清空记忆”尚未实现；R4 明确保证换人设不会隐式触发该动作；
- 真实 Persona 语义对模型生成的影响将在 R6/R9 集成验收。

## 6. 需要 A 做

1. 审查 PersonaBaseline/State 分离和 revision 语义；
2. 确认 R4 与 R1、R3 的合并顺序；
3. 在 Gate 1 验证自定义 Persona 不泄漏系统提示词，且换人设不重置世界。
