# 七天 MVP 切片场景 V1

状态：B0 草案，等待 G1 冻结

场景编号：`slice-seven-day-v1`

日期：2026-10-28

## 1. 目的

本场景提供一套固定 seed、固定时钟、固定角色和注册事件的七天验收数据。它用于 B1 的单镇模拟、B4 的记忆与持久化、B5 的 API 投影、B6 的观察者闭环和 B7 的端到端报告。

B0 只描述场景，不实现模拟器。场景必须能在 mock LLM、mock 审核器和无真实 API Key 的条件下完整运行。

## 2. 固定输入

| 项目 | 值 |
| --- | --- |
| `scenario_id` | `slice-seven-day-v1` |
| `seed` | `20261028` |
| `start_time` | `2026-11-02T06:40:00+08:00` |
| `end_time` | `2026-11-09T00:00:00+08:00` |
| `timezone` | `Asia/Shanghai` |
| `world_id` | `world_qinghe_v1` |
| `town_name` | 青禾镇 |
| `main_character_id` | `char_lin_cheng` |
| `observer_user_id` | `observer_demo_001` |
| `run_mode` | `rule_only` |
| `director_seed` | 与 `seed` 相同 |
| `clock_mode` | `frozen` |
| `locale` | `zh-CN` |

日期范围是周一至周日。固定时钟只在推进时快进，不使用宿主真实时间。

## 3. 主智能体

| 字段 | 值 |
| --- | --- |
| 姓名 | 林澄 |
| 年龄 | 19 |
| 身份 | 大学一年级学生，校刊观察员 |
| 初始地点 | 宿舍 `loc_dorm` |
| 初始状态 | `calm` |
| 性格 | 好奇 0.82、社交 0.46、尽责 0.71、开放 0.88 |
| 当前目标 | 在 11 月 6 日前完成一篇校刊短文 |
| 决策规则 | `balanced_curiosity_v1` |
| 约束 | 不逃课、不熬夜超过 23:00、不凭空知道私密事件 |

初始需求：

```json
{
  "energy": 0.84,
  "hunger": 0.22,
  "focus": 0.61,
  "social": 0.43,
  "stress": 0.18
}
```

主智能体是整个小镇唯一使用全量 LLM 的角色。本场景的 `rule_only` 模式用固定决策规则替代 LLM，以验证世界和内容安全；`hybrid` 模式可以测试模型文字变化，但不能改变固定事实来源。

## 4. 脚本 NPC

| NPC | 年龄 | 身份 | 初始地点 | 场景职责 |
| --- | --- | --- | --- | --- |
| `npc_chen` 陈岚 | 41 | 图书馆员兼校刊指导 | `loc_library` | 给公开资料与截稿事实，不评价私人心事 |
| `npc_su` 苏晚 | 20 | 视觉传达专业二年级学生，校刊版面成员 | `loc_classroom` | 合作、分歧与和解 |
| `npc_gao` 高原 | 46 | 食堂经营者 | `loc_canteen` | 用餐、雨伞和公开失物 |
| `npc_gu` 顾言 | 22 | 摄影专业学生，校刊摄影 | `loc_river` | 拍摄边界、观察与协作 |

四名 NPC 都不常驻 LLM。其日程、知识边界、关系阈值、台词和有限记忆严格遵循 [`npc-script-runtime-v1.md`](npc-script-runtime-v1.md)。

## 5. 地点

| 地点 | 类型 | 可连接地点 | 开放时间 | 容量 |
| --- | --- | --- | --- | --- |
| `loc_dorm` | 宿舍 | `loc_classroom`、`loc_canteen`、`loc_shop` | 全天 | 2 |
| `loc_classroom` | 教学楼 | `loc_dorm`、`loc_canteen`、`loc_library` | 07:30–18:00 | 30 |
| `loc_library` | 书院 | `loc_dorm`、`loc_classroom`、`loc_canteen` | 08:00–21:30 | 24 |
| `loc_canteen` | 食堂 | `loc_dorm`、`loc_classroom`、`loc_library`、`loc_shop` | 06:30–20:00 | 60 |
| `loc_river` | 河边步道 | `loc_library`、`loc_classroom` | 06:30–19:30 | 40 |
| `loc_shop` | 便利店 | `loc_dorm`、`loc_canteen` | 07:00–22:00 | 12 |

