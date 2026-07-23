---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "routing", "registry"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  event-types: "event-types.md"
  c4-core: "../c4/component-core.md"
  roadmap: "../../ROADMAP.md"
  beancount-integration: "beancount-integration.md"
---

# 路由注册表 — Routing Registry Specification

- **Version**: 0.1.0
- **Date**: 2026-07-20
- **Author**: vicat47
- **Status**: Draft

## Overview

路由注册表（Routing Registry）是 HomeBus 调度引擎（Dispatch Engine）在事件分发时查询路由参数的配置中心。

解决的问题：Agent 提交事件时只提供业务语义（品类、渠道），不指定后端参数（默认储物位置、会计分录、负债账户）。路由注册表提供这些"隐藏参数"的默认值映射。

**MVP 范围**：仅路由规则（观测面查询在 v0.2）

## 路由维度

路由注册表管理三个维度的映射：

| 维度 | 输入 | 输出 | 用途 |
|------|------|------|------|
| 品类路由 | item.category（consumable / durable） | 默认位置 + 默认科目 + 是否同步 Homebox | purchase 事件分发 |
| 渠道路由 | store（"京东"/"美团"/"现金"） | Beancount 负债账户 | purchase 事件记账科目 |
| 产品覆盖（未来 v0.2+） | product_name 精确匹配 | 覆盖品类默认值 | 精细调控 |

这三个维度在 Dispatch Engine 事件分发时**合并**产生每个子任务的完整参数。

## MVP 数据结构（版本控制：v0.1.0）

简化版——只保留 MVP 必需的品类路由 + 渠道路由。

### 品类路由

```toml
[routing.categories]

[routing.categories.consumable]
default_grocy_location = "厨房"
default_beancount_account = "Expenses:Food:Groceries"
homebox_enabled = false

[routing.categories.durable]
default_grocy_location = "客厅"
default_beancount_account = "Expenses:Home:Appliances"
default_homebox_location = "客厅"
homebox_enabled = true
```

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `default_grocy_location` | string | 否 | Grocy 库存默认储存位置名称 |
| `default_beancount_account` | string | 是 | Beancount 默认费用/资产科目 |
| `default_homebox_location` | string | 否 | Homebox 默认资产摆放位置名称（仅 durable） |
| `homebox_enabled` | bool | 是 | 该品类是否同步到 Homebox 资产库 |

### 渠道路由

```toml
[routing.stores]

[routing.stores.JD]
beancount_liability = "Liabilities:CreditCard:JD"

[routing.stores.美团]
beancount_liability = "Liabilities:CreditCard:MB"

[routing.stores.现金]
beancount_liability = "Assets:Cash"

[routing.stores.拼多多]
beancount_liability = "Liabilities:CreditCard:PDD"

[routing.stores.淘宝]
beancount_liability = "Liabilities:CreditCard:TB"

[routing.stores.抖音]
beancount_liability = "Liabilities:CreditCard:DY"

[routing.stores.微信]
beancount_liability = "Liabilities:WeChat"
```

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `beancount_liability` | string | 是 | 该渠道对应的 Beancount 负债账户 |

### 产品覆盖（v0.2+, 预留占位）

```toml
# [routing.overrides]
# [routing.overrides."蒙牛纯牛奶"]
# grocy_product_id = "5"
# beancount_account_override = "Expenses:Food:Milk"
# homebox_location_override = "厨房冰箱"
```

产品覆盖允许精确到 SKU 级别的路由定制。优先级：**Override > 品类默认**。v0.1 不做解析，但 TOML 结构预留，解析时静默忽略。

## 存储与加载

### 文件位置

遵循 XDG 规范：

```
$XDG_CONFIG_HOME/homebus/registry.toml
# 默认: ~/.config/homebus/registry.toml
```

与 `config.toml` 同目录。

### 默认值策略

路由注册表**无内置默认值**——它是用户自定义的配置，不是系统预设。如果某一项没有配置：

- **品类路由**：Dispatch Engine 用空值填充，Adapter 调用时使用后端默认值
- **渠道路由**：Beancount Adapter 使用 `Liabilities:Unknown` 作为兜底
- **产品覆盖**：未被覆盖的产品退回到品类默认

