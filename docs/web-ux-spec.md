# B7 最小 RPG Web 观察者界面

状态：已通过 A 验收

日期：2026-10-28

## 1. 观察者闭环

页面必须支持：

```text
小镇此刻
  -> 角色卡
  -> 公开时间线
  -> 审核留言
  -> 日记摘要
  -> 记忆摘要
  -> 返回小镇
```

观察者不能提交动作、事件、关系数值或状态补丁。

## 2. 页面结构

| 视图 | 内容 |
| --- | --- |
| 小镇地图 | 六个公开地点、开放状态、当前地点、在场人员和主角色预览 |
| 角色卡 | 林澄的身份、当前地点、心情、目标和四名 NPC 关系标签 |
| 公开时间线 | 公开事件与放学分享，按时间倒序 |
| 观察留言 | 1–280 字留言、审核状态、排队反馈和安全回复 |
| 日记摘要 | 只展示安全摘要，不展示完整私密内容 |
| 记忆摘要 | 经历、回顾、关系、偏好摘要，可筛选和扩展 |
| 设置 | B7.5 视觉与无障碍选项占位 |

## 3. 桌面布局

- 左侧固定导航栏；
- 主内容区最大宽度 `1440px`；
- 地图与角色预览采用双列；
- 时间线采用日期、节点和正文三列；
- 截图：`docs/screenshots/b7-desktop.png`。

## 4. 手机布局

- 顶部品牌与观察者标签分两行；
- 所有主视图单列；
- 底部固定七项导航；
- 地图地点卡单列；
- 最大宽度 `760px` 启用移动布局；
- 390px 视口无横向溢出；
- 截图：`docs/screenshots/b7-mobile.png`。

## 5. 状态处理

- 初次加载：骨架占位；
- 空时间线、空日记、空记忆：说明性空状态；
- 网络失败：全局错误横幅与重试按钮；
- 审核失败：留言区内安全错误提示；
- 图片失败：隐藏破损图片并保留文字与首字占位；
- 减少动态：遵守 `prefers-reduced-motion`。

## 6. 可访问性

- `lang="zh-CN"`；
- 跳过导航链接；
- 键盘焦点样式；
- 导航按钮显示 `aria-current`；
- 聊天与状态区域使用 `aria-live`；
- 所有图标和占位图有可访问文本或明确装饰属性；
- 颜色不作为唯一状态提示，开放/关闭同时显示文字。

## 7. B7.5 素材接口

以下组件不绑定具体正式图片：

```text
.map-art
.portrait
.location-card
.timeline-item
.memory-card
.nav-mark
```

占位资源：

```text
web/assets/placeholders/town-map.svg
web/assets/placeholders/avatar.svg
web/assets/placeholders/event.svg
```

B7.5 可以在保持 DOM 和字段不变的前提下替换 WebP/PNG/SVG，并补充响应式图片尺寸。正式资源必须进入素材清单和许可证审计。

## 8. 前端数据边界

前端只调用：

```text
/world
/agent
/timeline
/chat
/memory
```

不读取 tick、prompt、action、score、完整记忆、数据库或密钥字段。动态文本全部通过 `textContent` 写入，不使用 `innerHTML`。

## 9. 本地运行

```powershell
pwsh -NoProfile -File scripts/run-b7-web.ps1
```

打开：

```text
http://127.0.0.1:8080/
```
