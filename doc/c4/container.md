---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["c4", "homebus", "container"]
related:
  context: "context.md"
  specs: "../specs/homebus.md"
---

# C4 Level 2: Container Diagram

> HomeBus 内部的容器（进程/服务）划分。每个容器是一个可独立部署的单元。

## 容器总览

```
┌──────────────────────────────────────────────────────────┐
│ HomeBus 系统                                              │
│                                                          │
│ ┌────────────────────┐  ┌────────────────────┐           │
│ │  HomeBus CLI        │  │  HomeBus MCP Server │           │
│ │  (Python Click)     │  │  (Python MCP SDK)   │           │
│ └────────┬───────────┘  └────────┬───────────┘           │
│          │                       │                        │
│          └──────────┬────────────┘                        │
│                     │ HTTP (JSON)                         │
│                     ▼                                     │
│ ┌────────────────────────────────────────────────────┐   │
│ │  HomeBus API Server (FastAPI)                       │   │
│ │                                                     │   │
│ │  ┌──────────────────────────────────────────────┐   │   │
│ │  │  事件处理流水线                                 │   │   │
│ │  │  POST /v1/events → 写日志 → 调度 → saga        │   │   │
│ │  │  POST /v1/query  → 写日志 → 路由 → 返回         │   │   │
│ │  │  GET /v1/events/{id} → 返回执行状态              │   │   │
│ │  │  GET /v1/health  → 健康检查                     │   │   │
│ │  └──────────────────────────────────────────────┘   │   │
│ │                                                     │   │
│ │  ┌──────────────┐  ┌──────────────┐                 │   │
│ │  │ events 表     │  │ executions 表│                 │   │
│ │  │ (SQLite, 只增)│  │ (SQLite, 可变)│                 │   │
│ │  └──────────────┘  └──────────────┘                 │   │
│ └────────────────────────────────────────────────────┘   │
│                                                          │
│ ┌────────────────────────────────────────────────────┐   │
│ │  Adapter 层                                          │   │
│ │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐  │   │
│ │  │ Grocy  │ │ Beancount│ │ Homebox │ │ 查询代理   │  │   │
│ │  │Adapter │ │ Adapter  │ │ Adapter │ │ (路由+聚合) │  │   │
│ │  └────────┘ └──────────┘ └────────┘ └──────────┘  │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## 容器列表

### 1. HomeBus API Server

| 属性 | 值 |
|------|------|
| **技术** | Python + FastAPI + uvicorn |
| **职责** | HomeBus 核心服务——接收事件、写日志、分发调度、查询代理、健康检查 |
| **数据存储** | SQLite（events 表 + executions 表），文件卷挂载 |
| **端口** | 8080（可配置） |
| **部署** | Docker 容器 / 本地进程 |

**关键 API：**

| 端点 | 方法 | 职责 |
|------|------|------|
| `/v1/events` | POST | 提交事件（写入口） |
| `/v1/events/{event_id}` | GET | 查询事件状态 |
| `/v1/query` | POST | 查询代理 |
| `/v1/health` | GET | 健康检查 |

**内部模块：**
- 事件校验器 → 写 events 表 → 调度引擎 → 分发到 Adapter → 写 executions 表
- Saga 补偿推导器 → 部分失败时自动生成逆向操作
- 查询路由 → 路由到对应 Adapter → 返回结果

### 2. HomeBus CLI

| 属性 | 值 |
|------|------|
| **技术** | Python + Click |
| **职责** | 命令行封装，Agent 通过 terminal 命令调用 |
| **部署** | Python 包（pip install），随 HomeBus 一起分发 |
| **依赖** | 依赖 HomeBus API Server 运行 |

**命令列表：**

```
homebus publish      # 提交事件（购买/消耗/卖出/纠偏）
homebus query        # 查询后端状态
homebus status       # 查询事件执行状态
homebus health       # 检查 HomeBus 健康状态
```

### 3. HomeBus MCP Server

| 属性 | 值 |
|------|------|
| **技术** | Python + MCP SDK |
| **职责** | MCP 协议封装，支持 MCP Client 直接调用 HomeBus |
| **部署** | 作为子进程运行（stdio 模式），或独立 HTTP 服务 |
| **依赖** | 依赖 HomeBus API Server 运行（内部调 API） |
| **版本** | v0.2 规划，MVP 暂不实现 |

**MCP 工具：**

```
homebus_publish_event       # 提交事件
homebus_query               # 查询
homebus_get_event_status    # 获取事件状态
```

---

## 容器间关系

| 源容器 | 目标容器 | 关系 | 协议 |
|--------|---------|------|------|
| HomeBus CLI | HomeBus API Server | 调用 | HTTP (JSON) |
| HomeBus MCP Server | HomeBus API Server | 调用 | HTTP (JSON) |
| HomeBus API Server | Grocy Adapter | 内部调用 | Python 调用 |
| HomeBus API Server | Beancount Adapter | 内部调用 | Python 调用 |
| HomeBus API Server | Homebox Adapter | 内部调用 | Python 调用 |
| HomeBus API Server | 查询代理 | 内部调用 | Python 调用 |
| HomeBus API Server | SQLite (events) | 读写 | aiosqlite |
| HomeBus API Server | SQLite (executions) | 读写 | aiosqlite |

## 部署视图（MVP）

```
┌─────────────────────────┐
│  Docker Host             │
│                          │
│  ┌───────────────────┐  │
│  │  homebus-api       │  │  ← 核心服务, port 8080
│  │  (FastAPI + SQLite)│  │
│  └───────────────────┘  │
│                          │
│  ┌───────────────────┐  │
│  │  Grocy              │  │  ← 外部依赖
│  └───────────────────┘  │
│                          │
│  ┌───────────────────┐  │
│  │  Homebox            │  │  ← 外部依赖
│  └───────────────────┘  │
│                          │
│  ┌───────────────────┐  │
│  │  Beancount          │  │  ← 外部依赖 (fava)
│  └───────────────────┘  │
└─────────────────────────┘

CLI 和 MCP Server 在 Agent 侧运行（同一主机或网络可达）
```
