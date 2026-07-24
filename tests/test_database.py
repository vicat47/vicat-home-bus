import json
import tempfile
from pathlib import Path

import pytest

from homebus.database import (
    get_event,
    get_executions,
    init_db,
    insert_event,
    insert_executions,
    update_event_status,
    update_execution,
)
from homebus.models import SubTask


@pytest.fixture
async def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = await init_db(db_path)
    yield conn
    await conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_insert_and_get_event(db):
    inserted = await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    assert inserted is True

    event = await get_event(db, "evt_001")
    assert event is not None
    assert event["event_id"] == "evt_001"
    assert event["intent"] == "purchase"
    assert event["status"] == "accepted"


@pytest.mark.asyncio
async def test_duplicate_event_id(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    inserted = await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    assert inserted is False


@pytest.mark.asyncio
async def test_get_nonexistent_event(db):
    event = await get_event(db, "nonexistent")
    assert event is None


@pytest.mark.asyncio
async def test_update_event_status(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    await update_event_status(db, "evt_001", "success")
    event = await get_event(db, "evt_001")
    assert event["status"] == "success"


@pytest.mark.asyncio
async def test_insert_and_get_executions(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')

    subtasks = [
        SubTask(seq=0, service="grocy", action="add_stock", params={"items": []}),
        SubTask(seq=1, service="beancount", action="record_expense",
                params={"total": 100}, depends_on=[0]),
    ]
    await insert_executions(db, subtasks, "evt_001")

    executions = await get_executions(db, "evt_001")
    assert len(executions) == 2
    assert executions[0]["seq"] == 0
    assert executions[0]["status"] == "pending"
    assert executions[1]["depends_on"] == "[0]"


@pytest.mark.asyncio
async def test_update_execution(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    st = SubTask(seq=0, service="grocy", action="add_stock", params={})
    await insert_executions(db, [st], "evt_001")

    await update_execution(db, "evt_001", 0, "success", {"added": []})
    executions = await get_executions(db, "evt_001")
    assert executions[0]["status"] == "success"
