# R5 连续记忆、关系、情绪与 Schema 5 交接

状态：待 Gate 2 审查

日期：2026-11-07

分支：`codex/product-r5-memory-affection`

基线：`4941b9d04b27b70c29e6d6cc016819d77f7c9cca`

## 1. 交付

- schema 从 4 升级为 5；
- 新增记忆事件、关系、情绪、Persona baseline/state/change log、学习、媒体观察、
  setup、credential reference 和世界时钟表；
- Persona 生产运行时从 JSON 切到 schema-5 SQLite/PostgreSQL；
- 旧 `persona.json` 和 `setup_state.json` 的一次性导入命令；
- 事件/关系/情绪写入必须引用正式事件；
- 关系重放和事件去重；
- 持久世界时钟；
- 10 分钟后台 tick 和 Windows 任务；
- 24 小时内压缩追赶、超过 24 小时摘要跳转；
- release 外部生产数据目录；
- schema 5 Windows ACL 使用 SID；
- 设置路由代理保护；
- 默认 Persona 安全边界移入系统策略。

## 2. QQ 参考采用与拒绝

采用：

- 事件优先、摘要索引、重要性和情绪权重召回；
- 多维关系；
- SelfState 到 PersonaState/EmotionState 的拆分；
- 私有心流和低频自主活动边界。

拒绝：

- QQ 协议端、NapCat、消息分条、表情、语音；
- QQ/AI School 共用租户；
- 提示词原文、真实用户数据、真实 Key；
- 自动社交互动。

## 3. 世界时钟

```text
时区：Asia/Shanghai
tick：10 分钟
<=24h：压缩为最多 144 个行动 tick
>24h：记录离线摘要并跳到当前时间
模型调用：0
```

`AIWorld-WorldTick` 已加入 Windows 任务模板，但 B 不注册生产任务。

## 4. 生产配置和代理

生产数据目录：

```text
C:\AIWorld\data\setup
C:\AIWorld\data\persona
C:\AIWorld\data\world
```

`deploy/windows/production.env.example` 明确使用这些 release 外部路径。

Nginx/Caddy：

- `/setup`
- `/api/setup/*`
- `/api/persona/*`

仅允许本机/管理员网段，普通观察者 403，全部 `no-store`。

## 5. 测试

```text
pytest：224 passed, 1 warning
SQLite schema 5：通过
PostgreSQL schema 5：通过
旧 Persona JSON 导入和重复导入：通过
relationship/emotion 事件依据：通过
world clock 有界追赶：通过
Windows ACL SID 实机分支：通过
proxy template：通过
release 不含 data/logs/backups：通过
```

## 6. 已知风险

- 世界时钟已经持久化，但自主行动决策仍待 R7 接入；
- A 必须在生产候选上执行 schema 5、JSON 导入、tick 任务和 release 切换演练；
- 真实 DeepSeek smoke 仍只由 A 手动执行；
- 当前 Persona 安全策略只建立系统常量，R6 才会接入生成提示词链。

## 7. 需要 A 做

1. 审查 schema 5 字段、约束、迁移和回滚；
2. 在隔离 PostgreSQL 执行 JSON 导入与重复导入；
3. 注册 `AIWorld-WorldTick` 并验证 10 分钟节奏；
4. 验证 `/setup`、`/api/setup/*`、`/api/persona/*` 的代理拒绝规则；
5. Gate 2 通过前不开始 R6/R7/R8。
