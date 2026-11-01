# B10 集成、CI、E2E 与穿帮检测交接

状态：本地实现完成，等待 A 复审

日期：2026-11-01

分支：`codex/bx-b10-integration`

## 1. 实现范围

- 七日 E2E 可复现摘要；
- 统一质量门禁；
- NPC 知识越界检测；
- 公开字段和私密内容泄漏检测；
- 事实冲突与重复台词检测；
- 导演越权和主智能体直接写世界检测；
- prompt injection 检测；
- 资源和移动布局质量检查；
- GitHub Actions CI；
- 本地统一测试入口。

## 2. 代码结构

```text
rpg_quality/
  models.py      质量发现和报告
  detectors.py   穿帮、越权、预算和资源检查
  e2e.py         七日集成摘要
  __main__.py    E2E CLI
tests/test_b10_integration.py
scripts/
  run-b10-e2e.ps1
  test-b10.ps1
  test-all.ps1
.github/workflows/ci.yml
docs/e2e-7day-summary.json
docs/e2e-quality-gates-v1.md
```

## 3. 验收结果

```text
151 passed, 1 warning
7-day E2E: passed
events: 49
errors: 0
warnings: 1
```

唯一警告是顾言在同一日重复使用同一条脚本台词。该警告被质量报告稳定捕获，
不影响当前发布门禁；后续内容批次可替换为不同模板。

两次 E2E 的业务哈希和模拟哈希一致：

```text
business_hash: 145ce4a53180494191262033205db8c3a49a9541d1f18b1e6589018a118e2f18
```

## 4. 失败与安全验证

- 审核失败、模型异常和非法响应由 B9 测试覆盖；
- 数据库事务失败由 B4 测试覆盖；
- 进程重启、任务租约和恢复由 B1/B8 测试覆盖；
- prompt injection、权限越界和穿帮由 B10 合成污染夹具覆盖；
- 资源缺失、图片回退和移动布局由资产检查与 B7.5 记录覆盖；
- CI 环境显式设置空 `AIWORLD_LLM_API_KEY`，不访问真实供应商。

## 5. 交接字段

```text
任务 ID：B10 集成、CI、E2E 与穿帮检测
分支：codex/bx-b10-integration
提交哈希：26f6551c87f6a543f946752e442d779dd83c2987
改动文件：rpg_quality/、tests/、scripts/、.github/workflows/ci.yml、docs/、README.md
实现摘要：7 天可复现 E2E、穿帮/越权/注入检测、资源与移动布局门禁及 CI。
测试命令：pwsh -NoProfile -File scripts/test-all.ps1
测试结果：151 项通过；7 天 E2E passed，0 errors，1 warning
seed / mock：20261028；rule/mock；无真实供应商密钥
已知风险：重复台词警告仍需内容层优化；B11 负责最坏成本和压力测试。
需要 A 合并的文件：本分支质量层、CI、测试、脚本和文档
需要 A 在服务器执行的动作：无
```
