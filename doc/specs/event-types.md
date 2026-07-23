---
status: approved
priority: P0
blocks:
  - homebus/models.py
  - homebus/dispatch.py
  - homebus/executor.py
  - homebus/aggregator.py
  - homebus/validators.py
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "events", "mvp"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  c4-core: "../c4/component-core.md"
  prd-us1: "../prd/homebus-v0.1.md#US-1"
  prd-us4: "../prd/homebus-v0.1.md#US-4"
  beancount-integration: "beancount-integration.md"
  database-schema: "database-schema.md"
  adapter-interfaces: "adapter-interfaces.md"
---

# HomeBus 事件类型定义与推导规则 — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-20
- **Author**: vicat47
- **Status**: Approved

## Overview

定义 MVP v0.1 支持的事件类型、字段模型、子任务推导规则、以及位置归类策略。

## MVP 事件类型

| 事件类型 | 描述 | 涉及后端 |
|---------|------|---------|
| `purchase` | 购买物品（京东/超市等） | Grocy(+库存) + Beancount(记账) + Homebox(资产，仅 durable) |
| `consume` | 消耗/使用物品（如喝完牛奶） | Grocy(-库存) |

> MVP 仅此两种。`discard` / `transfer` 等后续版本添加。

## 字段模型

### purchase

