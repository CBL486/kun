# QQ 项目记忆与人格参考摘要 V1

状态：Agent A 为 B 整理的参考摘要  
来源项目：`D:\Users\LENOVO\Documents\ChatGPT\QQ`  
用途：供 Agent B 设计 AI World 的事件、关系、情绪、人设演化和媒体观察参考。  
注意：这是设计参考，不是要求复制 QQ 项目的全部业务代码。

## 1. 参考文件

```text
bot_core/memory.py
bot_core/self_model.py
bot_core/thought_flow.py
bot_core/autonomy.py
bot_core/video.py
bot_core/persona.py
bot_core/config.py
personas/
tests/test_memory.py
tests/test_persona.py
README.md
```

## 2. 记忆分层

QQ 项目当前采用轻量方案：

- SQLite 持久化近期消息。
- 每 6 个用户回合整理一次长期记忆摘要。
- 滚动摘要保留跨会话上下文。
- 消息带 `importance`、`emotional_weight`、`kind`、`confidence`、`source`。
- 检索时综合：
  - 关键词相关性
  - 重要性
  - 情绪权重
  - 时间衰减
  - 访问次数
- 默认保留最多 400 条存储消息，近期上下文默认 16 条。
- 记忆整理时排除密码、验证码、支付信息等敏感内容。

## 3. 关系状态

`self_model.py` 使用关系状态：

```text
familiarity
trust
warmth
turns
last_seen_at
```

- 每次正常互动只做小幅增加。
- 正面互动最多小幅提升 trust/warmth。
- 重复互动不应无限刷高关系。
- 关系状态与具体用户/会话绑定。

AI World 需要在此基础上扩展：

```text
affection
trust
familiarity
warmth
tension
```

并且每次变化必须引用 `source_event_id`。

## 4. 自我状态

`self_model.py` 的 `SelfState` 包含：

```text
energy
valence
curiosity
self_narrative
interests
goals
experience_count
updated_at
```

特点：

- 有自然衰减/恢复。
- 兴趣和目标来自长期活动。
- `self_narrative` 是自我认识摘要。
- 允许功能性情绪影响语气和选择，但不直接向用户播报数值。
- 低能量会影响是否主动发起活动。

AI World 应将其扩展为 `PersonaState`，并增加：

- behavior_habits
- value_weights
- change_log
- baseline_persona_id
- 事件证据和变化上限

## 5. 私有心流

`thought_flow.py` 提供：

- 每个会话一条有界私有思绪流。
- 记录 thought、open_question、status。
- 只在有持续话题或开放问题时继续思考。
- 默认不向用户直接展示完整心流。

AI World 可以把“心流”用于：

- 角色独处时的内部反思
- 对未完成事件的持续思考
- 学习后的自我提问
- 不直接暴露给玩家，只通过行为/语气间接体现

## 6. 自主活动

`autonomy.py` 设计：

- 低频自主活动。
- 自己看公开视频、安静复盘、翻表情库、写私人小记。
- 活动结果形成成长记录。
- 活动有节流，避免持续调用模型。
- 活动不是玩家命令，不要求玩家实时看到。

AI World 应复用“低频自主活动”的思路，但以世界内行动和事件为主，不直接使用 QQ 表情/语音等功能。

## 7. 媒体观察

`video.py` 支持：

- 公开抖音/B站链接。
- 提取视频画面。
- 可选 ASR 转写。
- B站公开热门列表。
- 不绕过登录、DRM 或私密内容限制。
- 观看后的摘要和感受可以进入记忆。

AI World 应限制：

- 只处理公开链接或白名单。
- 不自动点赞/评论/关注/私信/投币。
- 每次只保留摘要和感受，不保存完整视频。
- 内容必须审核后才进入记忆。
- CI 使用 fixture/mock，不直接访问平台。

## 8. 人格卡

`persona.py` 支持：

- Markdown 人设。
- SillyTavern V2 JSON 人格卡。
- 基础字段：名字、描述、性格、场景、系统提示、对话后指令、对话示例。

AI World 不应直接把这些字段拼成公开发布内容。需要拆分为：

- `PersonaBaseline`：玩家可编辑的基础人设。
- `PersonaState`：由事件演化的当前状态。
- `PersonaChangeLog`：可追溯的变化记录。

## 9. 与 AI World 的对应关系

| QQ 项目 | AI World |
| --- | --- |
| messages | memory_events + working memory |
| summaries | memory summaries |
| importance | importance |
| emotional_weight | emotional_weight |
| relationship familiarity/trust/warmth | 扩展关系向量 |
| SelfState | PersonaState + EmotionState |
| thought flow | private reflection / inner thoughts |
| autonomy | 世界内自主活动和学校/媒体观察 |
| video | 受控媒体观察适配器 |
| persona card | PersonaBaseline + PersonaState |

## 10. 不要照搬的部分

- 不复制 QQ 的消息分条、表情、语音、NapCat、QQ 协议端逻辑。
- 不复制 QQ 的长期提示词原文。
- 不把 QQ 的表情/语音/群聊能力带入 AI World。
- 不把 QQ 的用户数据、数据库或真实 Key 带入本项目。
- 不在单元测试中访问真实抖音/B站。

## 11. B 在 R5/R6/R8 的必读要求

B 在开始 R5 前必须：

1. 读取本摘要。
2. 如环境允许，读取 QQ 项目对应源码。
3. 在 `docs/agent-B-rework-context-v1.md` 或后续设计文档中记录哪些模式被采用、哪些被拒绝。
4. 不复制无关代码，只复用数据模型和边界思想。
