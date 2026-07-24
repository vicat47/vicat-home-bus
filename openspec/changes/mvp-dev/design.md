# Design: HomeBus v0.1 MVP

## Architecture Overview

```
Agent (终端工具调用)
    │
    ▼
CLI (Click): homebus publish/query/status/health
    │  HTTP (JSON)
    ▼
HomeBus API (FastAPI + uvicorn)
    │
    ├── Validator (Schema + 幂等)
    ├── Events DB (SQLite, WAL)
    ├── Dispatch Engine (子任务推导)
    ├── Task Executor (DAG 分层并发)
    ├── Saga Compensator (失败回滚)
    ├── Result Aggregator (终态推导)
    └── Adapters ─── Grocy / Beancount / Homebox
```

## Module Design

### 1. Data Models (`homebus/models.py`)

Pydantic models for API requests/responses and internal data:

- `EventItem` — 物品项（name, category, quantity, unit, price, extra fields allowed）
- `CreateEventRequest` — 事件提交请求（intent, event_id, items, total_price, store, etc.）
- `EventStatusResponse` — 事件状态响应
- `ExecutionItem` — 执行记录子项
- `QueryRequest` / `QueryResponse` — 查询代理
- `HealthResponse` / `AdapterHealth` — 健康检查
- `ErrorResponse` / `ErrorDetail` / `ErrorCode` — 统一错误格式
- `SubTask` (dataclass) — 内部子任务（seq, service, action, params, depends_on, timeout, max_retries）

### 2. Database (`homebus/database.py`)

- SQLite with WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`)
- Single `aiosqlite` connection (aiosqlite doesn't support pooling)
- Two tables: `events` (immutable, append-only) + `executions` (mutable, append)
- Migration system: versioned SQL files in `homebus/migrations/V001__*.sql`
- CRUD operations:
  - `init_db(path)` — create tables + run migrations
  - `insert_event(db, event)` — INSERT with PK collision detection for idempotency
  - `get_event(db, event_id)` — SELECT by PK
  - `update_event_status(db, event_id, status)` — UPDATE status
  - `insert_executions(db, executions)` — batch INSERT
  - `update_execution(db, event_id, seq, status, result)` — UPDATE single
  - `get_executions(db, event_id)` — SELECT by event_id

### 3. Event Validator (`homebus/validators.py`)

- Pydantic-based schema validation for `CreateEventRequest`
- Field-level rules (intent must be "purchase"/"consume", items non-empty, etc.)
- Idempotency check: if event_id exists in DB → return existing state (HTTP 200, duplicate=true)
- Event ID auto-generation: `evt_<session>_<seq>` if not provided by Agent

### 4. API Layer (`homebus/api.py`)

Four FastAPI endpoints:

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/v1/events` | POST | `CreateEventRequest` | `{event_id, status, message}` |
| `/v1/events/{event_id}` | GET | path param | `EventStatusResponse` |
| `/v1/query` | POST | `QueryRequest` | `{data, event_id}` |
| `/v1/health` | GET | — | `HealthResponse` |

Key implementation details:
- `POST /v1/events`: validate → write events row (status=accepted) → return 200 → BackgroundTasks: dispatch + execute + aggregate
- `GET /v1/events/{event_id}`: query events + executions rows, format response
- `POST /v1/query`: validate → write events row (intent=query) → route to adapter → return
- `GET /v1/health`: call each adapter's `health_check()`, aggregate

### 5. Dispatch Engine (`homebus/dispatch.py`)

Translates intent + items + routing registry → `list[SubTask]` with DAG dependencies.

For `purchase`:
```
L0: seq=0 Grocy add_stock (depends_on=[])
L1: seq=1 Beancount record_expense (depends_on=[0])
L1: seq=2 Homebox create_asset (depends_on=[0], durable items only)
```

For `consume`:
```
L0: seq=0 Grocy consume_stock (depends_on=[])
```

Uses `Registry` for category/store route lookups to fill in default account/location/liability params.

### 6. Task Executor (`homebus/executor.py`)

Executes sub-tasks respecting DAG dependencies:
1. Parse `depends_on` → build DAG
2. Topological sort → `[L0, L1, ..., Ln]`
3. For each layer: `asyncio.gather(...)` all subtasks concurrently
4. Layer failure → cancel in-flight → trigger Saga → stop
5. All layers success → Aggregator sets status=success

Each subtask execution:
- Call `adapter.execute(action, params)`
- Record result to executions table
- Retry on failure (up to `max_retries`)
- Timeout via `asyncio.wait_for`

### 7. Saga Compensator (`homebus/saga.py`)

Compensation map that reverses completed operations when a later step fails:

