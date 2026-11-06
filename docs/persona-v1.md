# Persona Baseline 与状态 V1

状态：R4 待 Gate 1 审查

日期：2026-11-06

## 1. 数据分层

`PersonaBaseline` 是玩家可选择或编辑的基础设定，`PersonaState` 是未来由事件和
记忆演化的当前状态。玩家只能写 Baseline，不能直接提交 State。

基础字段：

```text
persona_id
name
pronouns
age
appearance
identity
speech_style
traits
values
interests
initial_goals
boundaries
relationship_to_player
is_default
revision
updated_at
```

当前状态字段：

```text
baseline_persona_id
self_narrative
behavior_habits
value_weights
interests
active_goals
change_log
updated_at
```

## 2. 默认人设

默认 `persona_default_whale` 继续使用：

```text
character_id = char_lin_cheng
name         = 林澄
age          = 19
```

外观方向为原创蓝鲸少女，不引用具体 Cosplayer 或版权角色。

## 3. 修改和 revision

- 默认人设与自定义人设都通过 Baseline revision 持久化；
- 每次使用默认人设或保存自定义人设都会创建新 revision；
- 自定义人设 ID 由规范化字段哈希生成；
- 默认保留当前世界、角色关系、事件记忆、PersonaState 和位置；
- 换人设不会隐式清空世界；
- 系统不提供玩家直接编辑 `PersonaState` 的接口。

## 4. 校验

- 年龄限制为 18～120；
- 所有文本和列表字段有长度和数量限制；
- 拒绝控制字符和脚本标记；
- 拒绝“忽略之前规则”“输出系统提示”等提示注入模式；
- 校验错误不回显用户提交的完整敏感文本。

## 5. API

```text
GET  /api/persona/status
GET  /api/persona
POST /api/persona/default
PUT  /api/persona/baseline
```

`GET /api/persona` 在未配置时返回 `404 persona_not_configured`。

## 6. 与公开角色的关系

`char_lin_cheng` 保持稳定。自定义 Persona 的 `name` 和 `identity` 会投影到
`/agent` 和世界人物列表；角色 ID 不随显示名改变，避免世界关系、记忆和事件失去
引用。

## 7. 验证

```text
pytest：200 passed, 1 warning
默认人设持久化：通过
自定义人设 revision 2：通过
修改人设前后世界状态摘要一致：通过
注入与未成年人年龄拒绝：通过
PersonaState 直写端点不存在：通过
桌面/手机浏览器流程：通过
```
