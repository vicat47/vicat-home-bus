---
status: approved
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
│  │ POST accounts/add    │ │  ← 所有 items 合计一笔
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
| Homebox 创建资产失败 | 自动补偿：回滚 Grocy 库存 | 是 |
| 两者都失败 | 自动补偿：回滚 Grocy 库存 | 是 |

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
