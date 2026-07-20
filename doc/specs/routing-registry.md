---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "routing", "observation", "registry"]
type: spec
related:
  prd: "doc/prd/homebus-v0.1.md"
  event-types: "doc/specs/event-types.md"
  c4-core: "doc/c4/component-core.md"
---

# HomeBus 观测面与路由注册表 — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-20
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus 的观测面（Observation）与路由注册表（Routing Registry）的概念模型、数据结构和交互流程。

解决的核心问题：三个后端系统（Grocy、Beancount、Homebox）各自维护独立的数据模型和概念体系，Agent / 用户不需要理解这些差异，通过"观测面"以自然语言描述的方式获取跨系统聚合信息。

## 概念模型

### 三系统概念交集

```
                    ┌──────────────────┐
                    │   采购地点/价格   │ ← 三系统交集
                    │  (store, price)  │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐       ┌─────▼──────┐       ┌────▼─────┐
   │  Grocy   │       │  Beancount │       │ Homebox  │
   │          │       │            │       │          │
   │ 库存数量 │       │ 财务流水   │       │ 资产状态 │
   │ 储物位置 │←─────→│ 会计科目   │       │ 储物位置 │←─ Grocy/Homebox 交集
   │ 产品层级 │       │ 交易对手方 │       │ 资产类别 │
   │ 过期管理 │       │ 账户平衡   │       │ 购入价格 │←─ 三系统交集
   │ 价格     │       │ 价格       │       │          │
   └──────────┘       └────────────┘       └──────────┘
```

**关键认识**:

- **三系统交集**: 采购地点（store）和物品价格（price）是所有系统共同关心的
- **Grocy ↔ Homebox 交集**: 储物位置（location）——消耗品储存在哪、耐用资产放在哪
- **Beancount 的独特角色**: 不记录物品归属状态，而是财务状态。它与其他系统的对齐点不是位置，而是**路由规则**——什么品类该记到什么科目、什么渠道走什么负债账户

### 观测面（Observation）

观测面是 HomeBus 在三个后端系统之上架设的**统一抽象层**。一个观测面对应一个用户关心的自然语言概念。

**举例**:

| 观测面 | 含义 | Grocy 映射 | Beancount 映射 | Homebox 映射 |
|--------|------|-----------|---------------|-------------|
| "零食" | 零食类消耗品的库存与支出 | 父产品: 零食 | 科目: Expenses:Food:Snacks | — |
| "生鲜" | 生鲜类食品 | 父产品: 生鲜 | 科目: Expenses:Food:Groceries | — |
| "厨房" | 厨房整体状态 | 位置: 厨房 | 科目: Expenses:Food:Groceries | 位置: 厨房 |
| "家电" | 家电类耐用品 | — | 科目: Expenses:Home:Appliances | 类别: 家电 |

**观测面的核心能力**:

1. **跨系统聚合查询**: Agent 说"查零食"，HomeBus 同时查 Grocy（库存量）+ Beancount（支出），返回聚合结果
2. **语义路由**: 事件推导时，观测面提供各系统的默认参数（默认位置、默认科目）
3. **调谐基准** (v0.3): 对账引擎以观测面为单位做交叉验证
4. **可演进**: 新增观测面 = 加一行配置，不改代码

## 数据结构

### 路由注册表（Routing Registry）

注册表分为两个主要维度：**观测面定义** 和 **路由规则**。

#### 观测面定义

```toml
# ~/.config/homebus/registry.toml
# 观测面定义 —— Agent / 用户用自然语言查询的统一入口

[observations]

[observations.snacks]
name = "零食"
description = "零食类消耗品的库存与支出"
unit = "件"

[observations.snacks.grocy]
parent_product = "零食"
location = "厨房"

[observations.snacks.beancount]
account = "Expenses:Food:Snacks"
unit = "元"

[observations.fresh]
name = "生鲜"
description = "生鲜类食品（肉、菜、水果）"
unit = "斤"

[observations.fresh.grocy]
parent_product = "生鲜"
location = "冰箱"

[observations.fresh.beancount]
account = "Expenses:Food:Groceries"

[observations.kitchen]
name = "厨房"
description = "厨房整体状态（消耗品库存 + 设备资产 + 支出）"

[observations.kitchen.grocy]
location = "厨房"

[observations.kitchen.beancount]
account = "Expenses:Food:Groceries"

[observations.kitchen.homebox]
location = "厨房"

[observations.appliances]
name = "家电"
description = "家电类耐用品"

[observations.appliances.beancount]
account = "Expenses:Home:Appliances"

[observations.appliances.homebox]
category = "家电"
unit = "台"

[observations.beverages]
name = "饮品"
description = "饮品（水、饮料、奶制品）"
unit = "瓶"

[observations.beverages.grocy]
parent_product = "饮品"
location = "冰箱"

[observations.beverages.beancount]
account = "Expenses:Food:Beverages"
```

