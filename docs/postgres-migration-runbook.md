# PostgreSQL 迁移执行清单

状态：供 A 在生产环境执行；B 不执行本清单

日期：2026-11-07

## 1. 前置条件

A 必须确认：

- 已取得变更批准和生产数据库维护窗口；
- 已完成最近一次可恢复备份；
- 已核对备份校验值和恢复演练记录；
- 已确认应用版本与新 schema 兼容；
- 连接串只通过受控环境变量传入，不写入仓库和日志。

## 2. 环境变量

由 A 在自己的受限终端设置：

```powershell
$env:RPG_DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:<port>/<database>"
```

不要把真实值粘贴到代码、文档、聊天或提交记录。

## 3. 当前版本检查

```powershell
python -m rpg_orm version --url $env:RPG_DATABASE_URL
```

预期输出：

```json
{"schema_version": 0}
```

空库首次迁移为 0。若不是 0，先停止并与代码版本核对。

## 4. 迁移

```powershell
python -m rpg_orm migrate --url $env:RPG_DATABASE_URL
```

预期输出：

```json
{"schema_version": 5}
```

迁移可重复执行；再次执行不得产生重复表或重复版本记录。

## 5. 迁移后核验

```powershell
python -m rpg_orm version --url $env:RPG_DATABASE_URL
```

并由 A 在只读查询工具中确认：

- `schema_versions` 最高版本为 5；
- `world_heads`、`world_versions`、`actions`、`events` 存在；
- `memories`、`memory_projection_outbox`、`npc_memory_slots` 存在；
- `scheduled_tasks`、`observer_messages` 存在；
- `llm_operations`、`llm_usage`、`llm_cost_attributions` 存在；
- `memory_events`、`relationship_states`、`emotion_states` 存在；
- `persona_baselines`、`persona_states`、`persona_change_log` 存在；
- `study_sessions`、`media_observations` 存在；
- `setup_state`、`deepseek_credentials`、`world_clock_states` 存在；
- 索引 `idx_memories_scope_state`、`idx_memories_source_event` 存在；
- 应用 `/ready` 或等价数据库健康检查通过。

旧 JSON 数据导入：

```powershell
python -m rpg_orm import-persona-json `
  --url $env:RPG_DATABASE_URL `
  --path "C:\AIWorld\data\persona\persona.json" `
  --world-id world_qinghe_v1 `
  --character-id char_lin_cheng
python -m rpg_orm import-setup-json `
  --url $env:RPG_DATABASE_URL `
  --path "C:\AIWorld\data\setup" `
  --world-id world_qinghe_v1
```

导入可重复执行。`deepseek_credentials` 只保存 `key_ref` 和掩码，不保存完整 Key。

## 6. 回滚

回滚会删除 B5 创建的表，只能由 A 在确认备份可恢复后执行：

```powershell
python -m rpg_orm rollback --url $env:RPG_DATABASE_URL --confirm-rollback
```

执行后检查：

```powershell
python -m rpg_orm version --url $env:RPG_DATABASE_URL
```

预期 `schema_version=0`。如应用仍运行，必须先停止写入或切换到兼容版本。

## 7. 证据

A 执行后应保存：

- 执行时间与操作人；
- 迁移前后 schema 版本；
- 备份标识和校验值；
- 健康检查结果；
- 回滚是否发生及恢复验证；
- 应用版本和代码提交哈希。

## 8. 禁止事项

- B 不执行 SSH、数据库迁移或生产回滚；
- 不在命令行历史中保留密码；
- 不使用 `B0-V5` 或测试库连接串替代生产值；
- 不在未验证备份时执行回滚。
