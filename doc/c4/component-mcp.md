---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["c4", "homebus", "component", "mcp"]
related:
  container: "container.md"
  core: "component-core.md"
---

# C4 Level 3: Components — HomeBus MCP Server

> HomeBus MCP Server 的内部组件分解。v0.2 规划，MVP 暂不实现。

## 定位

MCP Server 是一个**薄封装层**，在 CLI 之上加一层 MCP 协议。它不包含业务逻辑——业务逻辑全在 HomeBus API Server 中。

## 组件结构

```
┌─────────────────────────────────────────────────────┐
│  HomeBus MCP Server                                  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  MCP Server (Python MCP SDK)                  │  │
│  │  - stdio 模式 (默认)                           │  │
│  │  - HTTP 传输模式 (可选)                        │  │
│  │  - 工具注册                                   │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                           │
│                         ▼                           │
│  ┌──────────────────────────────────────────────┐  │
│  │  工具实现层 (Tool Implementations)             │  │
│  │                                               │  │
│  │  homebus_publish_event(args) →                │  │
│  │    ├→ 参数校验 (JSON Schema)                   │  │
│  │    ├→ 构建请求体                               │  │
│  │    ├→ 调 CLI (subprocess) / 直调 API           │  │
│  │    └→ 格式化返回                               │  │
│  │                                               │  │
│  │  homebus_query(args) →                        │  │
│  │    └→ 参数校验 → 请求 → 返回                   │  │
│  │                                               │  │
│  │  homebus_get_event_status(args) →             │  │
│  │    └→ 参数校验 → 请求 → 返回                   │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                           │
│                         ▼                           │
│  ┌──────────────────────────────────────────────┐  │
│  │  底层调用方式 (Backend Strategy)              │  │
│  │  - 方式 A: subprocess(CLI) → 解析 stdout      │  │
│  │  - 方式 B: HTTP 直调 HomeBus API              │  │
│  │  (可配置，默认方式 A)                          │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## MCP 工具定义

### tool: homebus_publish_event

```json
{
  "name": "homebus_publish_event",
  "description": "向 HomeBus 提交一个家庭事务事件（购买/消耗/卖出/纠偏）",
  "inputSchema": {
    "type": "object",
    "required": ["intent", "items", "total_price"],
    "properties": {
      "intent": {
        "type": "string",
        "enum": ["purchase", "consume", "sell", "correct"],
        "description": "事件意图类型"
      },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["name", "quantity", "category"],
          "properties": {
            "name": { "type": "string" },
            "quantity": { "type": "number", "minimum": 0.01 },
            "category": { "type": "string", "enum": ["consumable", "asset"] },
            "unit_price": { "type": "number" },
            "location": { "type": "string" }
          }
        }
      },
      "total_price": { "type": "number" },
      "payment_account": { "type": "string", "default": "Assets:Alipay" }
    }
  }
}
```

### tool: homebus_query

```json
{
  "name": "homebus_query",
  "description": "查询后端服务状态（库存/资产/账目）",
  "inputSchema": {
    "type": "object",
    "required": ["target", "operation"],
    "properties": {
      "target": {
        "type": "string",
        "enum": ["grocy", "homebox", "beancount"]
      },
      "operation": { "type": "string" },
      "params": { "type": "object" }
    }
  }
}
```

### tool: homebus_get_event_status

```json
{
  "name": "homebus_get_event_status",
  "description": "查询事件执行状态",
  "inputSchema": {
    "type": "object",
    "required": ["event_id"],
    "properties": {
      "event_id": { "type": "string" },
      "watch": { "type": "boolean", "description": "持续等待直到事件完成" }
    }
  }
}
```

## 实现策略

| 方面 | 决策 |
|------|------|
| **MCP SDK** | Python 官方 MCP SDK |
| **传输方式** | stdio 模式（默认），HTTP 模式可选 |
| **底层调用** | 默认 subprocess(CLI)，可切换为直调 API |
| **部署** | 与 CLI 一起 pip install，作为独立进程运行 |
| **实现阶段** | v0.2（MVP 不包含） |
