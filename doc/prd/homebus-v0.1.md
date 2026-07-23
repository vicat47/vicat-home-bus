---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["prd", "homebus", "mvp"]
related:
  c4-context: "../c4/context.md"
  c4-container: "../c4/container.md"
  c4-core: "../c4/component-core.md"
  c4-cli: "../c4/component-cli.md"
  specs: "../specs/homebus.md"
  glossary: "../glossary.md"
---

# PRD: HomeBus MVP — 家庭服务总线 v0.1

- **Version**: 0.1.0
- **Date**: 2026-07-20
- **Product Owner**: vicat47
- **Tech Lead**: vicat47
- **Status**: Draft

## Background

### 问题陈述

家庭数字化管理面临三大核心场景（记账、消耗品库存、耐用品资产管理），目前使用三个独立系统（Beancount、Grocy、Homebox）。用户需要经过 AI Agent 进行意图解析后，将操作分发到这三个后端。

当前的问题：

| 问题 | 表现 |
|------|------|
| **无统一入口** | Agent 分别调用三个后端 API，耦合度高 |
| **无事务保障** | 发往多后端的操作没有原子性保障，部分成功部分失败无法自动修复 |
| **不可追溯** | Agent 调用不可审计，后端出了差异无法定位根因 |
| **重复执行** | Agent 重试可能导致同一操作被执行多次 |
| **后端对 Agent 不透明** | Agent 需要知道每个后端的地址、认证、数据格式 |

### 解决方案

HomeBus 作为**单一写入入口 + 查询代理 + 事务协调器**，位于 Agent 与后端之间，接管所有的数据交互。

**MVP 核心原则：**

1. **单一入口**：Agent 只跟 CLI 交互，CLI 只跟 HomeBus API 交互，HomeBus 统一调度后端
2. **先写日志再执行**：保证事件不丢
3. **先写日志再响应**：保证 Agent 即时获得 accepted 确认
4. **补偿兜底**：部分失败自动回滚，不留下脏数据
5. **查询也过总线**：保持入口统一，Agent 不直连后端

## Goals

### Primary Goals

1. **建立一致的写入入口** — Agent 通过 CLI → HomeBus API 完成所有写操作，Agent 不再直接接触后端
2. **建立统一的查询代理** — Agent 通过 CLI → HomeBus API 完成所有读操作，HomeBus 路由到对应后端
3. **保障事务一致性** — 跨后端的操作要么全成功，要么自动补偿回滚
4. **保障事件可靠性** — 事件先持久化再返回确认，幂等去重防止重复执行
5. **保障操作可追溯** — 所有操作（读写）记录在不可变事件日志中

### Success Metrics

| 指标 | 目标 | 测量方式 |
|------|------|---------|
| 写入成功率 | >99%（排除后端宕机） | events 表 status=success 占比 |
| 补偿覆盖率 | 100%（可推导的失败场景） | 所有 sub_task failed 场景均有对应补偿操作 |
| 事件不丢失 | 0 例 | 日志与实际后端状态调谐比对 |
| 查询响应时间 | <2s（非复杂查询） | 端到端 CLI 调用计时 |

## User Stories

### US-1: 提交购买事件

**As a** AI Agent,
**I want** 向 HomeBus 提交一个购买事件（含物品清单和金额），
**so that** HomeBus 自动完成各后端的写入（Grocy 加库存 / Beancount 记账 / Homebox 创建资产）。

**Acceptance Criteria:**

- [ ] CLI 提供 `homebus publish` 命令，接受 `--intent`、`--items`、`--total-price` 参数
- [ ] HomeBus API 校验事件格式，格式非法返回 400 + 错误详情
- [ ] HomeBus 先写入 events 表持久化，再返回 `{event_id, status: "accepted"}`
- [ ] 调度引擎根据 intent + items.category 推导子任务并分发
- [ ] 并行子任务同时执行，串行子任务按序执行
- [ ] 返回最终状态（success / compensated）

### US-2: 查询事件状态

**As a** AI Agent,
**I want** 通过 event_id 查询事件的执行状态，
**so that** 我知道事件是否已完成、哪些成功了、哪些失败了。

**Acceptance Criteria:**

