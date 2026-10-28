# 青禾镇 RPG 世界 MVP

当前完成 B1 的确定性七日规则模拟。B1 不连接服务器、真实模型或生产数据。

## 运行

在仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1
```

如果已经安装 Python，也可以直接运行：

```powershell
python -m rpg_sim seven-day --scenario slice-seven-day-v1 --seed 20261028 --mode rule_only --frozen-clock --output out/b1
```

输出包括：

- `run.json`：完整结构化报告和必需证据字段；
- `snapshot-before.json`、`snapshot-after.json`：初始与最终世界快照；
- `replay-manifest.json`：业务快照与重放哈希；
- `checkpoint.json`：可在重启后继续的原子检查点；
- `summary.md`：终端摘要副本。

暂停与继续：

```powershell
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1-checkpoint -PauseAfter 12
pwsh -NoProfile -File scripts/run-b1.ps1 -Output out/b1-checkpoint -Resume
```

首次验证暂停链路时，从新的输出目录开始执行第一条；恢复完成后，`business_result` 应与不中断运行一致。

## 测试

```powershell
pwsh -NoProfile -File scripts/test-b1.ps1
```

B1 契约说明见 [docs/handoff-B1.md](docs/handoff-B1.md)。
