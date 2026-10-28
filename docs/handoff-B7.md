# B7 最小 RPG Web 交接

状态：本地实现完成，等待 A 验收

批次：B7

日期：2026-10-28

分支：`codex/bx-b7-web`

## 1. 实现范围

B7 提供：

- 观察者视角首页；
- 六地点小镇地图；
- 主智能体角色卡和关系标签；
- 公开事件/分享时间线；
- 受审核观察者留言；
- 日记安全摘要；
- 记忆安全摘要和类型筛选；
- 设置占位页；
- 桌面侧栏和手机底部导航；
- 加载、空状态、网络失败和审核失败界面；
- B7.5 占位图、组件边界和素材替换说明；
- FastAPI 同源静态 Web 托管。

B7 未接入正式美术，未连接生产数据库或真实模型。

## 2. 代码结构

```text
web/
  index.html
  styles.css
  app.js
  assets/placeholders/
    town-map.svg
    avatar.svg
    event.svg
app/main.py
tests/test_b7_web.py
scripts/
  run-b7-web.ps1
  test-b7.ps1
docs/
  web-ux-spec.md
  screenshots/b7-desktop.png
  screenshots/b7-mobile.png
```

## 3. 运行

```powershell
pwsh -NoProfile -File scripts/run-b7-web.ps1
```

打开 `http://127.0.0.1:8080/`。

测试：

```powershell
pwsh -NoProfile -File scripts/test-b7.ps1
```

## 4. 验收结果

当前结果：

```text
B1-B6：92 项通过
B7：9 项通过
合计：101 项通过
```

浏览器实测：

- 桌面 1440×1000 截图正常；
- 手机 390×844 截图正常，`scrollWidth=390`；
- 地图、角色、时间线、留言、日记、记忆、设置七视图均可切换；
- 留言提交成功并显示排队回复；
- 网络失败横幅可触发；
- 浏览器控制台无错误；
- `node --check web/app.js` 通过。

视觉证据：

- `docs/screenshots/b7-desktop.png`
- `docs/screenshots/b7-mobile.png`

## 5. 数据与安全边界

- 所有数据来自 B6 mock API；
- 未使用真实密钥；
- 留言仍只排队，不创建世界事件；
- 不展示 tick、prompt、action、score、完整私有记忆；
- 动态文本使用 `textContent`；
- 不依赖 CDN、外部字体或第三方前端运行时；
- 图片加载失败不会使页面空白。

## 6. 已知限制

- 当前为功能性视觉，正式素材和视觉验收属于 B7.5；
- 留言只保存在 B6 进程内，持久化属于 B8；
- 时间线一次请求最多显示公开 API 返回的 50 项；
- 尚无账户、主题切换和完整设置；
- 未执行生产 Web 部署、反向代理、DNS 或 TLS 操作。

## 7. 交接字段

```text
任务 ID：B7 最小 RPG Web
分支：codex/bx-b7-web
提交哈希：待提交后回填
改动文件：web/、app/main.py、tests/test_b7_web.py、scripts/test-b7.ps1、scripts/run-b7-web.ps1、docs/web-ux-spec.md、docs/screenshots/、README.md、docs/handoff-B7.md
测试命令：pwsh -NoProfile -File scripts/test-b7.ps1
测试结果：B1-B6 92 项、B7 9 项，合计 101 项通过
seed / mock：20261028；B6 mock API；无真实密钥
素材许可证：仅项目内原创 SVG 占位图，无第三方付费素材
已知风险：留言持久化、正式美术和真实供应商分别由 B8/B7.5/B9 接入
需要 A 合并的文件：本分支 Web、静态占位资源、测试和手交接记录
需要 A 在服务器执行的动作：无；B7 仅本地交付
```
