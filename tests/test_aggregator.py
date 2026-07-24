import tempfile
from pathlib import Path

import pytest

from homebus.aggregator import Aggregator
from homebus.database import init_db, insert_event, insert_executions, update_execution
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
async def test_aggregate_all_success(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    st = SubTask(seq=0, service="grocy", action="add_stock", params={})
    await insert_executions(db, [st], "evt_001")
    await update_execution(db, "evt_001", 0, "success", {"added": []})

    agg = Aggregator(db)
    status = await agg.aggregate("evt_001")
    assert status == "success"


@pytest.mark.asyncio
async def test_aggregate_with_compensation(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    st = SubTask(seq=0, service="grocy", action="add_stock", params={})
    await insert_executions(db, [st], "evt_001")
    await update_execution(db, "evt_001", 0, "failed", {"error": "x"})

    comp_st = SubTask(seq=1000, service="grocy", action="consume_stock", params={})
    await insert_executions(db, [comp_st], "evt_001", is_compensation=1)
    await update_execution(db, "evt_001", 1000, "success", {})

    agg = Aggregator(db)
    status = await agg.aggregate("evt_001")
    assert status == "compensated"


@pytest.mark.asyncio
async def test_aggregate_compensation_failed(db):
    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    st = SubTask(seq=0, service="grocy", action="add_stock", params={})
    await insert_executions(db, [st], "evt_001")
    await update_execution(db, "evt_001", 0, "failed", {"error": "x"})

    comp_st = SubTask(seq=1000, service="grocy", action="consume_stock", params={})
    await insert_executions(db, [comp_st], "evt_001", is_compensation=1)
    await update_execution(db, "evt_001", 1000, "failed", {})

    agg = Aggregator(db)
    status = await agg.aggregate("evt_001")
    assert status == "failed"
