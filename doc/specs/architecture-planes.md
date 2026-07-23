---
status: draft
priority: ∞
blocks: []
created: 2026-07-23
updated: 2026-07-23
author: "vicat47"
tags: ["spec", "homebus", "architecture", "planes", "meta"]
type: spec
related:
  homebus: "homebus.md"
  event-types: "event-types.md"
  database-schema: "database-schema.md"
  adapter-interfaces: "adapter-interfaces.md"
  api-contracts: "api-contracts.md"
  beancount-integration: "beancount-integration.md"
  routing-registry: "routing-registry.md"
  config-paradigm: "config-paradigm.md"
  backend-boundaries: "backend-boundaries.md"
  c4-core: "../c4/component-core.md"
  c4-container: "../c4/container.md"
---

# HomeBus 架构平面定义 — Specification

- **Version**: 1.0.0
- **Date**: 2026-07-23
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus 系统架构中的 7 个核心抽象平面（Architecture Planes）和 3 个提升平面。每个平面代表一个架构关注面（concern），跨组件和数据流组织。本文档是对专项 spec 和 C4 模型的**元视角补充**——它解释"为什么文档体系是这样组织的"。

> **说明**：只有"观测面"在项目文档中被显式命名为"面"。其余平面是隐含在架构设计中的关注面，本文档将它们提升为显式的、可引用的架构概念。

---

## 核心平面（7 个）

### P1: 写入面 (Write Plane)

| 属性 | 值 |
|------|------|
| **版本** | v0.1 |
| **职责** | 事件提交流水线：Agent → API → 校验 → 持久化 → 调度 → 适配器执行 → 终态 |
| **入口** | `POST /v1/events` |
| **核心组件** | Event Validator → Event Writer → Dispatch Engine → Task Executor → Adapters |
| **数据流向** | Agent → API → DB (events) → BackgroundTask → Adapters → Backends |
| **终态出口** | `GET /v1/events/{id}` (success/compensated/failed) |

**覆盖的 spec**：`event-types.md`、`adapter-interfaces.md`、`beancount-integration.md`、`routing-registry.md`

**C4 覆盖**：`component-core.md` §1-7（完整序列图：校验→写入→调度→执行→补偿→聚合）

---

### P2: 读面 (Read Plane)

| 属性 | 值 |
|------|------|
| **版本** | v0.1 |
| **职责** | 查询代理：Agent → API → 路由到对应后端适配器 → 返回结果 |
| **入口** | `POST /v1/query` |
| **核心组件** | Query Router → Adapters |
| **数据流向** | Agent → API → Adapter.execute(action) → Backend → Agent |
| **特殊行为** | 查询写入 events 表（intent=query），不创建 executions 记录 |

**覆盖的 spec**：`api-contracts.md`（query 端点）、`adapter-interfaces.md`（每个 adapter 的读 action）

**C4 覆盖**：`component-core.md` §8（Query Router 组件）

> **设计决策**：查询与写入在 Adapter 层面统一走 `execute()` 接口（action catalog），不区分 `execute()` vs `query()` 方法。区分在 Query Router（读路径）和 Task Executor（写路径）的调用位置上完成。

---

### P3: 控制面 (Control Plane)

| 属性 | 值 |
|------|------|
| **版本** | v0.1 |
| **职责** | 系统管理：配置加载、健康检查、初始化引导、CLI 入口 |
| **入口** | CLI (`homebus publish/query/status/health/init`)、`GET /v1/health` |
| **核心组件** | CLI、Config Manager、`homebus init` |

**覆盖的 spec**：`cli-spec.md`、`config-paradigm.md`、`routing-registry.md`（`homebus init`）

**C4 覆盖**：`component-cli.md`（CLI 组件图）、`container.md`（系统管理员角色）

---

### P4: 数据面 (Data Plane)

| 属性 | 值 |
|------|------|
| **版本** | v0.1 |
| **职责** | 持久化：events 表（不可变）+ executions 表（可变），SQLite WAL |
| **核心组件** | `database.py`（连接管理、DDL、CRUD） |
| **存储格式** | events.payload = 完整 Event JSON blob；executions.params/result = JSON |
| **migration** | Flyway 式版本化迁移（`V001__init.sql`, `V002__...`） |

