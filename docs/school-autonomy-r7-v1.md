# R7 学校、每日学习与自主行动 V1

状态：待 R7 审查

日期：2026-11-07

## 1. 每日流程

每个 `Asia/Shanghai` 自然日最多一个学习会话：

```text
09:00 之后首次 tick
  -> scheduled / 走向教学楼
  -> 5 分钟后 running / study
  -> 首次进入 running 时执行 1 次学习生成
  -> 真实持续 30 分钟
  -> completed
```

跨日未完成会话直接标记 `missed`，不补播。

## 2. 模型和成本

- 每天最多 1 个学习会话；
- 每个会话最多 1 次 `study_reflection` 生成；
- 默认 token budget 为 1200；
- 超出预算时改用本地静态反思；
- 生成失败时使用本地静态反思，不影响世界状态；
- 纯阅读/写作状态持续期间不调用模型；
- operation ID 为学习会话稳定 ID，重放返回原结果。

## 3. 数据

复用 R5 `study_sessions`。生成结果写入一条私有 `memory_events`，
`source=school`、`visibility=private`，不进入公开时间线、日记或记忆 API。

## 4. Presence

- `scheduled`：教学楼，`enter_place`，`moving=true`；
- `running`：教学楼，`study`，`moving=false`；
- `completed`：教学楼，`idle`；
- 公开 world 只包含位置和状态，不包含课程摘要、反思正文或记忆 ID。

R2 资源新增四方向 study 精灵表，角色播放器会播放 study。

## 5. 后台任务

`AIWorld-WorldTick` 现在调用 `app.world_tick`：持久世界时钟、学校每日状态机和
必要时的一次 LLM 学习反思。每 10 分钟运行一次；没有学习会话或未到时间时不调用
模型。

## 6. 重启和失败

- 同日重启：读取现有 study session，保留进度和反思记忆；
- 跨日重启：旧的 scheduled/running 标记 missed；
- provider 失败：本地静态反思；
- gateway 预算/审核失败：使用安全模板；
- session 唯一约束保证同一天不会重复创建。

## 7. 验证

```text
每日单会话、5 分钟走向教室、30 分钟结束：通过
单次 provider 调用、预算回退：通过
重启读取现有会话、跨日 missed：通过
公开 world 不含课程摘要/记忆 ID：通过
study 四方向资源与桌面/手机页面：通过
```
