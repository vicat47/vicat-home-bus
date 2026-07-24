# Proposal: HomeBus v0.1 MVP

## What

实现 HomeBus 的最小可行产品（MVP），涵盖 API Server、CLI、三个后端适配器（Grocy / Beancount / Homebox）、Saga 补偿引擎、以及路由注册表。当前所有 `homebus/` 和 `cli/` 下的 `.py` 文件均为空骨架占位，本变更将其全部实现为可工作的代码。

## Why

### 问题

家庭数字化管理涉及三个独立系统（Grocy 消耗品库存、Beancount 复式记账、Homebox 耐用品资产），当前 AI Agent 需要分别调用三个后端 API，存在以下问题：

| 问题 | 表现 |
|------|------|
| **无统一入口** | Agent 分别调用三个后端 API，耦合度高 |
| **无事务保障** | 发往多后端的操作没有原子性保障，部分成功部分失败无法自动修复 |
| **不可追溯** | Agent 调用不可审计，后端出了差异无法定位根因 |
| **重复执行** | Agent 重试可能导致同一操作被执行多次 |
| **后端对 Agent 不透明** | Agent 需要知道每个后端的地址、认证、数据格式 |

### 解决

HomeBus 作为位于 AI Agent 与三个后端之间的**单一写入入口 + 查询代理 + 事务协调器**，Agent 通过 CLI → HomeBus API 完成所有操作。

### MVP 核心原则

1. **单一入口** — Agent 只跟 CLI 交互，CLI → HomeBus API → 统一调度后端
2. **先写日志再执行** — 事件先 SQLite 持久化，再分发到后端
3. **先写日志再响应** — Agent 即时获得 `accepted` 确认，不等待后端完成
4. **补偿兜底** — 部分失败自动回滚（Saga），不留下脏数据
5. **查询也过总线** — 读操作也走 HomeBus，保持入口统一

## Scope

### In Scope

- **API Server** — FastAPI + uvicorn，4 个端点（POST /v1/events, GET /v1/events/{id}, POST /v1/query, GET /v1/health）
- **SQLite 数据库** — events 表 + executions 表，WAL 模式，迁移管理
- **事件校验器** — Pydantic Schema 校验 + event_id 幂等去重
- **调度引擎** — intent + items.category → 子任务推导（含 routing registry 查询）
- **任务执行器** — DAG 分层并发执行，超时 + 重试
- **Saga 补偿器** — 部分失败自动逆向操作
- **结果聚合器** — 集合执行结果，推导终态
- **3 个后端 Adapter** — Grocy / Beancount / Homebox，实现统一 `AdapterBase` 接口
- **Beancount 共享库** — 分录生成 + 文件 I/O + bean-check + git commit
- **路由注册表** — TOML 加载 + 品类路由 + 渠道路由查询
- **查询路由** — 查询代理到对应后端
- **CLI** — Click 实现，4 个命令（publish / status / query / health）+ 1 个管理命令（init）
- **配置管理** — TOML 配置 + 环境变量注入 + 分层加载
- **端到端测试** — pytest + 集成测试

### Out of Scope (推迟到后续版本)

| 功能 | 版本 |
|------|------|
| MCP Server | v0.2 |
| 观测面引擎 | v0.2 |
| Webhook 回调 | v0.2 |
| 调谐引擎 | v0.3 |
| 物化视图/缓存 | v0.4 |
| HA/n8n 集成 | v1.0 |

## Success Metrics

| 指标 | 目标 |
|------|------|
| 写入成功率 | >99%（排除后端宕机） |
| 补偿覆盖率 | 100%（可推导的失败场景） |
| 事件不丢失 | 0 例 |
| 查询响应时间 | <2s（非复杂查询） |

## Related Documents

- PRD: [doc/prd/homebus-v0.1.md](../../doc/prd/homebus-v0.1.md)
- Roadmap: [ROADMAP.md](../../ROADMAP.md)
- Memory: [MEMORY.md](../../MEMORY.md)
- All specs: [doc/specs/](../../doc/specs/)