**覆盖的 spec**：`database-schema.md`、`event-types.md`（events/executions 状态机）

**C4 覆盖**：`component-core.md` Database Layer 子图、`container.md`（SQLite 存储卷）

---

### P5: 补偿面 (Saga Plane)

| 属性 | 值 |
|------|------|
| **版本** | v0.1 |
| **职责** | 事务兜底：部分子任务失败 → 自动推导逆向操作 → 执行补偿 → compensated 终态 |
| **核心组件** | Saga Compensator（`saga.py`）|
| **补偿推导** | `COMPENSATION_MAP`：每种 action 一条 lambda，从原始 params + result 推导补偿 params |
| **语义分化** | Beancount undo（删除行）、Grocy reverse（新增反向记录）、Homebox undo（DELETE） |

**覆盖的 spec**：`adapter-interfaces.md`（COMPENSATION_MAP + 语义分化表）、`event-types.md`（失败处理矩阵）、`beancount-integration.md`（Beancount 删除流程）

**C4 覆盖**：`component-core.md` §6（Saga 补偿器组件 + 数据流中的补偿分支）

---

### P6: 观测面 (Observation Plane) — v0.2

| 属性 | 值 |
|------|------|
| **版本** | v0.2 |
| **职责** | 跨系统语义聚合查询：自然语言概念（"零食"、"厨房"）→ 聚合 Grocy + Beancount + Homebox 数据 |
| **入口** | `POST /v1/query {target: "observation", name: "snacks"}` |
| **核心组件** | Observation Engine（`engine.py`）|
| **配置** | `registry.toml` 的 `[observations]` 段（v0.1 静默忽略） |
| **v0.1 行为** | 不做。Agent 直查各后端（`homebus query grocy ...` + `homebus query beancount ...`） |

**覆盖的 spec**：`routing-registry.md`（观测面段 + 实现路径）

**C4 覆盖**：`component-core.md` subgraph F["v0.2 (Future)"]（组件定义 + 序列图）、`context.md`、`container.md`

---

### P7: 调谐面 (Reconciliation Plane) — v0.3

| 属性 | 值 |
|------|------|
| **版本** | v0.3 |
| **职责** | 定期对账：从 events 表提取期望状态 → 查询后端实际状态 → diff → 自动修复差异 + 报警 |
| **触发方式** | Cron（轻量 5min + 全量 daily）+ 事件驱动（子任务失败时） |
| **核心组件** | Reconciliation Engine + 三个调谐适配器 |
| **v0.1 行为** | 不做。差异通过人工排查 |

**覆盖的 spec**：`homebus.md`（superseded，含完整触发方式 + 对账流程设计）。ROADMAP.md、MEMORY.md、glossary.md 保留设计意图。

**C4 覆盖**：`context.md`（调谐报告、定时对账描述）。`component-core.md` 暂无 v0.3 Future 占位（与观测面 v0.2 占位不对称）。

> ⚠️ **技术债**：调谐引擎的完整设计存在于已废弃的 `homebus.md` 中。在从 `homebus.md` 拆分到专项 spec 的过程中，调谐引擎没有被任何新 spec 承接。建议在启动 v0.3 设计时创建 `doc/specs/reconciliation-engine.md`，并在 `component-core.md` 中添加类似观测面的 Future 占位子图。

---

## 提升平面（3 个 — 隐式→显式）

### N1: 路由面 (Routing Plane)

| 属性 | 值 |
|------|------|
| **来源** | 从 Dispatch Engine 逻辑中拆分出的独立关注面 |
| **职责** | 品类路由（consumable/durable → 默认位置/科目）+ 渠道路由（京东/美团 → 负债账户） |
| **配置** | `~/.config/homebus/registry.toml` |
| **消费方** | Dispatch Engine（事件分发时查询路由参数）|

**覆盖的 spec**：`routing-registry.md`

**C4 覆盖**：`component-core.md` §9（Routing Registry 组件，含 Registry 类接口 + 序列图中的路由查询步骤）

---

### N2: 配置面 (Configuration Plane)