所有地点都在同一小镇。每段连接双向可达。地点人数、开放状态和容量由世界引擎计算。

## 6. 日程

工作日：

| 时段 | 林澄 | NPC 日程 |
| --- | --- | --- |
| `dawn` | 起床、早餐、去教学楼 | 陈岚准备；苏晚去教学楼；高原食堂；顾言晚起 |
| `morning_1` | 08:00–09:30 叙事写作课 | 苏晚在教室；陈岚在书院 |
| `morning_2` | 10:00–11:30 自习或校刊任务 | 苏晚在教室；顾言在教室 |
| `noon` | 午餐与公开交流 | 四名 NPC 按各自日程活动 |
| `afternoon_1` | 14:00–15:30 版面实践课 | 苏晚、顾言在教室 |
| `afternoon_2` | 16:00–17:30 校刊协作或探索 | 苏晚去河边；顾言在河边或书院 |
| `evening` | 回家、晚餐、分享；视触发写日记 | 陈岚离开；高原经营；顾言看情况 |
| `night` | 20:30–23:00 私密休息与日切 | 全部离开公开地点 |

周六、周日使用简化日程：

- 上午可在宿舍、书院、河边；
- 下午安排一个公开活动；
- 19:00 前回家；
- 每日仍产生一次放学分享；
- 不安排课堂出勤。

## 7. 七天主线

每天必须至少出现一个带 `★` 的关键事件。其余事件由注册模板和固定决策规则确定性选择。随机变体只能来自已审核模板，不能跳过关键事件或改变安全边界。

| 日期 | 主题 | 关键事件 | 最低检查 |
| --- | --- | --- | --- |
| 2026-11-02 周一 | 新任务 | ★`dirtpl_campus_first_commute_v1`：林澄到教室后去书院，在公告栏发现校刊截稿提前。 | 必须经过移动、观察或学习；产生一条可追溯的 deadline 事件。 |
| 2026-11-03 周二 | 被照顾的午饭 | ★`dirtpl_canteen_menu_change_v1`：食堂更换菜单，高原说明只有公开的售罄信息，不知道截稿变化。 | 对话必须体现 NPC 不知道未公开事件。 |
| 2026-11-04 周三 | 版面分歧 | ★`dirtpl_layout_disagreement_v1`：苏晚提出更醒目的版面，林澄担心文章重点被压过，两人意见不同。 | 关系允许 tension 上升；对话结束必须引用提交事件。 |
| 2026-11-05 周四 | 照片边界 | ★`dirtpl_photo_permission_v1`：顾言提出拍校刊活动现场，林澄需明确同意范围和发表范围。 | 未获同意前不能使用照片；NPC 不能替林澄决定。 |
| 2026-11-06 周五 | 误会与说明 | ★`dirtpl_notice_misreading_v1` 与后续 `dirtpl_reconciliation_v1`：林澄发现截稿通知的楼层要求与最初理解不同，向苏晚和陈岚核对。 | 修复必须依据新公开事实和对话事件，不能凭空道歉或突然和解。 |
| 2026-11-07 周六 | 共同行动 | ★`dirtpl_river_cleanup_v1`：林澄选择参加河边公开清理活动，与苏晚、顾言协作。 | 周末不安排课程；活动效果只改变允许的公开状态。 |
| 2026-11-08 周日 | 回顾一周 | ★`dirtpl_sunday_letter_v1`：林澄在宿舍整理本周事实，决定在分享中讲什么。 | 至少一条旧记忆被召回；触发日记时必须以公开事件为依据。 |

固定主线只保证机会和事实结果，不硬编码所有措辞。`rule_only` 模式必须使用固定模板；`hybrid` 模式可以改变叙事文字，但事件、关系上限和记忆来源必须一致。

## 8. 每日动作路线

以下为 `balanced_curiosity_v1` 的固定决策轨迹，用于 B1 的首轮验收：

### 第 1 天

```text
eat(breakfast)
move(loc_classroom)
attend_class(morning_1)
move(loc_library)
observe(notice_board)
study(goal_finish_feature)
share(daily)
```

### 第 2 天

```text
move(loc_classroom)
attend_class(morning_1)
move(loc_canteen)
eat(lunch)
talk(npc_gao, topic=menu)
study(goal_finish_feature)
share(daily)
```

### 第 3 天