| Original (service, action) | Compensation (service, action) |
|---------------------------|-------------------------------|
| (grocy, add_stock) | (grocy, consume_stock) with negative quantity |
| (beancount, record_expense) | (beancount, delete_entry) by event_id |
| (homebox, create_asset) | (homebox, delete_asset) by asset_id |

Compensation execution: sequential (not DAG), records as `is_compensation=1` executions. Original successful executions marked `status=compensated`.

Idempotency: `delete_asset` returning 404 = success (asset already doesn't exist, goal achieved).

### 8. Result Aggregator (`homebus/aggregator.py`)

Determines final event status:
- All executions success → `success`
- Some failed, compensation applied successfully → `compensated`
- Some failed, compensation also failed → `failed`
- Updates events table `status` and `updated_at`

### 9. Grocy Adapter (`homebus/adapters/grocy.py`)

Actions: `add_stock`, `consume_stock`, `stock_query`

- Communicates via HTTP REST API (`httpx`)
- Product name → product_id resolution: check `~/.config/grocy/cache.yaml` first, then Grocy API `/api/objects/products`, update cache
- **Fail-fast on unknown products**: error blocks the event, no silent skip
- Health check: `GET {base_url}/api/system/info`, timeout 5s

### 10. Beancount Adapter (`homebus/adapters/beancount.py`)

Actions: `record_expense`, `delete_entry`

- Delegates file I/O to `beancount_writer.py` (shared library, not subprocess)
- Generates Beancount entry text with `#homebus` tag + `homebus_event:` / `homebus_time:` meta
- `record_expense`: writes to `{ledger_path}/{YYYY}/0-default/homebus-{MM}.bean`
- `delete_entry`: scans .bean file for `homebus_event:` meta, removes matching entry
- After each write: run `bean-check`, then `git commit`
- Idempotency: checks `homebus_event:` meta before writing
- Health check: check `ledger_path` directory exists + .bean files readable + `bean-check` available

### 11. Homebox Adapter (`homebus/adapters/homebox.py`)

Actions: `create_asset`, `delete_asset`

- Communicates via HTTP REST API (`httpx`)
- `create_asset`: POST `/api/v1/items` with name, category, location, price
- `delete_asset`: DELETE `/api/v1/items/{id}` — 404 treated as success
- Health check: `GET {base_url}/api/v1/status`, timeout 5s

### 12. Beancount Writer (`homebus/adapters/beancount_writer.py`)

Shared library for Beancount file operations:
- `generate_entry(event_id, date, items, total_price, store, account, liability, note) → str` — generates .bean entry text
- `write_entry(ledger_path, entry_text) → Path` — determines target file path, appends entry
- `find_entry_by_event_id(ledger_path, event_id) → (Path, int) | None` — scans for `homebus_event:` meta
- `delete_entry_by_event_id(ledger_path, event_id) → bool` — removes entry lines from .bean file
- `run_bean_check(ledger_path) → (bool, str)` — validates bean file integrity
- `git_commit(ledger_path, message) → bool` — auto-commits changes

### 13. Routing Registry (`homebus/registry.py`)

Loads `~/.config/homebus/registry.toml` (TOML), provides:
- `get_category_route(category) → CategoryRoute` — default location/account/homebox_enabled
- `get_store_route(store) → StoreRoute | None` — liability account

Graceful degradation: missing file → empty registry → adapters use defaults.

### 14. Query Router (`homebus/query_router.py`)

Routes `POST /v1/query` to appropriate adapter based on `target`:
- `grocy` → `grocy_adapter.execute(operation, params)`
- `beancount` → `beancount_adapter.execute(operation, params)` (v0.1: `verify_entry` only)
- `homebox` → `homebox_adapter.execute(operation, params)`

Query intent writes to events table (intent=query) but NOT to executions table.

### 15. Configuration (`homebus/config.py`)

Pydantic models + TOML loader + environment variable overlay:
- `HomeBusConfig` — nested config (ApiConfig, DatabaseConfig, GrocyConfig, BeancountConfig, HomeboxConfig, CliConfig)
- `load_config(config_path, cli_overrides)` — layered loading: defaults < TOML < env vars < CLI
- `discover_config_path()` — XDG-compliant config discovery
- Sensitive fields (API keys, tokens) only via environment variables, never in config.toml

### 16. CLI (`cli/homebus.py`)

Click-based CLI with 5 commands:
- `homebus publish` — submit event (--body JSON or --file path)
- `homebus status` — query event status (--event-id, --watch, --timeout)
- `homebus query` — query backend (--target, --operation, --params)
- `homebus health` — health check
- `homebus init` — generate config.toml + registry.toml + .env.example

All output to stdout as JSON, errors to stderr. Exit code 0=success, non-zero=failure.

## Data Flow (Purchase Example)

```
Agent: homebus publish --body '{"intent":"purchase","items":[...],"total_price":60}'
    │
    ▼
CLI → HTTP POST /v1/events
    │
    ▼
Validator: Schema check + idempotency check ✓
    │
    ▼
Database: INSERT INTO events (status='accepted')
    │
    ▼
API Response: {"event_id": "evt_sess1_001", "status": "accepted"}
    │
    ▼ (BackgroundTask)
Dispatch: intent=purchase + items → 3 SubTasks with DAG
    │
    ├── L0: Grocy add_stock → success
    │       ├── L1: Beancount record_expense → success
    │       └── L1: Homebox create_asset → success
    │
    ▼
Aggregator: all success → status='success'
    │
    ▼
Database: UPDATE events SET status='success'
    │
    ▼
Agent: homebus status --event-id evt_sess1_001 → {"status":"success", ...}
```

## Event Status Machine

```
accepted → executing → success
                     → compensated (Saga回滚成功)
                     → failed (无法补偿)

Non-terminal states: accepted, executing
Terminal states: success, compensated, failed (irreversible)
```

## Database Schema

```sql
CREATE TABLE events (
    event_id   TEXT PRIMARY KEY,
    intent     TEXT NOT NULL,
    payload    TEXT NOT NULL,     -- Full Event JSON
    status     TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE executions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL,
    seq             INTEGER NOT NULL,
    service         TEXT NOT NULL,
    action          TEXT NOT NULL,
    params          TEXT NOT NULL,      -- JSON
    depends_on      TEXT DEFAULT '[]',  -- JSON array
    status          TEXT NOT NULL DEFAULT 'pending',
    result          TEXT,               -- JSON
    is_compensation INTEGER NOT NULL DEFAULT 0,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
```

## File Structure

```
homebus/
    __init__.py
    models.py          # Pydantic models
    database.py        # SQLite init + CRUD
    config.py          # Config loading (TOML + env)
    api.py             # FastAPI app + routes
    validators.py      # Schema + idempotency validation
    dispatch.py        # Sub-task derivation engine
    executor.py        # DAG-based task executor
    saga.py            # Compensation engine
    aggregator.py      # Result aggregation
    registry.py        # Routing registry (TOML)
    query_router.py    # Query routing
    adapters/
        __init__.py
        base.py        # AdapterBase ABC
        grocy.py       # Grocy adapter
        beancount.py   # Beancount adapter
        homebox.py     # Homebox adapter
        beancount_writer.py  # Beancount file I/O shared lib
    migrations/
        V001__initial_schema.sql
cli/
    __init__.py
    homebus.py         # Click CLI entry
tests/
    __init__.py
    test_models.py
    test_database.py
    test_validators.py
    test_dispatch.py
    test_executor.py
    test_saga.py
    test_aggregator.py
    test_api.py
    test_adapters.py
    test_registry.py
    test_cli.py
    test_integration.py
```

## Implementation Order

Following dependency graph (bottom-up):

1. **Data layer**: `models.py` → `database.py` → `config.py`
2. **Adapter base**: `adapters/base.py`
3. **Adapters**: `grocy.py`, `beancount_writer.py`, `beancount.py`, `homebox.py`
4. **Registry**: `registry.py`
5. **Core engine**: `dispatch.py` → `executor.py` → `saga.py` → `aggregator.py`
6. **Validators**: `validators.py`
7. **API**: `api.py`
8. **Query router**: `query_router.py`
9. **CLI**: `cli/homebus.py`
10. **Tests**: unit → integration → e2e

## Key Design Decisions (from MEMORY.md)

- **D2**: 事件先写再响应 — 防止 Agent 超时重试丢失事件
- **D3**: events + executions 分表 — 不可变 vs 可变生命周期分离
- **D4**: CLI 先行，MCP 后加 — 快速验证闭环
- **D5**: TOML 而非 YAML — Python 3.11 标准库 + Agent 写入确定性
- **D8**: Beancount 走共享库而非 CLI subprocess — 避免循环依赖
- **D9**: Beancount 元数据用 `#homebus` tag（延续现有 `#costflow` 范式）
- **D10**: 事件状态用 `accepted` 而非 `pending` — API 层面 vs execution 层面语义区分
- **D11**: 允许混合品类 purchase — 单笔交易含多 posting
- **D12**: Saga 补偿语义按后端分化 — Beancount undo / Grocy reverse / Homebox undo
- **D13**: Grocy fail-fast — 产品不存在直接报错，不静默跳过
- **D14**: Homebox 补偿幂等 — 404 视为成功
