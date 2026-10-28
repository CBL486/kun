# ADR-002：MVP 运行时与数据栈

日期：2026-10-27
状态：已采纳
关联：ADR-001、任务书 V4

## 背景

服务器运行 Windows 10 Enterprise 2016 LTSB，4 vCPU、约 5 GB 内存，没有 Docker、PostgreSQL 或 Redis。Python 3.12.10 已安装在 `C:\AIWorld\runtime\Python312`。

项目首版只有一个主智能体，不采用多智能体常驻循环。需要选择与当前服务器匹配的数据栈和任务调度方案。

## 决策

### PostgreSQL

服务器使用 `embedded-postgres` Python 包提供的 PostgreSQL 18.6 Windows amd64 二进制，数据目录规划为：

```text
C:\AIWorld\data\postgres
```

这样不依赖系统级 PostgreSQL 安装，也不需要 Docker。生产部署前仍需补充：

- 启动与停止脚本。
- 开机启动方式。
- 独立数据库账号。
- 每日备份与恢复演练。

### Redis

首版不部署 Redis。原因：

- 官方 Redis 不支持 Windows。
- 第三方 Windows 移植版版本较旧，不适合作为长期基础设施。
- 首版是单主智能体、低频离散事件，不需要高吞吐队列。

首版使用：

- PostgreSQL 作为持久化状态和任务表。
- APScheduler 作为进程内定时调度器。
- PostgreSQL advisory lock 或任务幂等键避免重复执行。

当达到多进程、多实例或明显任务积压时，再迁移到托管 Redis 或其他队列。

### SQLite

B 在本地开发和测试中使用 SQLite；A 在服务器使用 PostgreSQL。两端共享同一份契约测试，避免本地可跑、线上行为不同。

### 进程

首版使用 Python 进程运行 FastAPI 和调度器。Windows 上使用任务计划程序或等价方式拉起进程，不使用 Docker 或 Windows 服务包装器。

## 结果

- 首版可以继续在当前服务器推进，不需要先解决 Redis Windows 兼容问题。
- PostgreSQL 作为唯一权威业务数据库。
- 任务调度与业务状态保持幂等。
- Redis 从硬依赖降为扩容选项。

## 实施状态（2026-10-28）

- PostgreSQL 18.6.3 已在 `C:\AIWorld\data\postgres` 初始化并运行于 `127.0.0.1:55432`。
- 业务库和账号为 `aiworld`，主机连接使用 `scram-sha-256`。
- PostgreSQL 由计划任务 `AIWorldPostgreSQL` 在系统启动时拉起。
- 每日 03:30 通过 `AIWorldPostgresBackup` 执行 dump 与全局对象备份，保留 14 天。
- 已完成备份到临时数据库的恢复验证。
- Redis 继续延期，不属于首版上线阻塞项。