#### 路由规则

```toml
# 路由规则 —— 事件分发时的默认映射

[routing]

# 品类 → 默认路由
[routing.categories]

[routing.categories.consumable]
default_grocy_location = "厨房"
default_beancount_account = "Expenses:Food:Groceries"
homebox_enabled = false

[routing.categories.durable]
default_grocy_location = "客厅"
default_beancount_account = "Expenses:Home:Appliances"
default_homebox_location = "客厅"

# 采购渠道 → Beancount 负债账户
[routing.stores]

[routing.stores.JD]
beancount_liability = "Liabilities:CreditCard:JD"

[routing.stores.美团]
beancount_liability = "Liabilities:CreditCard:MB"

[routing.stores.现金]
beancount_liability = "Assets:Cash"

# 产品级覆盖（精确匹配，优先级高于品类默认）
# [routing.overrides]
# [routing.overrides."蒙牛纯牛奶"]
# grocy_product_id = "5"
# beancount_account_override = "Expenses:Food:Milk"
```

#### 存储方式

| 项目 | 内容 | 格式 | 位置 |
|------|------|------|------|
| 注册表配置 | 观测面 + 路由规则 | TOML | `~/.config/homebus/registry.toml` |
| 运行时缓存 | MVCC 读缓存 | 内存 dict | HomeBus 进程内 |
| 默认内置 | MVP 初始配置 | 嵌入代码 | `homebus/defaults/registry.toml` |
| 环境覆盖 | 高频覆盖项 | 环境变量 | e.g. `HOMEBUS_DEFAULT_BEANCOUNT_ACCOUNT` |

**MVP 阶段**: 注册表以 TOML 文件配置，HomeBus 启动时加载到内存缓存。不做热加载（v0.1 不做），变更需重启。

**配置路径**: 遵循 XDG 规范，与 `config.toml` 同目录：`$XDG_CONFIG_HOME/homebus/registry.toml`

### 注册表加载策略

```
① 内置默认值 (homebus/defaults/registry.toml)
    ↓  合并
② 用户配置 (~/.config/homebus/registry.toml)
    ↓  用户配置优先级更高，同键覆盖
③ 环境变量覆盖 (HOMEBUS_REGISTRY_OVERRIDE_*)
    ↓
最终注册表 (进程内存缓存，只读)
```

用户只需配置跟默认值不同的项。例如只自定义"零食"的科目：

```toml
# ~/.config/homebus/registry.toml
# 只覆盖需要调整的项，其余用默认

[observations.snacks.beancount]
account = "Expenses:Food:零食"  # 覆盖默认科目
```

## 核心数据流

### 数据流 1: Agent 通过观测面查询

```
Hermes: "看看零食还有多少"
                │
                ▼
Agent 解析意图 → "观测面查询: 零食"
                │
                ▼
homebus query observation snacks
                │
                ▼
HomeBus API: POST /v1/query
  {
    "target": "observation",
    "params": {"name": "snacks"}
  }
                │
                ▼
Query Router → 查找 Registry 中 observation=snacks
                │
                ├─ grocy.parent_product="零食" → Grocy Adapter: query stock by parent
                │    → 返回: {total_stock: 12, unit: "件"}
                │
                ├─ beancount.account="Expenses:Food:Snacks" → Beancount Adapter
                │    → 返回: {total_spent: 320, period: "2026-07", unit: "元"}
                │
                └─ homebox: null (零食不入资产库)
                │
                ▼
Aggregator → 合并结果
                │
                ▼
查询日志: INSERT INTO events (intent=query, target=observation.snacks)
                │
                ▼
Agent 收到:
  "零食库存还有 12 件，本月花了 320 元"
                │
                ▼
Hermes → 用户: "零食还有 12 件，这个月零食花了 320 块"
```

