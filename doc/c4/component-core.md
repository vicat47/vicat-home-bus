---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["c4", "homebus", "component", "core"]
related:
  container: "doc/c4/container.md"
  specs: "doc/specs/homebus.md"
---

# C4 Level 3: Components — HomeBus API Server 核心引擎

> HomeBus API Server 的内部组件分解。这是整个系统的核心。

## 组件结构图

```
┌──────────────────────────────────────────────────────────────────┐
│  HomeBus API Server (FastAPI)                                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Layer                                               │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │
│  │  │ POST       │  │ GET        │  │ POST       │        │    │
│  │  │ /v1/events │  │ /v1/events │  │ /v1/query  │        │    │
│  │  │            │  │ /{evt_id}  │  │            │        │    │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │    │
│  └────────┼───────────────┼───────────────┼────────────────┘    │
│           │               │               │                     │
│           ▼               │               ▼                     │
│  ┌──────────────────┐     │    ┌──────────────────────┐        │
│  │  事件校验器        │     │    │  查询路由            │        │
│  │  Event Validator │     │    │  Query Router        │        │
│  │  - Schema校验     │     │    │  - 目标路由           │        │
│  │  - 幂等检查       │     │    │  - 参数转发           │        │
│  │  - 格式标准化     │     │    │  - 查询日志记录        │        │
│  └────────┬─────────┘     │    └──────────┬───────────┘        │
│           │               │               │                     │
│           ▼               │               ▼                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  事件写入器 (Event Writer)                                    ││
│  │  - 写入 events 表 (status=pending)                           ││
│  │  - 分配 event_id (Agent 未提供时自动生成)                     ││
│  │  - 返回 accepted 响应                                         ││
│  └────────────────────────┬────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  调度引擎 (Dispatch Engine)                                   ││
│  │  - 根据 intent + items category 推导子任务清单                 ││
│  │  - 标记子任务间依赖关系 (并行/串行)                              ││
│  │  - 创建 executions 表记录 (status=pending)                    ││
│  │  - 投递到任务执行池                                            ││
│  └────────────────────────┬────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  任务执行器 (Task Executor)                                   ││
│  │  - 根据并行/串行配置执行子任务                                  ││
│  │  - 每个子任务独立 timeout                                      ││
│  │  - 重试机制 (可配置次数)                                       ││
│  │  - 更新 executions 表状态                                     ││
│  └──────┬───────────────────────────────────────┬──────────────┘│
│         │                                       │                 │
│         ▼                                       ▼                 │
│  ┌──────────────┐                     ┌──────────────────┐      │
│  │ Saga 补偿器   │                     │ 结果聚合器        │      │
│  │ - 检测失败     │                     │ Result Aggregator│      │
│  │ - 推导补偿事件  │                     │ - 集合所有 exec   │      │
│  │ - 执行补偿操作  │                     │ - 推导最终状态    │      │
│  │ - 更新事件状态  │                     │ - 更新 events 表 │      │
│  └──────────────┘                     └──────────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Adapter 接口定义层 (Adapter Interface)                       ││
│  │  - Abstract base class / Protocol                           ││
│  │  - execute(action, params) → dict                           ││
│  │  - health_check() → bool                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  数据库层 (Database Layer)                                    ││
│  │  - events 表读写 (aiosqlite)                                  ││
│  │  - executions 表读写 (aiosqlite)                             ││
│  │  - 连接池管理                                                ││
│  │  - WAL 模式 (读写不阻塞)                                      ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## 组件列表

### 1. API Layer

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| POST `/v1/events` | 事件提交入口 | `{intent, items, total_price, ...}` | `{event_id, status, message}` |
| GET `/v1/events/{id}` | 事件状态查询 | `event_id` | `{event_id, status, executions}` |
| POST `/v1/query` | 查询代理入口 | `{target, operation, params}` | `{data, event_id}` |
| GET `/v1/health` | 健康检查 | 无 | `{status, adapters_status}` |

### 2. 事件校验器 (Event Validator)

| 属性 | 值 |
|------|------|
| **职责** | 校验事件格式合法性，检查幂等性 |
| **核心逻辑** | Pydantic schema 校验、event_id 幂等查询 |
| **失败处理** | 格式错误 → 400；重复事件 → 返回已有状态（非错误） |

### 3. 事件写入器 (Event Writer)

| 属性 | 值 |
|------|------|
| **职责** | 将已验证的事件写入 events 表（不可变） |
| **关键行为** | 先写入再响应（保证持久化）、status 初始为 `pending` |
| **数据库交互** | `INSERT INTO events` |

### 4. 调度引擎 (Dispatch Engine)

| 属性 | 值 |
|------|------|
| **职责** | 根据事件类型推导需要分发的后端及操作 |
| **核心逻辑** | 基于 intent + item category 的规则引擎 |

**子任务推导规则：**

| intent | item category | 子任务 1 | 子任务 2 | 调度 |
|--------|--------------|----------|----------|------|
| purchase | consumable | Grocy: add_stock | Beancount: record_expense | 并行 |
| purchase | asset | Homebox: create_item | Beancount: record_asset | 并行 |
| consume | consumable | Grocy: consume_stock | — | 串行 |
| sell | asset | Homebox: mark_sold | Beancount: record_income | 并行 |
| correct | 任意 | 见 Saga 补偿器 | — | 补偿优先 |

### 5. 任务执行器 (Task Executor)

| 属性 | 值 |
|------|------|
| **职责** | 执行子任务，管理并发和超时 |
| **超时** | 每个子任务独立 timeout（默认 30s） |
| **重试** | 失败时幂等重试（默认 3 次） |
| **并发** | 并行子任务使用 asyncio.gather |

### 6. Saga 补偿器 (Saga Compensator)

| 属性 | 值 |
|------|------|
| **职责** | 部分子任务失败时，自动执行已成功子任务的逆向操作 |
| **补偿推导** | 根据原始事件类型 + 已成功的子任务，自动生成补偿操作 |

**补偿推导表：**

| 已完成的操作 | 补偿操作 |
|-------------|---------|
| Grocy: add_stock(item, +N) | Grocy: consume_stock(item, -N) |
| Beancount: record_expense(acct, -CNY) | Beancount: record_correct(acct, +CNY) |
| Beancount: record_asset(acct, +CNY) | Beancount: record_correct(acct, -CNY) |
| Homebox: create_item | Homebox: delete_item / mark_removed |

### 7. 结果聚合器 (Result Aggregator)

| 属性 | 值 |
|------|------|
| **职责** | 集合所有子任务执行结果，推导事件的最终状态 |
| **输出** | success / partial_failed / compensated / failed |

### 8. 查询路由 (Query Router)

| 属性 | 值 |
|------|------|
| **职责** | 将查询请求路由到对应后端，写入查询日志 |
| **不创建 executions** | 查询只写一条 events（intent=query），不创建执行轨迹 |
| **聚合功能** | 未来支持跨后端联合查询（当前仅做路由） |

### 9. Adapter 接口定义层

```python
class AdapterBase(ABC):
    """所有后端适配器的基类"""

    @property
    @abstractmethod
    def service_name(self) -> str:
        """后端服务名称，如 'grocy'、'beancount'、'homebox'"""
        ...

    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        """执行一个操作。action 是枚举值，params 是操作参数。
        返回 {success: bool, data: dict, error: str}"""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """检查后端连通性。返回 {healthy: bool, detail: str}"""
        ...