- [ ] CLI 提供 `homebus status --event-id <id>` 命令
- [ ] 返回 `{event_id, status, executions[]}` — 每个 execution 含 service、action、status、detail
- [ ] 支持 `--watch` 选项，持续轮询直到事件终态

### US-3: 查询后端状态

**As a** AI Agent,
**I want** 通过 HomeBus 查询 Grocy/Beancount/Homebox 的状态（如库存余量、账户余额），
**so that** 我不需要直接调用后端 API，保持入口统一。

**Acceptance Criteria:**

- [ ] CLI 提供 `homebus query --target <backend> --operation <op> --params <json>` 命令
- [ ] HomeBus 路由查询到对应后端，写入一条 intent=query 的事件日志
- [ ] 查询不创建 executions 表记录
- [ ] 后端不可达时返回友好错误，日志仍写入
- [ ] 日志记录查询内容和返回摘要

### US-4: 自动补偿

**As a** AI Agent,
**I want** 当部分后端写入失败时，HomeBus 自动撤销已成功的操作，
**so that** 不会留下"库存加了但账没记"之类的脏数据。

**Acceptance Criteria:**

- [ ] 子任务推导器按规则表生成正确的子任务清单
- [ ] 某个子任务失败后，Saga 补偿器自动推导补偿操作
- [ ] 补偿执行结果记录到 executions 表（标记为 compensation）
- [ ] 事件最终状态更新为 `compensated`
- [ ] Agent 轮询时可见补偿详情

### US-5: 健康检查

**As a** AI Agent / 系统管理员,
**I want** 调用 HomeBus 的健康检查接口，
**so that** 在操作前确认 HomeBus 和各后端是否可用。

**Acceptance Criteria:**

- [ ] CLI 提供 `homebus health` 命令
- [ ] 返回 `{status, adapters: {grocy: ok, beancount: ok, homebox: error}}`
- [ ] 各后端健康状态独立返回，不影响整体 API 响应

### US-6: 幂等性保障

**As a** AI Agent,
**I want** 同一个 event_id 重复提交时 HomeBus 自动去重，
**so that** Agent 超时重试不会导致重复执行。

**Acceptance Criteria:**

- [ ] Agent 可传入自定义 event_id（格式：`evt_<session>_<seq>`）
- [ ] 重复 event_id 返回已有的事件状态（不重新执行）
- [ ] 已有事件返回的 HTTP 状态码为 200（非错误）

## Scope

### In Scope (MVP)

| 功能 | 优先级 | 描述 |
|------|--------|------|
| HomeBus API Server (FastAPI) | P0 | 核心 HTTP 服务 |
| events 表 (SQLite) | P0 | 不可变事件日志 |
| executions 表 (SQLite) | P0 | 可变执行轨迹 |
| POST /v1/events | P0 | 写入入口（幂等） |
| GET /v1/events/{event_id} | P0 | 状态查询 |
| POST /v1/query | P0 | 查询代理入口 |
| GET /v1/health | P0 | 健康检查 |
| 调度引擎 (Dispatch Engine) | P0 | 子任务推导 + 分发 |
| 任务执行器 (Task Executor) | P0 | 并发/串行执行子任务 |
| Saga 补偿器 | P0 | 部分失败自动补偿 |
| 结果聚合器 | P0 | 集合执行结果，推导终态 |
| 事件校验器 | P0 | Schema 校验 + 幂等检查 |
| Grocy Adapter | P0 | 消耗品库存操作 |
| Beancount Adapter | P0 | 记账操作 |
| Homebox Adapter | P0 | 资产操作 |
| 查询路由 | P0 | 路由查询到对应后端 |
| 路由注册表 | P0 | TOML 配置加载 + 品类/渠道路由查询（供 Dispatch 使用） |
| HomeBus CLI | P0 | Click 命令行，4 个命令 |
| 事件/查询日志 | P0 | 所有操作写入 events 表 |

### Out of Scope (MVP)

| 功能 | 规划阶段 | 原因 |
|------|---------|------|
| HomeBus MCP Server | v0.2 | CLI 先行，MCP 后加 |
| 观测面引擎 (Observation Engine) | v0.2 | MVP 查询直连后端即可，语义聚合后加 |
| 调谐引擎 (Reconciliation) | v0.3 | MVP 不做定期对账 |
| Webhook 回调 | v0.2 | MVP 用轮询 |
| 降级模式 | v0.3 | MVP 假定后端可用 |
| 多用户/权限 | v0.4 | MVP 为单用户家庭 |
| Agent Memory 机制 | 外部系统 | HomeBus 无状态，memory 归 Agent |
| CQRS 物化视图 | v0.4 | MVP 查询直连后端 |
| 灰度/AB 测试 | v0.4+ | 非 MVP 考量 |
| HA 集成 | v1.0 | 未来规划 |
| n8n 集成 | v1.0 | 未来规划 |

