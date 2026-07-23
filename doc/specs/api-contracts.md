---
status: draft
priority: P1
blocks:
  - homebus/models.py
  - homebus/api.py
  - homebus/validators.py
created: 2026-07-23
updated: 2026-07-23
author: "vicat47"
tags: ["spec", "homebus", "api", "contract", "mvp"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  event-types: "event-types.md"
  database-schema: "database-schema.md"
---

# HomeBus API Contracts — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-23
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus API 四个端点的 Pydantic request/response schema、错误格式、错误码枚举。

## Endpoints

| 端点 | 方法 | 用途 |
|------|------|------|
| `/v1/events` | POST | 写入事件 |
| `/v1/events/{event_id}` | GET | 查询事件状态 |
| `/v1/query` | POST | 查询代理 |
| `/v1/health` | GET | 健康检查 |

---

## POST /v1/events

### Request

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class EventItem(BaseModel):
    name: str
    category: Literal["consumable", "durable"]
    quantity: float
    unit: str
    price: float
    grocy_product_id: Optional[str] = None

    model_config = {"extra": "allow"}  # homebox_location_id 等扩展字段透传

class CreateEventRequest(BaseModel):
    intent: Literal["purchase", "consume"]
    event_id: Optional[str] = Field(
        None, pattern=r"^evt_[a-z0-9_]+$",
        description="Agent 自定义 event_id。不传则自动生成"
    )
    items: list[EventItem] = Field(min_length=1)

    # purchase 专用
    total_price: Optional[float] = None
    store: Optional[str] = None
    purchased_at: Optional[datetime] = None

    # consume 专用
    consumed_at: Optional[datetime] = None

    # 通用
    note: Optional[str] = None

    model_config = {"extra": "allow"}
```

```json
// purchase 示例
{
  "intent": "purchase",
  "event_id": "evt_sess1_001",
  "items": [
    {"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}
  ],
  "total_price": 60.0,
  "store": "京东",
  "purchased_at": "2026-07-23T10:00:00"
}

// consume 示例
{
  "intent": "consume",
  "event_id": "evt_sess1_002",
  "items": [
    {"name": "牛奶", "quantity": 1, "unit": "盒"}
  ],
  "consumed_at": "2026-07-23T08:00:00"
}
```

**校验规则**：

| 规则 | 违反时返回 |
|------|-----------|
| `intent` 不在 `["purchase", "consume"]` 中 | 400 |
| `items` 为空 | 400 |
| `event_id` 格式非法 | 400 |
| purchase 缺少 `total_price` | 400 |
| **所有 items 必须同 category**（混合品类拒绝）| 400 |
| `event_id` 已存在（幂等命中）| **200**（返回已有事件状态） |

### Response（正常创建）

```json
{
  "event_id": "evt_sess1_001",
  "status": "pending",
  "message": "事件已接收"
}
```

### Response（幂等命中）

```json
{
  "event_id": "evt_sess1_001",
  "status": "executing",
  "duplicate": true,
  "message": "事件已存在（幂等命中）"
}
```

---

## GET /v1/events/{event_id}

### Response

```python
class ExecutionItem(BaseModel):
    seq: int
    service: Literal["grocy", "beancount", "homebox"]
    action: str
    status: Literal["pending", "running", "success", "failed", "compensated"]
    result: Optional[dict] = None
    is_compensation: bool = False

class EventStatusResponse(BaseModel):
    event_id: str
    status: Literal["accepted", "executing", "success", "compensated", "failed"]
    intent: str
    executions: list[ExecutionItem] = []
    created_at: str
    updated_at: str
```

```json
// 执行中
{
  "event_id": "evt_sess1_001",
  "status": "executing",
  "intent": "purchase",
  "executions": [
    {"seq": 0, "service": "grocy", "action": "add_stock", "status": "success",
     "result": {"added": [{"name": "牛奶", "product_id": 5, "quantity": 3}]}}
  ],
  "created_at": "2026-07-23T10:00:01",
  "updated_at": "2026-07-23T10:00:02"
}

// 终态（全部成功）
{
  "event_id": "evt_sess1_001",
  "status": "success",
  "intent": "purchase",
  "executions": [
    {"seq": 0, "service": "grocy", "action": "add_stock", "status": "success", "result": {...}},
    {"seq": 1, "service": "beancount", "action": "record_expense", "status": "success", "result": {...}}
  ],
  "created_at": "2026-07-23T10:00:01",
  "updated_at": "2026-07-23T10:00:05"
}

// 未找到
// HTTP 404 + ErrorResponse
```

---

## POST /v1/query

### Request

```python
class QueryRequest(BaseModel):
    target: Literal["grocy", "beancount", "homebox"]
    operation: str
    params: dict
```

```json
// Grocy 库存查询
{
  "target": "grocy",
  "operation": "stock_query",
  "params": {"product_name": "牛奶"}
}

// Beancount 写入验证
{
  "target": "beancount",
  "operation": "verify_entry",
  "params": {"event_id": "evt_sess1_001"}
}

// Homebox 位置列表查询
{
  "target": "homebox",
  "operation": "list_locations",
  "params": {}
}
```

### Response

```json
// Grocy stock_query
{
  "data": {
    "product_name": "牛奶",
    "product_id": 5,
    "stock": 50,
    "unit": "盒"
  },
  "event_id": "evt_q_001"
}

// Beancount verify_entry（找到）
{
  "found": true,
  "event_id": "evt_sess1_001",
  "entry": "2026-07-23 * \"京东\" \"蒙牛纯牛奶 x3\" #homebus\n  homebus_event: \"evt_sess1_001\"\n  homebus_time: \"2026-07-23T10:00:00\"\n  Expenses:Food:Groceries  60.00 CNY\n    item: \"蒙牛纯牛奶\"\n  Liabilities:CreditCard:JD  -60.00 CNY",
  "file": "~/ledger/2025/0-default/homebus-07.bean",
  "line": 5
}

// Beancount verify_entry（未找到）
{
  "found": false,
  "event_id": "evt_sess1_001"
}
```

**注意**：query 操作写 events 表（intent=query），但不创建 executions 记录。

---

## GET /v1/health

### Response

```python
class AdapterHealth(BaseModel):
    grocy: Literal["ok", "error"] = "ok"
    beancount: Literal["ok", "error"] = "ok"
    homebox: Literal["ok", "error"] = "ok"

class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"] = "healthy"
    adapters: AdapterHealth
```

```json
// 全部健康
{
  "status": "healthy",
  "adapters": {
    "grocy": "ok",
    "beancount": {"status": "ok", "detail": "bean-check v2.3.6"},
    "homebox": "ok"
  }
}

// 部分不可用（HTTP 200，不在状态码上报错）
{
  "status": "degraded",
  "adapters": {
    "grocy": "ok",
    "beancount": {"status": "ok", "detail": "bean-check v2.3.6"},
    "homebox": "error"
  }
}
```

Health check 详情见 [adapter-interfaces.md](adapter-interfaces.md#health-check)。

---

## 错误响应格式

### ErrorResponse

所有非 200 响应使用统一错误格式：

```python
from enum import Enum

class ErrorCode(str, Enum):
    INVALID_EVENT_SCHEMA = "INVALID_EVENT_SCHEMA"       # 400
    INVALID_QUERY_PARAMS = "INVALID_QUERY_PARAMS"       # 400
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"                  # 404
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"          # 502
    ADAPTER_TIMEOUT = "ADAPTER_TIMEOUT"                  # 504
    COMPENSATION_FAILED = "COMPENSATION_FAILED"          # 500
    INTERNAL_ERROR = "INTERNAL_ERROR"                    # 500

class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

```json
// 400 — 请求格式非法
{
  "error": {
    "code": "INVALID_EVENT_SCHEMA",
    "message": "items 列表不能为空",
    "details": {"field": "items", "reason": "empty"}
  }
}

// 404 — 事件不存在
{
  "error": {
    "code": "EVENT_NOT_FOUND",
    "message": "event_id 'evt_xxx' 不存在"
  }
}

// 502 — 后端不可达
{
  "error": {
    "code": "ADAPTER_UNAVAILABLE",
    "message": "Grocy API 不可达",
    "details": {"adapter": "grocy", "url": "http://localhost:9283/api/system/info"}
  }
}
```

### HTTP 状态码映射

| HTTP 状态码 | ErrorCode | 场景 |
|------------|-----------|------|
| 400 | `INVALID_EVENT_SCHEMA` | 请求格式非法 |
| 400 | `INVALID_QUERY_PARAMS` | 查询参数非法 |
| 404 | `EVENT_NOT_FOUND` | event_id 不存在 |
| 500 | `COMPENSATION_FAILED` | Saga 补偿失败 |
| 500 | `INTERNAL_ERROR` | 未知内部错误 |
| 502 | `ADAPTER_UNAVAILABLE` | 后端服务不可达 |
| 504 | `ADAPTER_TIMEOUT` | 后端调用超时 |

> **幂等命中**：`event_id` 重复 → HTTP **200**，非错误。`ErrorCode.IDEMPOTENT_MATCH` 为内部标识，不暴露给 API 消费者。

## Open Questions

- [ ] `items` 的 `model_config = {"extra": "allow"}` 中，`homebox_location_id` 等字段是否应在 v0.1 提升为正式字段？
- [ ] query 的 `operation` 是否需要枚举约束还是保留为 free-form string？（当前设计为 free-form string）
