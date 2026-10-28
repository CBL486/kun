# B0 V5 评审结果

评审人：Agent A

评审日期：2026-10-28

结论：**通过，G1 已冻结**

评审基线：`eda1d3c31e6386e286e361eafb9a00408d4cf71d`

B 修复分支：`codex/bx-b0-v5-contracts-fix`

B 修复提交：`a4c11a62f515f22e9be52e5d0224293a7dd8dd8e`

B 交接回填提交：`a9eebab30f1db0d37d8bd501b2f4968d617ce69e`

## 1. 冻结范围

接受以下文件作为 G1 契约基线：

- `docs/rpg-world-ontology-v1.md`
- `docs/agent-loop-v1.md`
- `docs/npc-script-runtime-v1.md`
- `docs/director-events-v1.md`
- `docs/mvp-actions-v1.md`
- `docs/mvp-slice-scenarios.md`
- `docs/rpg-mvp-risks.md`
- `docs/adr-memory-core.md`
- `docs/rpg-b0-index.md`
- `docs/review-request-B0-V5.md`
- `docs/handoff-B0-V5.md`
- `scripts/check-b0-v5.ps1`

## 2. G1 决定

| 编号 | 决定 |
| --- | --- |
| G1-01 | ADR-001、ADR-002 和上级 V4 由 A 带入整合基线并在本分支复核；B 不声称读过 |
| G1-02 | 接受观察、留言、公开事件反应和请求下一合法 slot 回应的有限影响 |
| G1-03 | 接受主智能体 19 岁、全部 NPC 18 岁以上；禁止涉及未成年角色的性内容 |
| G1-04 | 接受每日 6 个世界事件、8 次模型调用、24k 输入、6k 输出和 0.10 元作为 B1 硬上限 |
| G1-05 | 接受同一事务优先，允许待投影记录与幂等核对作为降级 |
| G1-06 | MVP 仅使用原创或已授权课程摘要；B3 提供来源和 `rights_status` |
| G1-07 | 接受 B1 用结构化终端报告和确定性快照验收，Web 推迟到 B6 |
| G1-08 | 允许 B1 开始；B5 前必须冻结 `/world`、`/agent`、`/timeline`、`/chat`、`/memory` 公开投影 |

## 3. A 整合时完成的修正

- 将 B0 文件统一到仓库根 `docs/` 和 `scripts/`。
- 删除旧的 `B0-V5/` 包装目录。
- 移除本体契约中无对应文件的旧 V2 引用。
- 将七份核心契约、记忆 ADR 和索引状态更新为 G1 已冻结。
- 保留 B 的真实修复分支和提交信息。
- 带入 A 侧 ADR-001、ADR-002、V4 任务书及服务器文档。

## 4. 静态检查

```text
B0 V5 静态契约检查通过
必需文档：7
允许动作：9
脚本 NPC：4
地点：6
导演模板：12
七天日期：7
```

## 5. 允许的下一批

允许 B 开始 **B1 单镇模拟器**。

B1 必须：

- 不登录服务器；
- 不接触生产数据库、生产密钥或真实用户数据；
- 使用固定 seed、mock LLM、mock 审核器和本地 SQLite；
- 按 V5 的 B1 验收标准交付结构化终端报告和确定性快照；
- 完成后提交独立分支和交接记录，等待 A 合并。
