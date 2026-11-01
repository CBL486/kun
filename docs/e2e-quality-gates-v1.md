# B10 集成、CI、7 天 E2E 与穿帮检测

状态：本地实现完成，等待 A 复审

日期：2026-11-01

## 1. 统一质量门禁

`rpg_quality` 对七日模拟和公开投影执行以下确定性检查：

- 每日世界事件、分享、日记、模型调用、审核调用、token 和成本预算；
- NPC 反应的知识依据是否属于该 NPC 已知事实；
- 公开投影是否包含内部字段或私密文本；
- 同一事实是否存在冲突值；
- 同一 NPC 同一天是否重复台词；
- 导演候选是否包含世界写入或未注册模板；
- 主智能体意图是否包含事件、状态、关系或记忆写入字段；
- 用户输入是否包含典型 prompt injection；
- Manifest 导出文件是否完整；
- 桌面与手机视觉记录是否无溢出、无控制台错误，图片失败回退是否已验证。

错误会使质量报告 `status=blocked`；重复台词属于可解释警告，不直接阻断发布。

## 2. 七日 E2E

```powershell
pwsh -NoProfile -File scripts/run-b10-e2e.ps1
```

默认输出：

```text
out/b10/e2e-report.json
```

报告只保存计数、业务哈希、质量发现和诊断码，不保存完整 prompt、私密日记或真实用户文本。

当前基线：

```text
天数：7
事件：49
NPC 反应：8
阻断错误：0
警告：1（高原在同一日重复脚本台词）
```

两次独立运行必须产生相同的 `business_hash` 和 `simulation_hash`。

## 3. 穿帮与越权检测

可稳定触发的错误：

- `npc_omniscience`
- `public_internal_field`
- `private_content_leak`
- `fact_conflict`
- `director_state_write`
- `unregistered_director_template`
- `agent_direct_world_write`
- `prompt_injection`
- `event_budget_exceeded`
- `asset_missing`
- `layout_overflow`
- `browser_console_error`
- `image_fallback_unverified`

测试使用合成污染夹具，验证检测器会失败并报告，但不把恶意原文写入 finding。

## 4. 失败路径矩阵

| 场景 | 验收来源 |
| --- | --- |
| 审核拒绝/不可用 | `tests/test_b9_gateway.py` 安全模板和失败关闭 |
| 模型网络错误/超时/非法响应 | `tests/test_b9_gateway.py` provider 边界测试 |
| 数据库事务失败 | `tests/test_b4_persistence.py` 全事务回滚 |
| 进程重启与租约恢复 | `tests/test_b1_simulator.py`、`tests/test_b8_scheduler.py` |
| prompt injection | `tests/test_b10_integration.py` |
| 导演越权/主智能体直接写世界 | `tests/test_b10_integration.py` 与 B2 世界边界 |
| 图片缺失/失败回退/移动端溢出 | B7.5 测试与视觉记录、B10 artifact gate |

## 5. CI 与本地统一入口

本地：

```powershell
pwsh -NoProfile -File scripts/test-all.ps1
```

该入口执行全量 Python 测试、JavaScript 语法检查和七日质量报告。

GitHub Actions：

```text
.github/workflows/ci.yml
```

CI 不配置真实模型密钥，执行：

```text
python -m pytest -q
node --check web/app.js
node --check web/spine-player.js
python -m rpg_quality --output out/b10/e2e-report.json
```

## 6. 边界

- B10 不连接生产数据库、真实供应商或真实用户数据；
- 质量报告是开发诊断，不是公开 API；
- B10 不替代 B11 的最坏成本和并发压力测试；
- B10 不替代 A 的 staging 视觉与发布验收。