## User Experience

### Agent 工作流 (MVP)

```
Agent 收到用户输入 → 意图解析 + 实体提取
         │
         ▼
    terminal("homebus publish --intent purchase --items ... --total-price 180")
         │
         ▼
    解析 CLI 返回的 JSON → 判断 status
         │
         ├→ "accepted" → 轮询 GET /v1/events/{event_id}
         │                 ├→ success → 告诉用户"已登记"
         │                 ├→ compensated → 告诉用户"部分失败已回滚"
         │                 └→ pending → 继续轮询
         │
         ├→ exit_code != 0 → 解析错误，修正后重试
         │
         └→ 超时 → 用同一 event_id 重试（幂等）
```

### CLI 交互体验

```bash
# 成功
$ homebus publish --intent purchase --items '[{"name":"牛奶","quantity":3,"category":"consumable"}]' --total-price 60
{"event_id": "evt_sess1_001", "status": "accepted", "message": "事件已接收"}

# Agent 确认执行完成
$ homebus status --event-id evt_sess1_001 --watch
{"event_id": "evt_sess1_001", "status": "success", "executions": [{"service": "grocy", "status": "success"}, {"service": "beancount", "status": "success"}]}

# 查询
$ homebus query --target grocy --operation stock_level --params '{"item":"牛奶"}'
{"data": {"name": "牛奶", "stock": 50, "unit": "盒"}, "event_id": "evt_q_002"}

# 健康检查
$ homebus health
{"status": "healthy", "adapters": {"grocy": "ok", "beancount": "ok", "homebox": "ok"}}
```

## 设计决策

### Decision 1: 写查询都走 HomeBus

读操作（查询）也经过 HomeBus 总线，而不是直连后端。

**理由：**
- 保持单一入口原则完整
- 查询日志可追溯
- Agent 不需要知道后端的地址和认证
- 未来可在 HomeBus 层做查询的缓存/聚合

**影响：**
- 查询接口走 POST（而非 GET），以便写入请求体传递复杂参数
- 查询写入 events 表，但不需要 executions 表

### Decision 2: CLI 先行

MVP 采用 Python Click CLI 作为 Agent 的调用入口，MCP Server 后加。

**理由：**
- 开发成本低，快速验证闭环
- Agent 通过 `terminal` 工具调用 CLI，CLI 自己进行参数校验
- 错误通过非零退出码 + stderr 传递，Agent 可自动修正重试
- MCP 可以在 v0.2 作为 CLI 的上层封装添加

### Decision 3: 先写后应答

HomeBus 先写 events 表再返回 accepted 响应。

**理由：**
- 保证事件不丢失（持久化后再确认）
- Agent 收到 accepted 后即可确认事件已安全存储

### Decision 4: 不可变事件 + 可变执行轨迹分离

events 表（不可变、仅追加）与 executions 表（可变、可追加）分离。

**理由：**
- 事件日志保持纯净可重放
- 执行轨迹可以重复记录（重试、补偿、调谐）
- 两表使用 event_id 关联

### Decision 5: 补偿操作可推导

根据原始事件类型 + 已成功子任务，自动生成逆向操作，不依赖硬编码的补偿清单。

**理由：**
- 减少维护成本
- 添加新事件类型时不需要同步更新补偿表
- 补偿操作在 executions 表中有独立 trace

## 技术架构

参见 C4 模型文档：

| 视图 | 文档 |
|------|------|
| Context 图 | [doc/c4/context.md](../c4/context.md) |
| Container 图 | [doc/c4/container.md](../c4/container.md) |
| Core Component 图 | [doc/c4/component-core.md](../c4/component-core.md) |
| CLI Component 图 | [doc/c4/component-cli.md](../c4/component-cli.md) |

### 技术栈