| 属性 | 值 |
|------|------|
| **来源** | 从控制面中拆出的独立关注面 |
| **职责** | 配置分层加载（默认值 < TOML < 环境变量 < CLI 参数）、XDG 发现、敏感信息注入 |
| **核心组件** | `config.py`（HomeBusConfig Pydantic model + load_config/discover_config_path）|

**覆盖的 spec**：`config-paradigm.md`

**C4 覆盖**：`component-cli.md`（Config Manager 组件）。`component-core.md` 在 Routing Registry 加载序列中隐含了配置发现逻辑，但无独立 Config Manager 组件。

---

### N3: 后端边界面 (Backend Boundary Plane)

| 属性 | 值 |
|------|------|
| **来源** | 三个后端领域职责的系统化分析（原属架构决策，现提升为独立关注面） |
| **职责** | 定义 Beancount/Grocy/Homebox 的领域边界、分工链条、模糊地带判定规则、事件类型与后端映射总表 |
| **核心产出** | 三阶状态追踪模型（Beancount）、消耗品 vs 耐用品 vs 循环品判定规则 |

**覆盖的 spec**：`backend-boundaries.md`

**C4 覆盖**：`context.md` 外部系统描述表传达了后端职责（"管什么"），但没有传达边界约束（"不管什么"）。三阶模型等深层语义在 C4 中无对应表达。

---

## 平面关系图

```
         ┌──────────────────────────────────────┐
         │           控制面 (P3)                 │
         │  CLI · health · init · config        │
         └──────────┬───────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌───────┐     ┌───────────┐   ┌───────────┐
│写入面  │     │  读面      │   │  观测面    │
│(P1)   │     │  (P2)     │   │  (P6)     │
│ v0.1  │     │  v0.1     │   │  v0.2     │
└───┬───┘     └─────┬─────┘   └─────┬─────┘
    │               │               │
    ▼               ▼               ▼
┌──────────────────────────────────────────┐
│              数据面 (P4)                  │
│          events + executions             │
└──────────────────────────────────────────┘
    │               │               │
    ▼               ▼               ▼
┌──────────────────────────────────────────┐
│           路由面 (N1)                    │
│        品类路由 + 渠道路由                │
└──────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌──────────────────────────────────────────┐
│          Adapter 层                      │
│     Grocy · Beancount · Homebox         │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│          补偿面 (P5)                      │
│    Saga · COMPENSATION_MAP               │
└──────────────────────────────────────────┘

         ┌──────────────────────────┐
         │      调谐面 (P7)          │
         │      v0.3                │
         │  定时对账 · 自动修复      │
         └──────────────────────────┘

    ┌──────────────────────────────────┐
    │     后端边界面 (N3)              │
    │  Beancount | Grocy | Homebox    │
    │  领域边界 · 三阶模型 · 判定规则   │
    └──────────────────────────────────┘
```

## 版本覆盖矩阵

| 平面 | v0.1 | v0.2 | v0.3 | v1.0 |
|------|:----:|:----:|:----:|:----:|
| P1 写入面 | ✅ | ✅ | ✅ | ✅ |
| P2 读面 | ✅ | ✅ | ✅ | ✅ |
| P3 控制面 | ✅ | ✅ | ✅ | ✅ |
| P4 数据面 | ✅ | ✅ | ✅ | ✅ |
| P5 补偿面 | ✅ | ✅ | ✅ | ✅ |
| P6 观测面 | — | ✅ | ✅ | ✅ |
| P7 调谐面 | — | — | ✅ | ✅ |
| N1 路由面 | ✅ | ✅ | ✅ | ✅ |
| N2 配置面 | ✅ | ✅ | ✅ | ✅ |
| N3 后端边界 | ✅ | ✅ | ✅ | ✅ |

## Open Questions

- [ ] `component-core.md` 中是否需要为 P7 调谐面添加 Future 占位子图（类似观测面的 subgraph F）？
- [ ] 是否需要在 `component-core.md` 中添加独立的 Config Manager 组件（N2 配置面目前只在 CLI 组件图中有）？
- [ ] v0.3 启动时是否需要为 P7 创建独立的 `doc/specs/reconciliation-engine.md`？
