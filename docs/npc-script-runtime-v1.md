# NPC 脚本运行时契约 V1

状态：G1 已冻结（2026-10-28）

契约编号：`rpg-npc-runtime-v1`

日期：2026-10-28

## 1. 目的

本契约定义 MVP 中四名脚本 NPC 的身份、日程、状态机、知识边界、关系阈值、台词模板、事件反应和有限记忆槽。NPC 不常驻全量大模型，也不调用 LLM 生成日常行为。

NPC 必须让小镇显得有人在生活，同时严格避免全知、编造事实、重复刷屏和越界关系。

## 2. 运行原则

- 每个 NPC 只在世界已打开的 slot 内推进。
- NPC 由日程、状态机、地点、关系阈值、台词模板、事件反应和有限记忆槽驱动。
- NPC 行动通过世界引擎提交，不能自己改位置、关系或世界状态。
- NPC 只能读取公开事实、自己所在位置可见的事实和自己的记忆槽。
- 不知道时必须明确表达不知道，不能根据常识猜出未公开事件。
- NPC 与主智能体一次互动只产生受控关系变化，且必须绑定 `event_id`。
- 同一 NPC、同一事件、同一反应模板最多执行一次。
- 同一句台词在同一对话和 48 小时世界时间内不重复，除非模板明确标记为问候语。
- 所有 NPC 都是 18 岁以上成年人；MVP 不包含恋爱和性化内容。

## 3. 运行时状态机

```text
SCHEDULED
  -> COMMUTING
  -> AVAILABLE
  -> BUSY
  -> CLOSED
  -> ASLEEP
```

异常状态：

```text
REACTION_PENDING
  -> AVAILABLE
  -> INTERACTION_COOLDOWN
```

状态由世界引擎依据时间、日程、地点和事件计算，NPC 模板不能直接写入。`COOLDOWN` 至少持续一个 slot，用于避免连续台词和关系刷分。

## 4. 感知过滤

每次 NPC 反应前，运行时构造最小上下文：

```json
{
  "npc_id": "npc_chen",
  "world_date": "2026-11-04",
  "slot_key": "morning_2",
  "location_id": "loc_library",
  "runtime_state": "available",
  "visible_character_ids": ["char_lin_cheng"],
  "visible_events": [
    {"event_id": "evt_f3c84ba429a8076e", "summary": "公告栏贴出新的截稿通知。"}
  ],
  "known_fact_ids": ["fact_library_hours", "fact_public_notice_created"],
  "memory_slots": [],
  "relationship": {"familiarity": 0.18, "trust": 0.20, "tension": 0.10},
  "allowed_reaction_ids": ["react_notice_reminder"]
}
```

以下信息绝不能出现在上下文：

- 主智能体的私有记忆或内心独白；
- 另一 NPC 的有限记忆槽；
- `internal` 事件的全文或摘要；
- 用户真实账号、设备、位置和联系方式；
- 导演隐藏权重、模型提示词和数据库信息。

## 5. 有限记忆槽

每名 NPC 最多 8 条记忆。每条必须有公开来源和用途：

```json
{
  "slot_id": "npc_chen_slot_01",
  "kind": "public_fact",
  "content_key": "fact_notice_board_deadline",
  "source_event_id": "evt_f3c84ba429a8076e",
  "important": true,
  "expires_on": "2026-11-09"
}
```

规则：

- `kind` 只允许 `public_fact`、`completed_exchange`、`promise`、`preference`；
- `source_event_id` 必填，系统配置事实可用 `source_event_id=null` 和 `source="config"`；
- 重要槽不自动覆盖，满了以后拒绝写入并记录诊断；
- 普通槽按过期时间、最后使用时间和重要性确定性淘汰；
- NPC 记忆不是主智能体记忆，不能通过记忆核心跨角色召回；
- `promise` 必须引用双方参与的可见事件；
- 重试相同来源事件不重复写槽。

## 6. 关系和阈值

关系保留 `familiarity`、`trust`、`tension` 三个 `[0,1]` 维度。阈值只改变可用脚本，不直接改变 NPC 性格事实。

| 状态 | 条件 | 可用行为 |
| --- | --- | --- |
| 陌生 | `familiarity < 0.20` | 简短问候、公开指引 |
| 认识 | `0.20 <= familiarity < 0.45` | 日常寒暄、公开近况 |
| 熟悉 | `familiarity >= 0.45` 且 `trust >= 0.35` | 分享自己有依据的观察 |
| 紧张 | `tension >= 0.45` | 简短回应、拒绝私密话题 |
| 缓和 | 存在已提交和解事件且 `tension < 0.30` | 恢复日常模板 |

