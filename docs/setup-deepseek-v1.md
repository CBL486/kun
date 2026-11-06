# DeepSeek 启动配置 V1

状态：R3 待 Gate 1 审查

日期：2026-11-06

## 1. 启动流程

```text
首次访问 /
  -> 启动设置页
  -> 输入 DeepSeek Key
  -> 可选“仅校验”
  -> 保存（服务端再校验一次）
  -> 选择默认人设或填写自定义人设
  -> 进入青禾镇
```

已配置且 `world_ready=true` 时，`/` 返回观察者主页面。`GET /setup` 始终可访问，
用于替换或清除 Key。

## 2. API

```text
GET  /api/setup/status
POST /api/setup/deepseek/validate
POST /api/setup/deepseek/save
POST /api/setup/complete
POST /api/setup/deepseek/clear
```

`validate` 不保存；`save` 先校验再原子写入。`complete` 在没有 Key 时返回
`409 deepseek_not_configured`，没有人设时返回 `409 persona_not_configured`。

稳定错误码：

```text
invalid_deepseek_key
deepseek_auth_failed
deepseek_quota_unavailable
deepseek_timeout
deepseek_network_error
deepseek_unavailable
deepseek_invalid_response
deepseek_not_configured
setup_lock_busy
setup_acl_failed
```

错误响应不回显 Key 或供应商原始响应。

## 3. 存储和权限

- 默认目录为 `data/setup/`，已加入 Git 忽略规则；
- Key 文件为 `deepseek_api_key.txt`；
- 非秘密状态保存为 `setup_state.json`，只包含掩码、provider 和流程状态；
- 文件通过临时文件加原子替换写入；
- `.setup.lock` 提供单实例写入锁，超过 30 秒的陈旧锁可回收；
- Windows 默认在首次保存前使用 `icacls` 移除继承权限，仅授权当前服务账户、
  `SYSTEM` 和 `Administrators`；
- ACL 设置失败时停止保存并返回 `setup_acl_failed`；
- 清除 Key 不删除角色、关系、世界或 Persona 状态。

## 4. 浏览器边界

- 输入框使用 `type=password` 和 `autocomplete=off`；
- 提交后立即清空输入框；
- 不使用 `localStorage`、`sessionStorage`、cookie、URL 或前端日志；
- 不回显完整 Key，只显示 `sk-...ABCD` 形式掩码；
- 正常页面展示当前为本地/测试模式，未假装公网 HTTPS 已配置。

## 5. 验证

```text
pytest：194 passed, 1 warning
Edge 1440×1000：无横向溢出，控制台无错误
Edge 390×844：无横向溢出，控制台无错误
浏览器 localStorage/sessionStorage/cookie：空
```

截图：

```text
docs/screenshots/r3-setup-desktop.png
docs/screenshots/r3-setup-tutorial.png
docs/screenshots/r3-setup-mobile.png
```

## 6. 已知限制

- R4 已将占位完成状态替换为真实 PersonaBaseline；
- R3 分支尚未与 R1 的观察者 Web 合并；
- 生产反向代理必须额外拒绝外部访问 `/api/setup/*` 和 `/setup`，或由 A 配置
  管理员鉴权；
- 真实 DeepSeek 校验只在手动 smoke 中使用，CI 全部使用 fake client。
