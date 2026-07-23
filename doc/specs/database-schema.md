---
status: draft
priority: P0
blocks:
  - homebus/database.py
created: 2026-07-23
updated: 2026-07-23
author: "vicat47"
tags: ["spec", "homebus", "database", "schema", "mvp"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  event-types: "event-types.md"
  homebus: "homebus.md"
---

# HomeBus 数据库 Schema — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-23
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus SQLite 数据库的 DDL、字段约束、索引策略。使用 aiosqlite + WAL 模式，单一连接（aiosqlite 不支持连接池），WAL 下读不阻塞写。

## Requirements

### Functional Requirements

- **FR-1**: `events` 表仅追加（INSERT），状态字段可 UPDATE
- **FR-2**: `executions` 表追加子任务执行记录（INSERT），状态和结果可 UPDATE
- **FR-3**: `event_id` 全局唯一（PRIMARY KEY + UNIQUE 约束）
- **FR-4**: 数据库文件路径由 `config.toml` 的 `homebus.database.path` 指定

### Non-Functional Requirements

- **NFR-1**: WAL 模式，`synchronous=NORMAL`，`journal_mode=WAL`
- **NFR-2**: 数据库路径的父目录不存在时自动创建
- **NFR-3**: 数据库损坏时有明确错误信息（非静默失败）

## Design

### DDL

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
    event_id   TEXT PRIMARY KEY,
    intent     TEXT NOT NULL,
    payload    TEXT NOT NULL,     -- 完整 Event JSON（Pydantic model_dump_json）
    status     TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_created ON events(created_at);

CREATE TABLE IF NOT EXISTS executions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id         TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    service          TEXT NOT NULL,
    action           TEXT NOT NULL,
    params           TEXT NOT NULL,      -- JSON
    depends_on       TEXT DEFAULT '[]',  -- JSON array of seq numbers
    status           TEXT NOT NULL DEFAULT 'pending',
    result           TEXT,               -- JSON
    is_compensation  INTEGER NOT NULL DEFAULT 0,
    retry_count      INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE INDEX idx_executions_event ON executions(event_id);
CREATE INDEX idx_executions_status ON executions(event_id, status);
```

### events 表字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `event_id` | TEXT | PK, NOT NULL | 格式: `evt_<session>_<seq>` |
| `intent` | TEXT | NOT NULL | `purchase` / `consume` / `query` |
| `payload` | TEXT | NOT NULL | 完整 Event JSON，extra fields 保留。v0.2 观测面通过宽表/物化视图索引常用字段 |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | 状态机见 [event-types.md](event-types.md#事件状态机) |
| `created_at` | TEXT | NOT NULL | ISO8601 或 datetime('now') |
| `updated_at` | TEXT | NOT NULL | 每次状态变更时更新 |

### executions 表字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK AUTOINCREMENT | 自增主键 |
| `event_id` | TEXT | NOT NULL, FK→events | 关联的事件 ID |
| `seq` | INTEGER | NOT NULL | 子任务序号（Dispatch 分配，从 0 开始） |
| `service` | TEXT | NOT NULL | `grocy` / `beancount` / `homebox` |
| `action` | TEXT | NOT NULL | 操作名称，见 [adapter-interfaces.md](adapter-interfaces.md) |
| `params` | TEXT | NOT NULL | JSON，传递给 Adapter.execute() 的参数 |
| `depends_on` | TEXT | DEFAULT '[]' | JSON array of seq，依赖的子任务序号列表 |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | 执行状态机 |
| `result` | TEXT | NULL | JSON，Adapter 返回的结果，执行完成后写入 |
| `is_compensation` | INTEGER | NOT NULL, DEFAULT 0 | 0=正常执行，1=补偿操作 |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | 已重试次数 |
| `created_at` | TEXT | NOT NULL | 记录创建时间 |
| `updated_at` | TEXT | NOT NULL | 状态变更时更新 |

### Execution 状态机

```
pending → running → success
                 → failed → retrying → running（最多 max_retries 次）
                 → failed（最终）

success → compensated（被 Saga 回滚时更新原 execution 记录）
```

补偿操作创建**新的** execution 记录（`is_compensation=1`），拥有独立的状态流。被补偿的原 execution 记录的 `status` 从 `success` 更新为 `compensated`。

### events 状态机

详见 [event-types.md](event-types.md#事件状态机)。

## Implementation Details

### 连接管理

```python
import aiosqlite

async def init_db(path: str) -> aiosqlite.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(path)
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA synchronous = NORMAL")
    await db.execute("PRAGMA foreign_keys = ON")
    await db.executescript(DDL)
    return db
```

单一连接（`aiosqlite.connect()`），WAL 模式下读不阻塞写。不对 `db` 做并发共享（单线程异步）。

### 幂等检查

```python
async def event_exists(db, event_id: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM events WHERE event_id = ?", (event_id,)
    )
    return await cursor.fetchone() is not None
```

events 表的 PRIMARY KEY 约束天然保证 `event_id` 唯一，INSERT 重复时触发 `sqlite3.IntegrityError`。

### 查询 API

```python
# 插入事件
await db.execute(
    "INSERT INTO events (event_id, intent, payload) VALUES (?, ?, ?)",
    (event_id, intent, payload_json)
)

# 查询事件状态
cursor = await db.execute(
    "SELECT * FROM events WHERE event_id = ?", (event_id,)
)

# 查询事件的所有 executions
cursor = await db.execute(
    "SELECT * FROM executions WHERE event_id = ? ORDER BY seq",
    (event_id,)
)

# 更新 execution 状态
await db.execute(
    "UPDATE executions SET status = ?, result = ?, updated_at = datetime('now') WHERE event_id = ? AND seq = ?",
    (status, result_json, event_id, seq)
)
```

## Migration Plan

使用 Flyway 式版本化迁移策略（适合不需要回滚的 SQLite 场景）：

```
homebus/
  migrations/
    V001__initial_schema.sql    ← CREATE TABLE events + executions
    V002__add_index_xxx.sql     ← 未来增量变更
```

- **版本表**：`CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))`
- **启动时检查**：查询 `schema_version` 表，按版本号升序执行所有未应用的 `V*.sql` 文件
- **向后兼容**：新增字段用 `ALTER TABLE ADD COLUMN`（SQLite 3.25+ 支持），不修改或删除已有列
- **不需要回滚**：SQLite 嵌入场景无需支持版本回退，只向前迁移

## Open Questions

- [ ] v0.1 → v0.2 是否需要 Alembic？还是简单版本号检查？
- [ ] `payload` 使用 JSON blob vs 展开字段的性能影响是否有评估？