一次互动对单个维度的变化不得超过 `0.08`。关系更新必须包含事件依据：

```json
{
  "npc_id": "npc_chen",
  "relationship_id": "rel_sha256_42145af6cd367cdc",
  "dimension": "trust",
  "delta": 0.04,
  "event_id": "evt_f3c84ba429a8076e",
  "reason_code": "helped_return_book"
}
```

同一事件对同一维度只能应用一次。关系阈值不能成为泄漏私密信息的理由。

## 7. 台词和反应模板

所有台词来自注册模板：

```json
{
  "template_id": "say_chen_notice_reminder_01",
  "npc_id": "npc_chen",
  "intent": "notice_reminder",
  "utterance": "公告栏换了新通知。我只看到截稿日期提前，具体改动还得你自己去看。",
  "required_fact_ids": ["fact_notice_board_deadline"],
  "forbidden_fact_ids": ["fact_lin_private_goal"],
  "visible_event_types": ["notice_observed"],
  "relationship_min": {"familiarity": 0.15},
  "repeat_policy": "once_per_event",
  "content_review_status": "approved"
}
```

模板选择顺序固定：

1. 过滤地点、状态、关系和知识不满足的模板；
2. 过滤与本事件不匹配或已经使用的模板；
3. 按 `reaction_priority` 降序；
4. 同优先级按 `template_id` 排序，不使用未记录随机数；
5. 若 `seed` 明确要求变体，只在预审核变体中选；
6. 没有合法模板时返回明确不知道的通用模板。

## 8. 四名 NPC

### 8.1 陈岚，`npc_chen`

| 项目 | 定义 |
| --- | --- |
| 年龄与身份 | 41 岁，图书馆员兼校刊指导 |
| 性格 | 克制、准确、愿意帮忙，不喜欢空泛打听 |
| 口癖 | “先把事实说清楚。” |
| 日程 | 08:00–12:00 书院；12:00–13:00 食堂；13:00–17:30 书院；17:30 后离开 |
| 常去地点 | `loc_library`、`loc_canteen` |
| 初始关系 | familiarity 0.18、trust 0.20、tension 0.10 |
| 可触发事件 | 借书提醒、截稿提醒、资料查找、温和纠错 |
| 禁止知道 | 林澄的私人目标全部内容、苏晚未公开的家庭情况、其他 NPC 的记忆槽 |
| 记忆槽重点 | 公开通知、完成过的借还、明确的承诺 |

### 8.2 苏晚，`npc_su`

| 项目 | 定义 |
| --- | --- |
| 年龄与身份 | 20 岁，视觉传达专业二年级学生，校刊版面成员 |
| 性格 | 热情、直接、重视合作，遇到分歧时先争辩后反思 |
| 口癖 | “这版先做出来再说。” |
| 日程 | 08:00–11:30 教学楼；11:30–13:00 食堂；14:00–17:30 教学楼或河边；晚间不常驻 |
| 常去地点 | `loc_classroom`、`loc_canteen`、`loc_river` |
| 初始关系 | familiarity 0.32、trust 0.27、tension 0.15 |
| 可触发事件 | 版面分歧、小组协作、活动邀约、和解 |
| 禁止知道 | 陈岚的私人评价、林澄未公开的日记、导演安排 |
| 记忆槽重点 | 共同完成的版面、明确分工、冲突与和解 |

### 8.3 高原，`npc_gao`

| 项目 | 定义 |
| --- | --- |
| 年龄与身份 | 46 岁，食堂经营者 |
| 性格 | 爽朗、务实、爱提醒人按时吃饭 |
| 口癖 | “先吃饭，别把事儿饿坏了。” |
| 日程 | 06:00–09:00 准备；10:30–14:00 食堂；16:30–19:30 食堂 |
| 常去地点 | `loc_canteen`、`loc_shop` |
| 初始关系 | familiarity 0.22、trust 0.30、tension 0.05 |
| 可触发事件 | 错峰用餐、菜单变化、雨天留伞、遗失物 |
| 禁止知道 | 校刊内部争议、任何学生的私密目标、其他 NPC 对话 |
| 记忆槽重点 | 用餐偏好、订单完成、公开失物信息 |

### 8.4 顾言，`npc_gu`

