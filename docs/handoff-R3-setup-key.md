# R3 启动页、DeepSeek Key 与教程交接

状态：待 Gate 1 审查

日期：2026-11-06

分支：`codex/product-r3-setup-key`

基线：`848a73ac8efb80c92500b7e7a5d1b004a6aedf65`

## 1. 交付

- 首次访问的独立启动页 `/setup`；
- 未完成设置时 `/` 返回启动页，完成后返回世界页面；
- DeepSeek Key 状态的五个 API；
- 可关闭的问号教程；
- 仅校验与保存两条路径；
- 服务端私有目录、原子写入和单实例锁；
- Windows ACL 收紧，失败时阻断保存；
- Key 掩码、清除 Key 和替换流程；
- 本地/测试模式 HTTPS 提示。

## 2. 安全边界

- 完整 Key 不进入响应、日志、URL、cookie、`localStorage` 或
  `sessionStorage`；
- 浏览器输入框为 `type=password`、`autocomplete=off`，提交后立即清空；
- 状态文件只保存 provider、掩码和流程状态；
- 测试 Key 只使用 `sk-test-*`，校验器全部通过 fake client；
- 清除 Key 不自动清空世界、关系或人格。

## 3. 测试

```text
pwsh -NoProfile -File scripts/test-b6.ps1
194 passed, 1 warning
```

`tests/test_r3_setup.py` 覆盖：

- 私有 Key 持久化和重启读取；
- Key 掩码不含完整 Key；
- 首次访问门禁和完成后进入世界；
- 清除 Key 后重新门禁；
- Key 格式、鉴权、额度、超时、网络和非法响应错误；
- 写入锁冲突；
- 浏览器不使用凭据存储。

## 4. 浏览器证据

使用 Edge 无头浏览器：

```text
桌面 1440×1000：无横向溢出
手机 390×844：无横向溢出
localStorage=[]，sessionStorage=[]，cookie=""
Key 输入类型=password，autocomplete=off
控制台错误=[]
```

截图：

```text
docs/screenshots/r3-setup-desktop.png
docs/screenshots/r3-setup-tutorial.png
docs/screenshots/r3-setup-mobile.png
```

复现脚本：`scripts/capture-r3-evidence.js`。

## 5. 已知风险

- 启动页当前将“默认人设”标记为完成；实际 PersonaBaseline 由 R4 替换；
- 该分支从 Gate 0 主线独立开发，尚未合并 R1，两个前端需在 Gate 1 集成；
- 生产代理必须阻止外部访问 `/setup` 和 `/api/setup/*`，或在部署层增加管理员
  鉴权；
- 真实 DeepSeek Key 校验不属于 CI，只允许 A 在隔离环境手动 smoke。

## 6. 需要 A 做

1. 审查 Key 存储路径、ACL 失败关闭和启动门禁；
2. 与 R4 合并后验证 Persona 使用真实配置，而非占位 `persona_configured`；
3. 在代理模板中确认 `/api/setup/*` 不暴露给普通观察者。
