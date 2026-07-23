---
status: draft
priority: P0
blocks:
  - homebus/adapters/base.py
  - homebus/adapters/grocy.py
  - homebus/adapters/beancount.py
  - homebus/adapters/homebox.py
  - homebus/executor.py
  - homebus/saga.py
created: 2026-07-23
updated: 2026-07-23
author: "vicat47"
tags: ["spec", "homebus", "adapter", "interface", "mvp"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  event-types: "event-types.md"
  database-schema: "database-schema.md"
  beancount-integration: "beancount-integration.md"
---

# Adapter 接口规范 — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-23
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus 三个后端（Grocy、Beancount、Homebox）的 Adapter 统一接口、action catalog、参数/返回 schema。所有 Adapter 实现 `AdapterBase`，暴露 `execute(action, params) -> dict`。

## Requirements

- **FR-1**: 所有 Adapter 实现统一接口 `execute(action, params) -> {success, data?, error?}`
- **FR-2**: 每个 Adapter 支持列出所有 action 元数据（`list_actions() -> list[ActionMeta]`）
- **FR-3**: 每个 Adapter 提供 `health_check() -> {healthy, detail}`

## Design

### AdapterBase

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ActionMeta:
    name: str
    description: str
    params_schema: dict   # JSON Schema
    returns_schema: dict  # JSON Schema

class AdapterBase(ABC):
    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        """执行操作，返回 {success: bool, data: dict, error: str}"""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """健康检查，返回 {healthy: bool, detail: str}"""
        ...

    @abstractmethod
    def list_actions(self) -> list[ActionMeta]:
        """返回此 adapter 支持的所有 action"""
        ...
```

### 统一返回格式

```json
// 成功
{"success": true, "data": {...}}

// 失败
{"success": false, "error": "Grocy API timeout"}

// 幂等命中（仅 query 场景）
{"success": true, "data": {...}, "duplicate": true}
```

---

## Action Catalog

### Grocy Adapter

| action | 描述 | 调用方向 | 幂等性 |
|--------|------|---------|--------|
| `add_stock` | 库存增加 | 写 | 否（每次调用都执行） |
| `consume_stock` | 消耗库存 | 写 | 否 |
| `stock_query` | 查询库存 | 读 | 是（N/A） |

#### `add_stock`

```json
// params
{
  "items": [
    {
      "name": "牛奶",              // 物品名称
      "quantity": 3,               // 数量
      "unit": "盒",                // 单位
      "grocy_product_id": null,    // 可选：指定 Grocy 产品 ID
      "location": "厨房"           // 可选：默认位置（来自 routing registry）
    }
  ]
}

// returns (success)
{
  "success": true,
  "data": {
    "added": [
      {"name": "牛奶", "product_id": 5, "quantity": 3}
    ]
  }
}

// returns (failure — 映射失败或 API 超时)
{
  "success": false,
  "error": "产品'蒙牛纯牛奶'在 Grocy 中不存在"
}
```

名称到 `product_id` 的映射：先查 `grocy-cli` 缓存（`~/.config/grocy/cache.yaml`），再查 Grocy API `/api/objects/products`。缓存未命中时查询 API 并更新缓存。

**映射失败策略（fail-fast）**：产品名称在 Grocy 中不存在时，**直接返回 error**，阻塞整个事件。不做静默跳过——这是 security-by-design：Agent 收到 failed 后可以补救（先在 Grocy 创建产品再重试 publish），避免 silent data loss。

#### `consume_stock`

```json
// params
{
  "items": [
    {
      "name": "牛奶",
      "quantity": 1,
      "unit": "盒",
      "grocy_product_id": null
    }
  ]
}

// returns (success)
{
  "success": true,
  "data": {"consumed": true}
}
```

#### `stock_query`

```json
// params
{
  "product_name": "牛奶"           // 物品名称（优先于 product_id）
  // 或 product_id: 5              // Grocy 产品 ID
}

// returns (success)
{
  "success": true,
  "data": {
    "product_name": "牛奶",
    "product_id": 5,
    "stock": 50,
    "unit": "盒"
  }
}
```

---

### Beancount Adapter

| action | 描述 | 调用方向 | 幂等性 |
|--------|------|---------|--------|
| `record_expense` | 生成购买分录并写入（含 `#homebus` tag + `homebus_event:` meta） | 写 | 是（通过 homebus_event） |
| `delete_entry` | 删除分录（Saga 回滚）| 写 | 是（通过 event_id） |

Beancount Adapter 的 `execute()` 内部调用 `beancount_writer.py` 完成"生成分录文本 + 文件 I/O + bean-check + git commit"的完整链路。Executor 对所有 adapter 统一调用 `adapter.execute(action, params)`，不感知 Beancount 的差异。

#### `record_expense`

```json
// params
{
  "event_id": "evt_sess1_001",
  "date": "2026-07-23",
  "items": [
    {
      "name": "蒙牛纯牛奶",
      "quantity": 3,
      "unit": "盒",
      "category": "consumable",
      "price": 20.0
    }
  ],
  "total_price": 60.0,
  "store": "京东",
  "account": "Expenses:Food:Groceries",      // 来自 routing registry（品类路由）
  "liability": "Liabilities:CreditCard:JD",   // 来自 routing registry（渠道路由）
  "note": null
}

// returns (success)
{
  "success": true,
  "data": {
    "event_id": "evt_sess1_001",
    "file": "~/ledger/2025/0-default/homebus-07.bean",
    "bean_check": true,
    "git_committed": true
  }
}

// returns (幂等命中)
{
  "success": true,
  "data": {
    "event_id": "evt_sess1_001",
    "already_exists": true,
    "file": "~/ledger/2025/0-default/homebus-07.bean"
  }
}
```

#### `delete_entry`

```json
// params (Saga 补偿)
{
  "event_id": "evt_sess1_001"
}

// returns (success)
{
  "success": true,
  "data": {
    "event_id": "evt_sess1_001",
    "removed_from": "~/ledger/2025/0-default/homebus-07.bean",
    "git_committed": true
  }
}
```

内部实现：从 `homebus-MM.bean` 扫描 `homebus_event:` meta 找对应行并进行删除 → `bean-check` → `git commit`。

---

### Homebox Adapter

| action | 描述 | 调用方向 | 幂等性 |
|--------|------|---------|--------|
| `create_asset` | 创建资产记录 | 写 | 否 |
| `delete_asset` | 删除资产（Saga 回滚）| 写 | 否 |

#### `create_asset`

```json
// params
{
  "name": "洗衣机",
  "category": "家电",
  "location": "厨房",           // 来自 routing registry 或 Agent 传入
  "price": 3000.0,
  "purchased_at": "2026-07-23",
  "note": null
}

// returns (success)
{
  "success": true,
  "data": {
    "asset_id": "abc123",
    "name": "洗衣机"
  }
}
```

#### `delete_asset`

```json
// params
{
  "asset_id": "abc123"          // 来自 create_asset 的返回值
}

// returns (success)
{
  "success": true,
  "data": {"deleted": true}
}

// returns (success — 资产已不存在，目标已达成)
{
  "success": true,
  "data": {"deleted": false, "note": "asset already deleted"}
}
```

**幂等处理**：Saga 补偿调用 `delete_asset` 时，如果 Homebox API 返回 404（资产已手动删除或已被上一次补偿删除），视为**成功**——补偿语义的目标是"该资产不应存在"，状态已达成。附带 `note` 字段供日志审计。

---

### Health Check

```
Grocy:       GET {base_url}/api/system/info       timeout 5s
Homebox:     GET {base_url}/api/v1/status         timeout 5s
Beancount:   检查 ledger_path 目录存在 + .bean 文件可读
             + which bean-check（非 HTTP）       timeout 1s
```

Beancount v0.1 不走 HTTP 健康检查（没有 Fava），改为检查文件系统可达性 + `bean-check` 命令可用性。`bean-check` 版本号通过 `detail` 字段返回。

```json
{
  "status": "healthy",
  "adapters": {
    "grocy": "ok",
    "beancount": {"status": "ok", "detail": "bean-check v2.3.6"},
    "homebox": "ok"
  }
}
```

---

### 调用约定

Executor 统一通过 `adapter.execute(action, params)` 调用所有 adapter：

```python
# executor.py
for subtask in layer:
    adapter = self.adapters[subtask.service]
    result = await adapter.execute(subtask.action, subtask.params)
    await self._record_execution_result(subtask, result)
    if not result["success"]:
        await self.saga.compensate(event_id, completed_subtasks)
        return
```

Saga 补偿也走同样的 `adapter.execute()` 调用路径，不复用 Executor 的 DAG 逻辑（避免循环依赖）。Saga 直接逐个执行补偿操作：

```python
# saga.py

COMPENSATION_MAP = {
    ("grocy", "add_stock"): {
        "action": "consume_stock",
        "params": lambda original: {
            **original["params"],
            "items": [{**i, "quantity": -i["quantity"]} for i in original["params"]["items"]]
        }
    },
    ("beancount", "record_expense"): {
        "action": "delete_entry",
        "params": lambda original: {
            "event_id": original["params"]["event_id"]
        }
    },
    ("homebox", "create_asset"): {
        "action": "delete_asset",
        "params": lambda original, result: {
            "asset_id": result["data"]["asset_id"]
        }
    },
}

def _derive_compensation(subtask):
    key = (subtask["service"], subtask["action"])
    if key not in COMPENSATION_MAP:
        raise UncompensatableError(key)
    mapping = COMPENSATION_MAP[key]
    params = mapping["params"](subtask["params"], subtask.get("result"))
    return {"service": subtask["service"], "action": mapping["action"], "params": params}
```

### 补偿语义的差异化

三个后端的本质属性导致补偿语义不同：

| 后端 | 补偿方式 | 语义 | 原因 |
|------|---------|------|------|
| Beancount | 删除 entry 行 | **undo** — 回到写入前状态 | `.bean` 文件允许物理删除 |
| Grocy | 新增反向记录（`consume_stock(-N)`）| **reverse** — 新增抵消操作 | Grocy 是操作日志系统，add/consume 都是不可变记录 |
| Homebox | DELETE 资产 | **undo** — 回到创建前状态 | REST API 允许物理删除 |

> **Grocy 产品创建**：未来如果 Support 自动创建产品 + 入库，补偿时**不删除产品**——只扣减库存。Saga 补偿只还原"量变"（库存数量），不还原"质变"（产品是否存在）。删除产品会丢失用户手动附加的元数据（保质期、最低库存等）。

## Open Questions

- [ ] `depends_on` 执行依赖关系如何建模？是 Executor 消费 `depends_on` 字段还是在另一个独立结构中
- [ ] Saga 补偿操作的 `depends_on` 是否总是为空？（Saga 直接串行执行补偿）