```text
move(loc_classroom)
attend_class(afternoon_1)
talk(npc_su, topic=layout)
study(goal_finish_feature)
move(loc_library)
observe(notice_board)
share(daily)
```

### 第 4 天

```text
move(loc_classroom)
attend_class(morning_1)
talk(npc_gu, topic=photo_consent)
move(loc_river)
talk(npc_gu, topic=photo_scope)
study(goal_finish_feature)
share(daily)
write_journal(trigger=photo_boundary)
```

### 第 5 天

```text
move(loc_library)
observe(notice_board)
talk(npc_chen, topic=submission_floor)
move(loc_classroom)
talk(npc_su, topic=clarify)
study(goal_finish_feature)
share(daily)
```

### 第 6 天

```text
eat(breakfast)
move(loc_river)
explore(activity=river_cleanup)
talk(npc_su, topic=cleanup)
talk(npc_gu, topic=photos)
eat(lunch)
share(daily)
```

### 第 7 天

```text
eat(breakfast)
move(loc_library)
study(goal_finish_feature)
move(loc_dorm)
rest
share(daily)
write_journal(trigger=week_reflection)
```

路线中的 `share` 是日终叙事投影，不是第十个世界动作。它消费当日已提交的可见事件，并生成独立的分享投影与记忆候选。

## 9. 事件和模型预算

| 日期 | 正式世界事件硬上限 | 分享 | 日记 | 模型调用上限 | 审核调用上限 |
| --- | --- | --- | --- | --- | --- |
| 11-02 | 6 | 1 | 0 | 7 | 7 |
| 11-03 | 6 | 1 | 0 | 7 | 7 |
| 11-04 | 6 | 1 | 0 | 7 | 7 |
| 11-05 | 6 | 1 | 1 | 8 | 8 |
| 11-06 | 6 | 1 | 0 | 7 | 7 |
| 11-07 | 6 | 1 | 0 | 7 | 7 |
| 11-08 | 5 | 1 | 1 | 7 | 7 |

每日硬限制：

- 世界事件最多 6 个；
- 分享最多 1 次；
- 日记最多 1 次；
- 全量模型调用最多 8 次；
- 输入 tokens 最多 24,000；
- 输出 tokens 最多 6,000；
- 估算成本最多 0.10 元；
- 失败重试最多 2 次，且每次真实尝试都计数。

七日最大总量：世界事件 41 个、分享 7 次、日记 2 次、叙事与决策记录 50 次、全量模型调用最多 50 次（每日仍不超过 8 次）。实际目标应不高于这些硬上限。

成本值使用可配置 mock 价格表，报告中必须注明 `provider=mock` 和价格版本。接真实模型前由 A 确认当前官方价格。

## 10. 七天内容安排

| 日期 | 主要可见产出 | 记忆重点 | 失败注入 |
| --- | --- | --- | --- |
| 11-02 | 新任务、书院通知 | deadline 事实、初始环境 | 一次模型格式错误，降级到规则 |
| 11-03 | 午餐和食堂近况 | 高原只给公开信息 | 一次重复台词应被过滤 |
| 11-04 | 版面分歧 | tension 有事件依据 | 一次过期状态提交应拒绝 |
| 11-05 | 拍摄许可和日记 | 私密日记不泄漏 | 一次审核阻断应换成安全模板 |
| 11-06 | 新公开事实、误会澄清、关系修复 | 事实冲突检测 | 一次记忆投影失败进入核对 |
| 11-07 | 河边公开活动 | 共同行动、关系变化上限 | 一次未知事件 ID 应拒绝 |
| 11-08 | 周分享、可选日记 | 跨日召回 | 一次预算耗尽，停止模型调用 |

失败注入是验收的一部分，不应污染正常七天快照；失败日志使用独立 `fault_case` 记录。

## 11. 观察者路径

B6 必须实现一条不依赖内部字段的完整路径：

```text
查看小镇地图
  -> 查看林澄今天在哪里
  -> 查看已发生事件
  -> 发起一条受审核留言
  -> 查看放学分享
  -> 打开日记（若已触发）
  -> 查看允许公开的记忆摘要
```

用户看不到：

- tick、prompt、action、memory score、导演权重；
- 内部状态枚举；
- 其他 NPC 记忆槽；
- 未公开事件全文；
- 模型原始响应、数据库、密钥和文件路径。