**为什么没有内置默认**：不像日志级别可以预设"INFO"，路由规则完全取决于用户的家庭记账习惯。张三的"零食"走 `Expenses:Food:零食`，李四的"零食"走 `Expenses:零食`——HomeBus 不知道也无法猜。用户首次使用需要 `homebus init` 生成一份模板，用户按自己习惯修改。

### 加载流程

```
① homebus init 生成 registry.toml 模板
        │
② 用户按需编辑（不编辑 = 空文件，使用后端默认值）
        │
③ HomeBus 启动时加载 registry.toml
        │
④ 解析失败 → 日志警告 + 使用空注册表（不退场）
        │
⑤ 运行时内存缓存（只读，不做热加载）
```

### 初始化模板

`homebus init` 生成的内容：

```toml
# ~/.config/homebus/registry.toml
# HomeBus 路由注册表
# 编辑后重启 HomeBus 生效

[routing.categories]

[routing.categories.consumable]
default_grocy_location = ""
default_beancount_account = "Expenses:Food:Groceries"
homebox_enabled = false

[routing.categories.durable]
default_grocy_location = ""
default_beancount_account = "Expenses:Home:Appliances"
default_homebox_location = ""
homebox_enabled = true

[routing.stores]
# [routing.stores.京东]
# beancount_liability = "Liabilities:CreditCard:JD"
# 在下方按需取消注释并修改
```

### 空注册表行为（兜底）

如果 `registry.toml` 不存在或所有配置都为空：

- Dispatch Engine **不报错**，继续分发
- Adapter 调用时使用各自后端 API 的默认参数
- 对用户的影响：purchase 事件仍能写入，但默认位置为空（Grocy 会使用自己的默认位置），默认账户为空（Beancount 用兜底账户）

## 事件分发中的路由流程

### purchase 事件

```
Dispatch Engine 收到 purchase 事件
        │
        ├─ items[].category = "consumable"
        │   ├─ routing.categories.consumable.default_grocy_location → "厨房"
        │   ├─ routing.categories.consumable.default_beancount_account → "Expenses:Food:Groceries"
        │   └─ routing.categories.consumable.homebox_enabled = false → 不下发 Homebox
        │
        ├─ store = "京东"
        │   └─ routing.stores.京东.beancount_liability → "Liabilities:CreditCard:JD"
        │
        └─ 推导子任务:
            ├─ (serially) Grocy: add_stock(
            │     product=牛奶, location="厨房", quantity=1
            │   )
            └─ (parallel) Beancount: record_expense(
                  account="Expenses:Food:Groceries",
                  liability="Liabilities:CreditCard:JD",
                  amount=60
                )
```

### consume 事件

consume 事件不涉及路由——它只跟 Grocy 交互，不需要默认位置/科目。Dispatch Engine 直接推导单任务。

## 组件接口

### Registry 类

```python
# homebus/registry.py

@dataclass
class CategoryRoute:
    default_grocy_location: str = ""
    default_beancount_account: str = ""
    default_homebox_location: str = ""
    homebox_enabled: bool = False

@dataclass
class StoreRoute:
    beancount_liability: str = "Liabilities:Unknown"

@dataclass
class Registry:
    categories: dict[str, CategoryRoute] = field(default_factory=dict)
    stores: dict[str, StoreRoute] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | None = None) -> "Registry":
        """从 TOML 文件加载。文件不存在或解析失败时返回空注册表（不退场）。"""
        ...

    def get_category_route(self, category: str) -> CategoryRoute:
        """获取品类路由。未配置时返回全空 CategoryRoute（后端兜底）。"""
        ...

    def get_store_route(self, store: str) -> StoreRoute | None:
        """获取渠道路由。未配置时返回 None。"""
        ...
```

### Dispatch Engine 集成