```

### 10. 数据库层

| 组件 | 职责 |
|------|------|
| events 表读写 | `INSERT`（只增）+ `SELECT`（按 event_id 和状态过滤） |
| executions 表读写 | `INSERT`（追加）+ `UPDATE`（状态变更）+ `SELECT` |
| 连接池 | aiosqlite 连接管理 |
| WAL 模式 | SQLite WAL 模式，读写不相互阻塞 |

---

## 数据流（事件提交流程）

```
Agent CLI
   │  POST /v1/events
   ▼
① API Layer (POST /v1/events)
   │
   ▼
② Event Validator
   │  ├→ 校验 schema (Pydantic)
   │  └→ 幂等检查 (SELECT events WHERE event_id=?)
   │
   ▼
③ Event Writer
   │  ├→ INSERT INTO events (status=pending)
   │  └→ 返回 accepted {event_id}
   │
   ▼
④ Dispatch Engine
   │  ├→ 推导 sub_tasks (规则表)
   │  └→ INSERT INTO executions × N
   │
   ▼
⑤ Task Executor
   │  ├→ asyncio.gather(并行任务)
   │  │   ├→ Grocy Adapter.execute()
   │  │   └→ Beancount Adapter.execute()
   │  ├→ 串行任务按序执行
   │  └→ UPDATE executions (per sub_task)
   │
   ├→ 全部成功 ──→ Result Aggregator
   │                  └→ UPDATE events (status=success)
   │
   └→ 部分失败 ──→ Saga Compensator
                      ├→ 推导补偿操作
                      ├→ 执行补偿（通过 Adapter）
                      └→ UPDATE events (status=compensated)

Agent 轮询 GET /v1/events/{event_id}
                    │
                    ▼
              API Layer → Event Writer (只读SELECT)
                    │
                    ▼
              返回 {event_id, status, executions[]}
```