### 数据流 2: 事件分发时使用路由规则

```
Agent: "买了箱牛奶，60 块，京东"
                │
                ▼
homebus publish --body '{
  "intent": "purchase",
  "items": [{"name": "牛奶", "category": "consumable", "quantity": 1, "unit": "箱", "price": 60}],
  "total_price": 60,
  "store": "京东"
}'
                │
                ▼
Dispatch Engine → 查阅 Routing Registry
                │
                ├─ category=consumable → default_grocy_location="厨房"
                │                       → default_beancount_account="Expenses:Food:Groceries"
                │                       → homebox_enabled=false
                │
                ├─ store="京东" → beancount_liability="Liabilities:CreditCard:JD"
                │
                └─ 推导子任务:
                   ① Grocy: add_stock(item=牛奶, location=厨房, quantity=1)
                   ② Beancount: record_expense(
                        account=Expenses:Food:Groceries,
                        liability=Liabilities:CreditCard:JD,
                        amount=60
                      )
```

### 数据流 3: 调谐引擎使用观测面（v0.3 规划）

```
调谐引擎按观测面执行对账：

Observation: "零食"
  ├─ Grocy 报告: 零食类库存余量 = 12 件
  ├─ Beancount 报告: 零食类近 7 天支出 = 80 元
  │
  └─ 调谐逻辑:
       ├─ 库存下降速度 vs 购买频率是否匹配
       ├─ 有购买记录但库存未增加 → 补偿事件
       └─ 有库存增加但无购买记录 → 标注待确认
```

## API 接口

### 查询观测面

```
POST /v1/query
{
  "target": "observation",
  "params": {
    "name": "snacks",
    "period": "2026-07"  // 可选，默认当月
  }
}

Response:
{
  "data": {
    "observation": "snacks",
    "description": "零食类消耗品的库存与支出",
    "grocy": {
      "total_stock": 12,
      "unit": "件",
      "parent_product": "零食"
    },
    "beancount": {
      "total_spent": 320,
      "unit": "元",
      "account": "Expenses:Food:Snacks"
    }
  },
  "event_id": "evt_q_003"
}
```

### 列出观测面

```
POST /v1/query
{
  "target": "observation",
  "params": {
    "list": true    // 列出所有可用观测面
  }
}

Response:
{
  "data": {
    "observations": [
      {"name": "snacks", "description": "零食类消耗品", "unit": "件"},
      {"name": "fresh", "description": "生鲜类食品", "unit": "斤"},
      {"name": "kitchen", "description": "厨房整体状态"},
      {"name": "appliances", "description": "家电类耐用品", "unit": "台"},
      {"name": "beverages", "description": "饮品", "unit": "瓶"}
    ]
  },
  "event_id": "evt_q_004"
}
```

### CLI 命令

```bash
# 查询观测面
homebus query observation snacks
homebus query observation kitchen --period 2026-07

# 列出所有观测面
homebus query observation --list

# 查询仍保留原始后端查询（低层级）
homebus query grocy stock --filter '{"product_id": "5"}'
```

## 组件架构（新增/变更）

在现有的 C4 component-core 基础上新增以下组件：

### 新增: 观测面引擎 (Observation Engine)

| 属性 | 值 |
|------|------|
| **职责** | 处理观测面查询（observation target），跨系统聚合结果 |
| **输入** | `{target: "observation", params: {name, period}}` |
| **输出** | `{observation, grocy?, beancount?, homebox?}` 聚合结果 |
| **挂载点** | 插入在 Query Router 之后、Adapter 调用之前 |

**工作流程**:

```
Query Router 收到 target=observation
        │
        ▼
Observation Engine
        │
        ├─ 查 Registry → 解析观测面的后端映射
        ├─ 为每个有映射的后端构造 Adapter 查询
        ├─ asyncio.gather 并行查询
        ├─ 聚合结果
        └─ 返回统一响应
```

### 新增: 路由注册表 (Routing Registry)