```python
# homebus/dispatch.py

class DispatchEngine:
    def __init__(self, registry: Registry, ...):
        self.registry = registry

    def _derive_sub_tasks(self, event: Event) -> list[SubTask]:
        # 1. 查品类路由
        category = event.items[0].category
        cat_route = self.registry.get_category_route(category)

        # 2. 查渠道路由
        store_route = self.registry.get_store_route(event.store)

        # 3. 构造子任务
        if event.intent == "purchase":
            sub_tasks = []

            # Grocy: add_stock（串行）
            grocy_params = {
                "items": [...],
                "location": cat_route.default_grocy_location,  # 可能为空
            }
            sub_tasks.append(SubTask(
                service="grocy", action="add_stock", params=grocy_params
            ))

            # Beancount: record_expense（并行）
            beancount_params = {
                "items": [...],
                "total": event.total_price,
                "account": cat_route.default_beancount_account,
                "liability": store_route.beancount_liability if store_route else None,
            }
            sub_tasks.append(SubTask(
                service="beancount", action="record_expense", params=beancount_params,
                depends_on=[0]  # 依赖 Grocy 先成功
            ))

            return sub_tasks
```

## v0.2 展望：观测面

v0.2 引入的观测面是路由注册表的**互补查询能力**。

### 观测面是什么

观测面（Observation）是语义化的跨系统查询入口。它复用同一个 `registry.toml` 文件，但在 `[observations]` 段定义：

```
[observations]
[observations.snacks]
name = "零食"
description = "零食类库存与支出"

[observations.snacks.grocy]
parent_product = "零食"

[observations.snacks.beancount]
account = "Expenses:Food:Snacks"
```

### 观测面与路由规则的区别

| 维度 | 路由规则（v0.1） | 观测面（v0.2） |
|------|-----------------|---------------|
| **触发时机** | 事件分发时 | 查询请求时 |
| **方向** | 写入（事件→后端） | 读取（查询←后端） |
| **语义** | 品类→默认位置/科目 | 自然语言概念→跨系统聚合 |
| **是否 MVP** | ✅ 是 | ❌ 否 |

### 为什么观测面不做在 MVP

1. **MVP 的 Agent 自己知道查哪个后端**——Agent 说"查查零食还有多少"，它可以直接 `homebus query grocy stock --parent-product 零食` 和 `homebus query beancount balance --account Expenses:Food:Snacks`。观测面只是把这两个步骤合并了
2. **MVP 的后端直查足够用**——查询代理已经能路由到各个后端，Agent 在 semantic layer 之上再加一层封装是这个阶段不需要的
3. **观测面的真正价值**需要后续能力搭配才体现：调谐引擎（v0.3 以观测面为单位对账）和 Agent 的模糊意图解析（用户说"看看厨房"→ Agent 自动选 observation=kitchen）

### 观测面 v0.2 实现路径

```
v0.1 → 路由注册表只存 [routing.*] 段，[observations] 段解析时静默忽略
    ↓
v0.2 → 观测面引擎启动，解析 [observations] 段，暴露
        homebus query observation <name>
        homebus query observation --list
```

## 实现清单

### MVP v0.1

| 文件 | 职责 | 优先级 |
|------|------|--------|
| `homebus/registry.py` | TOML 加载、缓存、查询接口（仅 `[routing.*]`） | P0 |
| `homebus/defaults/init_config.toml` | `homebus init` 生成的模板文件 | P0 |
| `homebus/dispatch.py` 更新 | Dispatch Engine 集成注册表查询路由参数 | P0 |
| 测试 | Registry 加载、空注册表、部分配置 | P1 |

### v0.2

| 文件 | 职责 |
|------|------|
| `homebus/engine.py` | 观测面引擎（跨系统聚合查询） |
| `homebus/registry.py` 更新 | 解析 `[observations]` 段 |
| `homebus/query_router.py` 更新 | 支持 `target=observation` |
| CLI 命令 | `homebus query observation <name>` / `--list` |

## 错误处理策略

| 场景 | 行为 | 日志级别 |
|------|------|---------|
| `registry.toml` 不存在 | 空注册表，正常启动 | INFO |
| TOML 解析语法错误 | 空注册表，正常启动 | WARN |
| 路由规则引用了不存在的 category | 返回空 CategoryRoute，兜底处理 | WARN |
| 渠道路由不存在 | `get_store_route()` 返回 None，Adapter 兜底 | DEBUG |
| 观测面段存在但 v0.1 不解析（v0.2 行为） | v0.1 静默忽略 `[observations]` | DEBUG |
