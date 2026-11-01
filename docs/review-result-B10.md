# B10 集成、CI、E2E 与穿帮检测评审结果

评审人：Agent A

评审日期：2026-11-01

分支：`codex/bx-b10-integration`

实现提交：`26f6551c87f6a543f946752e442d779dd83c2987`

最终交接提交：`5c3b4ce508c8c6ce11357e84e9dffd0774d1df58`

## 1. 结论

结论：**通过，允许进入 B11。**

B10 已提供统一质量门禁、7 天可复现 E2E、GitHub Actions CI、穿帮与越权检测，
并在无真实模型密钥的干净副本中通过全部测试。

未发现功能或安全阻断项。发现一项不影响运行结果的 P2 文档修正：
当前唯一重复台词警告属于 `npc_gu`（顾言），但 B10 交接和质量规范误写成高原。

## 2. 独立验证

验证基线：

```text
分支：codex/bx-b10-integration
最终提交：5c3b4ce
环境：无真实 LLM Key
测试位置：从提交创建的干净 clone
```

实际结果：

```text
151 passed, 1 warning in 22.38s
7-day E2E: passed
events: 49
quality errors: 0
quality warnings: 1
```

唯一警告是：

```text
Starlette/httpx TestClient deprecation
```

不影响 B10 功能和安全边界。

## 3. 7 天 E2E 复现

独立运行两次：

```text
status_a = passed
status_b = passed
business_equal = true
simulation_equal = true
```

业务哈希：

```text
145ce4a53180494191262033205db8c3a49a9541d1f18b1e6589018a118e2f18
```

模拟与质量组合哈希：

```text
9ed818bbe4d63ee2b4615a34f81346910914ffb5a05f2599356c53a89f0d0e1b
```

机器可读报告：

```text
docs/e2e-7day-summary.json
```

## 4. 质量门禁检查

已实际确认：

- 每日事件、分享、日记、模型调用、审核调用、token 和成本预算；
- NPC 知识依据不超过个人已知事实；
- 公开投影没有内部字段；
- 公开 API 不暴露 tick、prompt、action score、完整私密记忆或数据库字段；
- 事实冲突可稳定触发 error；
- 重复台词可稳定触发 warning；
- 导演包含世界写入或未注册模板会失败；
- 主智能体意图包含事件、关系、状态或记忆写入字段会失败；
- prompt injection 会报告且不回显恶意原文；
- Manifest 导出文件缺失会阻断；
- 移动布局、浏览器控制台和图片失败回退使用 B7.5 已验证记录检查。

合成污染夹具均能稳定失败并生成脱敏 finding。

## 5. 失败路径覆盖

| 场景 | 验证位置 | 结论 |
| --- | --- | --- |
| 审核拒绝/不可用 | B9 gateway tests | 通过 |
| 模型网络错误、超时、非法响应 | B9 provider/gateway tests | 通过 |
| 数据库事务失败 | B4 persistence tests | 通过 |
| 进程重启与租约恢复 | B1/B8 tests | 通过 |
| Prompt injection | B10 integration tests | 通过 |
| 导演越权/主智能体直接写世界 | B10/B2 tests | 通过 |
| 美术缺失与移动布局记录 | B7.5 + B10 artifact gates | 通过 |

## 6. CI 检查

`.github/workflows/ci.yml` 在无真实密钥条件下执行：

```text
python -m pytest -q
node --check web/app.js
node --check web/spine-player.js
python -m rpg_quality --output out/b10/e2e-report.json
```

环境显式设置：

```text
AIWORLD_LLM_API_KEY=""
```

未发现真实 API Key、Token、私钥或生产数据库凭据。

## 7. 非阻断问题

### P2：重复台词角色名称写错

质量报告实际 finding：

```text
npc_gu:2026-11-05 同一 NPC 同日重复台词 2 次
```

`npc_gu` 对应顾言，但 `docs/handoff-B10.md` 和
`docs/e2e-quality-gates-v1.md` 将其写成了高原。

影响：仅文档表述错误，不影响质量检测、测试结果或业务数据。

处理：在 A 合并前或 B11 收尾时修正为“顾言”。该问题不阻塞 B11。

## 8. 接受的有意限制

- 当前重复台词属于 warning，不直接阻断发布；
- B10 使用 B7.5 已验收的视觉记录检查图片回退和移动布局，不重复执行浏览器截图；
- B10 不覆盖 B11 要求的最坏成本、并发压力和长对话场景；
- 不连接生产数据库、真实模型供应商或真实用户数据；
- 不执行服务器、DNS、TLS、防火墙或部署操作。

## 9. 放行决定

```text
B10 评审：PASS
允许合并 codex/bx-b10-integration
允许进入 B11 安全、失败与成本压力测试
```

B11 应继续修正重复台词文档表述，并重点验证最坏调用、并发、限流、熔断、
长对话、队列积压和异常恢复。