| 属性 | 值 |
|------|------|
| **职责** | 管理观测面定义和路由规则的加载、缓存、查询 |
| **加载时机** | HomeBus 启动时从 `registry.toml` 加载 |
| **存储** | 进程内存缓存（只读，MVP 不做热加载） |
| **调用方** | Dispatch Engine（事件分发时查路由）+ Observation Engine（查询时查映射） |

### 变更: 调度引擎 (Dispatch Engine)

在原有的推导逻辑之前增加一步：**查阅注册表获取路由参数**。

```
Dispatch Engine 收到事件
        │
        ├─ 1. 查 Routing Registry
        │      ├─ event.items[].category → routing.categories
        │      ├─ event.store → routing.stores
        │      └─ 合并默认值到子任务参数
        │
        ├─ 2. 推导子任务清单 (原有逻辑)
        │
        └─ 3. 创建 executions
```

## MVP 实现边界

| 功能 | MVP v0.1 | 未来 |
|------|----------|------|
| 观测面查询 | ✅ 基础查询（按 name 精确匹配） | 模糊搜索、自然语言匹配 |
| 观测面列表 | ✅ 列出所有可用观测面 | — |
| 路由注册表加载 | ✅ 启动时从 TOML 文件加载 | 热加载、API 管理 |
| 调度引擎查路由 | ✅ Dispatch 查阅注册表 | 高级规则（条件分支） |
| 默认内置注册表 | ✅ 嵌入 `homebus/defaults/registry.toml` | 支持用户配置覆盖 |
| 调谐引擎使用观测面 | ❌ | v0.3 |
| 注册表热加载 | ❌ | v0.2+ |
| 产品级覆盖（override） | ❌ | v0.2+ |
| 观测面聚合缓存 | ❌ | 按需 |

## 与现有事件模型的对接

### purchase 事件的完整路由流程

```
Agent 提交 purchase 事件:
  items[0] = {name: "牛奶", category: "consumable", ...}
  store = "京东"
        │
        ▼
Dispatch Engine:
  ① 查 Registry.routing.categories.consumable
     → default_grocy_location: "厨房"
     → default_beancount_account: "Expenses:Food:Groceries"
     → homebox_enabled: false
  ② 查 Registry.routing.stores.京东
     → beancount_liability: "Liabilities:CreditCard:JD"
  ③ 推导子任务:
     sub_task_1:
       service: grocy
       action: add_stock
       params: {product: "牛奶", location: "厨房", quantity: 1}
     sub_task_2:
       service: beancount
       action: record_expense
       params: {
         account: "Expenses:Food:Groceries",
         liability: "Liabilities:CreditCard:JD",
         items: [{name: "牛奶", price: 60}],
         total: 60
       }
```

### consume 事件的路由流程

```
Agent 提交 consume 事件:
  items[0] = {name: "牛奶", quantity: 1, ...}
        │
        ▼
Dispatch Engine:
  ① 查 Registry (consume 不需要路由——它只涉及 Grocy)
  ② 推导子任务:
     sub_task_1:
       service: grocy
       action: consume_stock
       params: {product: "牛奶", quantity: 1}
```

## 配置示例

### 最小配置（仅覆盖链路账户）

```toml
# ~/.config/homebus/registry.toml
# 用户自定义覆盖。未配置的项使用内置默认值

[observations.snacks.beancount]
account = "Expenses:Food:零食"

[routing.stores.京东]
beancount_liability = "Liabilities:CreditCard:京东白条"
```

### 完整配置（内置默认值，用户无需手动创建）

```toml
# homebus/defaults/registry.toml
# 内置默认注册表。用户的自定义配置与这份 merge（同键覆盖）
```

## 实现清单

| 文件 | 职责 |
|------|------|
| `homebus/registry.py` | 注册表加载、缓存、查询接口 |
| `homebus/engine.py` | 观测面引擎（跨系统聚合查询） |
| `homebus/defaults/registry.toml` | 内置默认注册表（MVP 初始配置） |
| `registry.toml.example` | 用户自定义注册表示例（提交到 git） |
| 更新 `homebus/dispatch.py` | Dispatch Engine 集成注册表查询 |
| 更新 `homebus/query_router.py` | Query Router 集成 observation target |
| 更新 `homebus/api.py` | 注册表管理端点（v0.2+） |
