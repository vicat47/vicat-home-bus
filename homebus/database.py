from __future__ import annotations

import json
import os
from pathlib import Path

import aiosqlite


_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version   INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    event_id   TEXT PRIMARY KEY,
    intent     TEXT NOT NULL,
    payload    TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

CREATE TABLE IF NOT EXISTS executions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id         TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    service          TEXT NOT NULL,
    action           TEXT NOT NULL,
    params           TEXT NOT NULL,
    depends_on       TEXT DEFAULT '[]',
    status           TEXT NOT NULL DEFAULT 'pending',
    result           TEXT,
    is_compensation  INTEGER NOT NULL DEFAULT 0,
    retry_count      INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_executions_event ON executions(event_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(event_id, status);
"""


async def _apply_migrations(db: aiosqlite.Connection) -> None:
    cursor = await db.execute(
        "SELECT MAX(version) FROM schema_version"
    )
    row = await cursor.fetchone()
    current_version = row[0] if row[0] is not None else 0

    if not _MIGRATIONS_DIR.exists():
        return

    migration_files = sorted(_MIGRATIONS_DIR.glob("V*.sql"))
    for mf in migration_files:
        version_str = mf.stem.split("__")[0].lstrip("V")
        try:
            version = int(version_str)
        except ValueError:
            continue
        if version > current_version:
            sql = mf.read_text(encoding="utf-8")
            await db.executescript(sql)
            await db.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (version,),
            )
            await db.commit()


async def init_db(path: str) -> aiosqlite.Connection:
    path_obj = Path(path).expanduser().resolve()
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(path_obj))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA synchronous = NORMAL")
    await db.execute("PRAGMA foreign_keys = ON")
    await db.executescript(_DDL)
    await _apply_migrations(db)
    await db.commit()
    return db


async def insert_event(
    db: aiosqlite.Connection, event_id: str, intent: str, payload_json: str
) -> bool:
    try:
        await db.execute(
            "INSERT INTO events (event_id, intent, payload) VALUES (?, ?, ?)",
            (event_id, intent, payload_json),
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def get_event(db: aiosqlite.Connection, event_id: str) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM events WHERE event_id = ?", (event_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def update_event_status(
    db: aiosqlite.Connection, event_id: str, status: str
) -> None:
    await db.execute(
        "UPDATE events SET status = ?, updated_at = datetime('now') WHERE event_id = ?",
        (status, event_id),
    )
    await db.commit()


async def insert_executions(
    db: aiosqlite.Connection,
    subtasks: list,
    event_id: str,
    is_compensation: int = 0,
) -> None:
    for st in subtasks:
        params_json = json.dumps(st.params, ensure_ascii=False)
        depends_json = json.dumps(st.depends_on, ensure_ascii=False)
        await db.execute(
            """INSERT INTO executions
               (event_id, seq, service, action, params, depends_on,
                status, is_compensation, retry_count)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (
                event_id,
                st.seq,
                st.service,
                st.action,
                params_json,
                depends_json,
                is_compensation,
                0,
            ),
        )
    await db.commit()


async def update_execution(
    db: aiosqlite.Connection,
    event_id: str,
    seq: int,
    status: str,
    result: dict | None = None,
    retry_count: int | None = None,
) -> None:
    result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
    if retry_count is not None:
        await db.execute(
            """UPDATE executions
               SET status = ?, result = ?, retry_count = ?,
                   updated_at = datetime('now')
               WHERE event_id = ? AND seq = ?""",
            (status, result_json, retry_count, event_id, seq),
        )
    else:
        await db.execute(
            """UPDATE executions
               SET status = ?, result = ?, updated_at = datetime('now')
               WHERE event_id = ? AND seq = ?""",
            (status, result_json, event_id, seq),
        )
    await db.commit()


async def get_executions(
    db: aiosqlite.Connection, event_id: str
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM executions WHERE event_id = ? ORDER BY seq",
        (event_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