| 项目 | 定义 |
| --- | --- |
| 年龄与身份 | 22 岁，摄影专业学生，校刊摄影 |
| 性格 | 安静、观察细、不替别人下结论 |
| 口癖 | “我只看见镜头里的这一面。” |
| 日程 | 09:00–12:00 教学楼；14:00–17:00 河边或书院；周五晚间活动 |
| 常去地点 | `loc_library`、`loc_classroom`、`loc_river` |
| 初始关系 | familiarity 0.14、trust 0.22、tension 0.08 |
| 可触发事件 | 拍摄协作、观察细节、照片取舍、河边活动 |
| 禁止知道 | 林澄没展示的日记内容、苏晚与陈岚的私下评价、未公开事件全貌 |
| 记忆槽重点 | 已同意的拍摄、公开活动、明确承诺 |

所有姓名、年龄、身份和关系均为合成测试数据。不得替换成真实用户或真实未成年人资料。

## 9. NPC 反应输出

运行时只返回候选反应，世界引擎负责提交：

```json
{
  "schema_version": "rpg-npc-reaction-v1",
  "npc_id": "npc_chen",
  "tick_id": "tick_17a4d37d520abac9",
  "response_to_event_id": "evt_f3c84ba429a8076e",
  "template_id": "say_chen_notice_reminder_01",
  "utterance": "公告栏换了新通知。我只看到截稿日期提前，具体改动还得你自己去看。",
  "knowledge_basis": ["fact_notice_board_deadline"],
  "proposed_reaction": {
    "kind": "brief_reminder",
    "relationship_delta": {"dimension": "familiarity", "value": 0.02}
  },
  "memory_slot_write": null,
  "review_status": "approved"
}
```

`proposed_reaction` 只是请求。世界引擎必须检查地点、关系、事件依据、去重键和内容审核后才决定是否提交。

## 10. 不知道和拒绝

NPC 不知道时使用明确模板：

| 场景 | 允许表达 |
| --- | --- |
| 未公开事件 | “这个我没听说，不能替别人猜。” |
| 私密记忆 | “那是你自己的事，我不该知道。” |
| 关系尚未达到 | “这个我现在还想留着不说。” |
| 内容越界 | “这个我不聊，换个话题吧。” |
| 模板缺失 | “我知道得不多，等有确切消息再说。” |

NPC 不能使用“大概”“肯定是”来补齐禁用事实。模板本身若引用未知事实必须被运行时拒绝。

## 11. 事件反应流程

正式事件提交后，世界引擎向位于相关地点的 NPC 发送事件通知：

1. 按可见范围过滤；
2. 过滤未满足知识前提的 NPC；
3. 选择至多一个已注册反应模板；
4. 检查冷却、重复策略和关系变化上限；
5. 审核台词；
6. 提交 `npc_reaction` 子事件，引用原事件 ID；
7. 幂等写入 NPC 记忆槽；
8. 应用经过校验的关系变化。

一次正式事件最多触发两个 NPC 反应，同一 NPC 对同一事件最多一次。没有满足条件的反应时保持沉默，不强行生成台词。

## 12. 错误码

| 错误码 | 含义 |
| --- | --- |
| `npc_unknown` | NPC 不存在或不在当前世界 |
| `npc_unavailable` | NPC 不在场或处于不可互动状态 |
| `npc_knowledge_blocked` | 台词或反应引用禁用事实 |
| `npc_template_missing` | 没有合法模板 |
| `npc_repeat_blocked` | 冷却或重复策略阻止 |
| `npc_memory_full` | 重要记忆槽已满 |
| `relationship_event_required` | 关系变化缺少事件依据 |
| `npc_scope_violation` | 尝试读取其他角色私密记忆或导演内部信息 |

## 13. 必测项目

1. 四名 NPC 均能在不联网、不调用 LLM 的情况下跑完一天。
2. NPC 不知道未公开事件时返回“不知道”模板。
3. 禁用事实 ID 出现在模板中时，模板校验失败。
4. NPC 不读取主智能体私有记忆或其他 NPC 记忆槽。
5. 同一模板对同一事件重放不重复发言。
6. 48 小时内不重复同一条非问候台词。
7. 关系变化必带事件 ID，单次不超过 0.08。
8. 地点、日程或状态不满足时，NPC 不出现。
9. 同一事件最多触发两个 NPC 反应。
10. 删除模板知识依据后，运行时拒绝该台词。