```json
{
  "intent": "purchase",
  "items": [
    {
      "name": "牛奶",
      "category": "consumable",
      "quantity": 3,
      "unit": "盒",
      "price": 20.0,
      "grocy_product_id": null
    }
  ],
  "total_price": 60.0,
  "store": "京东",
  "purchased_at": "2026-07-20T10:00:00",
  "note": "早餐牛奶"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `intent` | string | ✅ | 固定值 `"purchase"` |
| `items[]` | array | ✅ | 物品清单，至少 1 项 |
| `items[].name` | string | ✅ | 物品名称 |
| `items[].category` | string | ✅ | `"consumable"` 消耗品 / `"durable"` 耐用品 |
| `items[].quantity` | float | ✅ | 数量 |
| `items[].unit` | string | ✅ | 单位（盒/个/瓶/kg） |
| `items[].price` | float | ✅ | 单价 |
| `items[].grocy_product_id` | string\|null | 否 | 指定 Grocy 产品 ID |
| `total_price` | float | ✅ | 总价 |
| `store` | string\|null | 否 | 购买渠道 |
| `purchased_at` | datetime\|null | 否 | 购买时间，默认当前 |
| `note` | string\|null | 否 | 备注 |

**扩展预留字段**（当前模型不包含，接口层面允许 extra fields 透传）:

```
items[].homebox_location_id   — 资产位置 ID（Agent 推断后传入）
items[].beancount_account     — 记账科目覆盖
actor                         — 操作人（预留多用户）
tags[]                        — 自定义标签
reference                     — 外部引用 ID
```

### consume

```json
{
  "intent": "consume",
  "items": [
    {
      "name": "牛奶",
      "quantity": 1,
      "unit": "盒",
      "grocy_product_id": null
    }
  ],
  "consumed_at": "2026-07-20T08:00:00",
  "note": "早餐喝了"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `intent` | string | ✅ | 固定值 `"consume"` |
| `items[]` | array | ✅ | 物品清单，至少 1 项 |
| `items[].name` | string | ✅ | 物品名称 |
| `items[].quantity` | float | ✅ | 消耗数量 |
| `items[].unit` | string | ✅ | 单位 |
| `items[].grocy_product_id` | string\|null | 否 | 指定 Grocy 产品 ID |
| `consumed_at` | datetime\|null | 否 | 消耗时间，默认当前 |
| `note` | string\|null | 否 | 备注 |

**扩展预留**: `actor`、`tags`

## 子任务推导规则

### purchase

```
┌───────── 事件校验 ─────────┐
│ intent + items 合法性检查   │
└─────────────┬───────────────┘
              │ 通过
              ▼
┌───────── 步骤 1 ──────────┐
│ Grocy 批量加库存           │  ← 串行，必须先成功
│ POST stock/add {items}    │
└─────────────┬───────────────┘
              │ 成功
              ▼
┌───────── 步骤 2 ──────────┐
│ 并行执行:                  │
│                            │
│  ┌──────────────────────┐ │
│  │ Beancount 记支出      │ │
│  │ .bean 文件写入         │ │  ← Adapter 生成分录文本，CLI write 执行 I/O
│  └──────────────────────┘ │
│                            │
│  ┌──────────────────────┐ │
│  │ Homebox 创建资产      │ │  ← 仅 category=durable 的 items
│  │ POST assets/create   │ │
│  └──────────────────────┘ │
└─────────────┬───────────────┘
              │
       ┌──────┴──────┐
       │ 全成功       │ 部分失败
       ▼              ▼
   success       补偿模式
```

**失败处理矩阵**:

| 失败位置 | 处理方式 | 是否补偿 |
|---------|---------|---------|
| 事件校验不通过 | 返回 400，事件不写入 | 否 |
| Grocy 加库存失败 | 事件标记失败，不继续 | 否（无任何操作已执行） |
| Beancount 记支出失败 | 自动补偿：回滚 Grocy 库存 | 是 |
| Homebox 创建资产失败 | 自动补偿：回滚 Grocy 库存；若 Beancount 已成功则同时回滚 Beancount 分录 | 是 |
| 两者都失败 | 自动补偿：回滚 Grocy 库存；若 Beancount 已成功则同时回滚 Beancount 分录 | 是 |

### consume

```
┌───────── 事件校验 ─────────┐
└─────────────┬───────────────┘
              │ 通过
              ▼
┌───────── 单项 ────────────┐
│ Grocy 减库存               │  ← 单项，无依赖
│ POST stock/consume {items}│
└─────────────┬───────────────┘
              │
       ┌──────┴──────┐
       │ 成功        │ 失败
       ▼            ▼
   success     事件标记失败
```

| 失败位置 | 处理方式 | 是否补偿 |
|---------|---------|---------|
| Grocy 减库存失败 | 事件标记失败 | 否（单项操作） |

## 位置归类策略

Homebox 资产创建时需要的"位置"字段不由 HomeBus 硬编码，遵循以下流程：

```
用户: "买了箱牛奶放厨房"
  │
  ▼
Agent 解析意图 + 实体 → 构建 purchase 事件
  │                      │
  │                    items.category=consumable → Grocy + Beancount 即可
  │                    items.category=durable   → 需要位置信息
  │
  ▼
查询位置资源: homebus query homebox/locations
  │  返回: [{id: "loc_1", name: "厨房"}, {id: "loc_2", name: "客厅"}, ...]
  │
  ▼
Agent 结合: 用户说了"放厨房" + 查询结果 → 推断 location_id = "loc_1"
  │
  ▼
publish 事件: 在 items[].homebox_location_id 中携带推断结果
  │
  ▼
用户确认 / 用户纠正 ("不对，放客厅") → Agent 重新查询并更新
```

**核心原则**:
1. HomeBus 不负责智能归类（归 Agent 层职责）
2. HomeBus 通过 query 接口暴露可供查询的资源（位置列表、分类、标签）
3. Agent 结合用户输入 + 上下文 + 历史偏好 + 查询结果推断位置
4. 用户默认确认，纠偏时 Agent 重新 query 并 update
5. 用户显式指定位置时，Agent 直接使用用户指定值

## 事件数据流 (完整)

```
Agent 构建事件 JSON
       │
       ▼
CLI: homebus publish --body '{...}'
       │
       ▼
HomeBus API: POST /v1/events
       │
       ├─ 校验 Schema + 幂等检查
       ├─ 写入 events 表 (status=accepted)
       ├─ 返回 {event_id, status: "accepted"}
       │
       ▼ (后台异步)
       ├─ Dispatch: intent + items → 子任务列表
       ├─ Executor: 按规则执行子任务
       │   ├─ Grocy 批量操作
       │   ├─ Beancount 记账
       │   └─ Homebox 资产创建 (durable only)
       ├─ 结果聚合: success / compensated / failed
       └─ 更新 events 表 status
       │
       ▼
Agent: homebus status --event-id <id>
        ├─ success     → 告知用户
        ├─ compensated → 告知用户部分失败已回滚
        └─ failed      → 告知用户并提供错误详情
```

## 事件状态机

### 状态定义

| 状态 | 含义 | 谁设置 |
|------|------|--------|
| `pending` | 已写入 events 表，等待后台调度 | Writer（`api.py`） |
| `executing` | 后台开始执行子任务 | Dispatch（`dispatch.py`） |
| `success` | 所有子任务成功 | Aggregator（`aggregator.py`） |
| `compensated` | 部分失败已自动补偿回滚 | Aggregator（`aggregator.py`） |
| `failed` | 执行失败且无法补偿 | Aggregator（`aggregator.py`） |

### 状态转换

```
           POST /v1/events
                │
          Schema 校验
          ┌─────┴─────┐
          ▼             ▼
       通过          不通过 → 400（不写 DB）
          │
          ▼
    INSERT events (status=pending)
          │
          ▼
    API 响应 {event_id, status: "pending"}
          │
          ▼  ← BackgroundTask 异步触发
    Dispatch 推导子任务
          │
    UPDATE events SET status='executing'
          │
          ▼
    Executor 执行子任务（逐层 DAG）
          │
    ┌─────┼──────────┐
    ▼     ▼          ▼
  全成功 部分失败   全部失败
    │     │          │
    ▼     ▼          ▼
 success Saga补偿   failed
          │
    ┌─────┼──────────┐
    ▼     ▼
  补偿   补偿
  成功   失败
    │     │
    ▼     ▼
compensated failed
```

### 状态与 API 响应对照

| DB status | GET /v1/events/{id} 返回 | 说明 |
|-----------|-------------------------|------|
| `pending` | `{event_id, status: "pending"}` | Agent 需轮询等待 |
| `executing` | `{event_id, status: "executing"}` | Agent 需继续轮询 |
| `success` | `{event_id, status: "success", executions: [...]}` | 终态 |
| `compensated` | `{event_id, status: "compensated", executions: [...]}` | 终态 |
| `failed` | `{event_id, status: "failed", executions: [...]}` | 终态 |

> **注意**：API 响应中的 `status` 字段直接使用 DB 值，不翻译。之前部分文档使用 `"accepted"` 作为概念性描述，**已废弃**——统一使用 `"pending"`。DB initial value = `"pending"`，API response status = DB status。

### 约束

- **非终态→终态不可逆**：`success`/`compensated`/`failed` 不可再变为其他状态
- **Saga 补偿**：执行成功→创建 `is_compensation=1` 的 execution 记录；原 execution 的 status 从 `success` 更新为 `compensated`
- **幂等重试**：同一个 event_id 的 `POST` 请求返回已有 DB 状态（200，非错误）


## SubTask 数据模型

### 定义

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class SubTask:
    seq: int                              # 序号（Dispatch 分配，从 0 开始）
    service: Literal["grocy", "beancount", "homebox"]
    action: str                           # 如 "add_stock"、"record_expense"、"create_asset"
    params: dict                          # 传递给 Adapter.execute() 的参数
    depends_on: list[int] = field(default_factory=list)  # 依赖的 seq 列表
    timeout: float = 30.0                 # 超时（秒）
    max_retries: int = 3                  # 最大重试次数
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `seq` | int | Dispatch Engine 分配的子任务序号。Executor 用此序号建立 DAG |
| `service` | Literal | 目标后端 |
| `action` | str | 操作名称，对应 Adapter 的 action catalog（见 [adapter-interfaces.md](adapter-interfaces.md)）|
| `params` | dict | 操作参数，由 Dispatch 从 Event + routing registry 拼装 |
| `depends_on` | list[int] | 依赖的子任务 seq 列表。空列表=无依赖（可与其他同层子任务并行） |
| `timeout` | float | 子任务执行超时，默认 30s |
| `max_retries` | int | 失败后最大重试次数 |

### depends_on 示例

```
purchase(consumable) 事件:

  seq=0: Grocy add_stock     depends_on=[]    ← L0（无依赖）
  seq=1: Beancount record_expense depends_on=[0]  ← L1（依赖 Grocy 先成功）

purchase(durable) 事件:

  seq=0: Grocy add_stock     depends_on=[]
  seq=1: Beancount record_expense depends_on=[0]  ← L1（与 seq=2 并行）
  seq=2: Homebox create_asset  depends_on=[0]      ← L1（与 seq=1 并行）

consume 事件:

  seq=0: Grocy consume_stock depends_on=[]    ← 单项，无依赖
```

### Executor DAG 执行算法

```
1. Parse SubTask[].depends_on → Build DAG
2. Topological sort → layers [L0, L1, ..., Ln]
3. For each layer Li:
   a. Execute all subtasks in Li concurrently (asyncio.gather)
   b. If any subtask in Li fails:
      - Cancel remaining in-flight subtasks in Li
      - Do NOT proceed to Li+1
      - Trigger Saga compensator for all successful subtasks in L0..Li
   c. If all succeed, proceed to Li+1
4. If all layers complete → Aggregator sets status='success'
```

## 多 item 约束

purchase 事件中所有 `items` **必须属于同一 category**（全部 consumable 或全部 durable）。如需混合品类，Agent 应拆为两个独立的 purchase 事件。Validator 负责在校验阶段拒绝混合品类的事件。