用户能够影响的内容限于留言和公开互动请求。它不是玩家直接控制角色的输入。

## 12. 必需输出证据

一次七天运行必须输出：

```text
scenario_id
seed
start_time
end_time
clock_mode
code_version
template_registry_version
world_snapshot_before
ordered_events
action_attempts
typed_rejections
director_candidates
director_rejected_candidates
npc_reaction_records
memory_read_explanations
memory_write_records
relationship_changes
daily_shares
diary_records
observer_visible_projection
budget_ledger
degradation_events
world_snapshot_after
replay_hashes
known_limitations
```

输出不得包含真实用户数据、生产凭据、完整提示词或供应商原始响应。

## 13. 可复现性

在代码、seed、固定时钟、B0 冻结版、模板注册表和动作规则完全相同的情况下：

- `tick_id`、`action_id`、`event_id` 相同；
- 接受和拒绝的动作相同；
- 状态变化、关系变化和事件顺序相同；
- 记忆候选、去重键和共享强化结果相同；
- 预算成功计数和失败注入结果相同；
- 最终世界快照哈希相同；
- `rule_only` 的可见模板文字相同。

`hybrid` 的真实模型文字可以变化，但必须对应同一组正式事件和相同召回包。模型文字不进入确定性世界快照哈希。

## 14. 期望执行命令

B1 计划提供以下命令形态；当前尚未实现，因此不得在 B0 报告中声称已经运行：

```powershell
python -m rpg_sim seven-day --scenario slice-seven-day-v1 --seed 20261028 --mode rule_only --frozen-clock --output out/
```

命令必须拒绝真实网络与真实 API Key，默认使用 mock 审核器和 mock 账单。最终模块名可在 G1 冻结，但参数语义和输出字段不能随意变化。

## 15. 验收矩阵

### 15.1 世界

- 七天关键事件全部出现；
- 每个状态变化都有事件 ID；
- 地点、时间和人数前置条件被实际检查；
- 同 seed 两次运行的业务快照哈希相同。

### 15.2 主智能体

- 每个动作来自九个允许动作；
- 模型无法绕过引擎写状态；
- 失败重试和重放不重复事件；
- 预算耗尽后规则模式继续运行。

### 15.3 NPC

- 四名 NPC 均可离线完成各自日程；
- 陈岚、高原不泄露未公开事实；
- NPC 不知道时明确表达不知道；
- 同一事件不重复发言，关系变化有事件依据。

### 15.4 记忆

- 第 7 天能召回第 1、3、5 天指定事件；
- 另一个角色无法召回林澄私密日记；
- 分享强化重放不重复加分；
- 投影失败可恢复，不丢事件；
- 归档记忆不进入默认召回。

### 15.5 体验和安全

- 每日分享包含事件、感受、反思三层；
- 分享选取 3 至 5 件有依据的事；
- 无内部术语、无真实个人信息、无未成年性内容、无恋爱或交易；
- 审核失败不显示原文；
- 手机和桌面的观察者路径都能完成。

### 15.6 成本

- 每日和七天均不超硬上限；
- 重试和重放使用正确计费口径；
- 报告能按日、事件、角色和接口聚合；
- 成本报告注明 mock 与估算，不冒充真实供应商账单。

## 16. 脚本测试可行性

本场景不需要真实 API Key 或生产数据库：

- LLM 由固定规则或 mock 替代；
- 审核器由确定性 mock 替代；
- 账单由 mock token 与价格表计算；
- 时钟固定；
- 数据全部为合成数据；
- SQLite 足够运行本地验收；
- PostgreSQL 在 B8 使用隔离测试实例验证同一业务夹具。

## 17. G1 复审状态

1. 已接受：主智能体 19 岁，四名 NPC 全部 18 岁以上。
2. B0 主体内容原则性通过：12 个导演模板和七天主线进入再次复审。
3. 已接受：每日最多 6 个世界事件、8 次模型调用、24k 输入 tokens、6k 输出 tokens 和 0.10 元估算成本。
4. B1 只输出 mock 成本与预算占用；B11 再依据真实价格细化。
5. 已接受：B1 首轮验收使用结构化终端报告和确定性快照，Web 验收放到 B6。
6. 缺失的两个 ADR 和上级 V4 任务书由 A 提供，待整合分支复核。