| 组件 | 技术 |
|------|------|
| API Server | Python 3.11+ / FastAPI / uvicorn |
| CLI | Python 3.11+ / Click |
| 数据库 | SQLite (aiosqlite, WAL 模式) |
| 异步 HTTP | httpx |
| 测试 | pytest |
| 部署 | Docker (Docker Compose) |

### API 摘要

| 端点 | 方法 | 用途 |
|------|------|------|
| `POST /v1/events` | 写入事件 | `{intent, items, total_price, ...}` → `{event_id, status}` |
| `GET /v1/events/{event_id}` | 查询事件状态 | → `{event_id, status, executions[]}` |
| `POST /v1/query` | 查询后端 | `{target, operation, params}` → `{data, event_id}` |
| `GET /v1/health` | 健康检查 | → `{status, adapters}` |

## 模块清单 (MVP 实现)

### 模块 1: 数据模型与数据库

| 文件 | 职责 |
|------|------|
| `homebus/models.py` | Pydantic 模型（Event, Execution, Query, Health） |
| `homebus/database.py` | SQLite 初始化 + 连接池 + WAL 模式 + events/executions 表 CRUD |

### 模块 2: API Layer

| 文件 | 职责 |
|------|------|
| `homebus/api.py` | FastAPI 应用 + 路由定义 |
| `homebus/validators.py` | 事件校验器（Schema + 幂等） |

### 模块 3: 核心引擎

| 文件 | 职责 |
|------|------|
| `homebus/dispatch.py` | 调度引擎（子任务推导规则） |
| `homebus/executor.py` | 任务执行器（并发/串行/超时） |
| `homebus/saga.py` | Saga 补偿推倒器 |
| `homebus/aggregator.py` | 结果聚合器 |

### 模块 4: Adapters

| 文件 | 职责 |
|------|------|
| `homebus/adapters/base.py` | AdapterBase 抽象基类 |
| `homebus/adapters/grocy.py` | Grocy Adapter |
| `homebus/adapters/beancount.py` | Beancount Adapter |
| `homebus/adapters/homebox.py` | Homebox Adapter |

### 模块 5: 查询代理

| 文件 | 职责 |
|------|------|
| `homebus/query_router.py` | 查询路由 |

### 模块 6: CLI

| 文件 | 职责 |
|------|------|
| `cli/homebus.py` | Click CLI 入口（publish / query / status / health） |

## Dependencies

### 运行时依赖

| 依赖 | 用途 |
|------|------|
| fastapi | API Server |
| uvicorn | ASGI 服务器 |
| aiosqlite | 异步 SQLite |
| pydantic | 数据模型 + 校验 |
| click | CLI 框架 |
| httpx | 异步 HTTP 客户端 |

### 外部系统依赖

| 系统 | 版本要求 | 接入方式 |
|------|---------|---------|
| Grocy | 4.x+ | REST API |
| Beancount | 2.x+ | 写入：CLI + 本地文件；读取：REST API (fava, v0.2) |
| Homebox | 0.10+ | REST API |

## Timeline

| 里程碑 | 内容 | 预计耗时 |
|--------|------|---------|
| v0.1-alpha | 可运行的 API + CLI + 基础适配器 + saga | 2 周 |
| v0.1-beta | Agent 端集成测试 + 端到端验证 | 1 周 |
| v0.1-release | Bug 修复 + 文档完善 + 发布 | 3 天 |

## Open Questions

1. **适配器配置** — 各后端的地址/认证/API key 通过环境变量还是配置文件？
   → ✅ 已解决：TOML 配置文件 + 环境变量注入（敏感信息）。详见 [config-paradigm.md](../specs/config-paradigm.md)

2. **Beancount 接入方式** — ✅ 已决策：CLI `homebus beancount write` 直接写入 `.bean` 文件（幂等 + bean-check + git commit），读取走 Fava REST API（v0.2）
   → 详见 [beancount-integration.md](../specs/beancount-integration.md)

3. **CLI 的 JSON 参数如何安全传递** — `--items` 参数是嵌套 JSON，命令行引号处理易出错
   → 初步建议：可接受 JSON 文件路径（`--items-file ./items.json`）作为备选

4. **Saga 补偿的确定性** — 某些补偿操作可能自身也失败（如 Homebox 删除物品时已不存在）
   → 需定义不可撤销场景的处理策略（记录日志 + 人工介入）
