# R8 受控媒体观察 V1

状态：待 R8 审查

日期：2026-11-07

## 1. 支持范围

- 用户明确提供的 B站/抖音公开视频链接；
- B站公开热门列表中的新视频；
- 只读取公开标题、简介和封面 URL 引用；
- 不读取登录内容、会员内容、地区限制内容或 DRM 内容；
- 不自动点赞、评论、关注、私信或投币。

## 2. URL 安全

- 只接受 `https`；
- 平台必须匹配 B站/抖音白名单；
- 禁止 URL 用户名/密码和异常端口；
- 禁止 `/login`、`/member`、`/space` 等非视频入口；
- HTTP 重定向后的最终 URL 再次校验；
- 单页最大 512 KB；
- 请求头不包含 Authorization 或 Cookie。

## 3. 数据流

```text
公开 URL / B站热门
  -> URL hash 去重
  -> 每日上限
  -> 公开元数据读取
  -> 元数据审核
  -> 短摘要生成
  -> 摘要审核
  -> media_observations
  -> private memory_event
  -> 小幅度 curiosity 变化
```

任何一步失败都只记录 blocked/failed，不写 memory event。

## 4. 配额与隐私

```text
默认每日观察上限：2
单次摘要 token budget：600
同一 URL 重放：返回原 observation
```

`media_observations` 只保存 URL hash。完整视频、字幕媒体、账号 Cookie 和登录态
不进入仓库或数据库；只保存摘要、公开元数据引用和感受。

## 5. 验证

```text
fake provider / fixture：通过
URL 白名单和重定向拒绝：通过
无 Authorization/Cookie 请求头：通过
每日上限、重复 URL 去重：通过
审核/provider 失败不写事件：通过
超预算静态回退、B站热门选择：通过
```
