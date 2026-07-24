import tempfile
from pathlib import Path

import pytest

from homebus.database import init_db, insert_event
from homebus.models import CreateEventRequest
from homebus.validators import validate_event


@pytest.fixture
async def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = await init_db(db_path)
    yield conn
    await conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_validate_generates_event_id(db):
    req = CreateEventRequest(
        intent="purchase",
        items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
        total_price=60.0,
    )
    assert req.event_id is None

    error, event_id = await validate_event(db, req)
    assert error is None
    assert event_id is not None
    assert event_id.startswith("evt_")


@pytest.mark.asyncio
async def test_validate_purchase_missing_total_price(db):
    req = CreateEventRequest(
        intent="purchase",
        items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
    )
    error, event_id = await validate_event(db, req)
    assert error is not None
    assert error["error"]["code"] == "INVALID_EVENT_SCHEMA"


@pytest.mark.asyncio
async def test_validate_idempotency(db):
    await insert_event(db, "evt_sess1_001", "purchase", '{"items":[]}')

    req = CreateEventRequest(
        intent="purchase",
        event_id="evt_sess1_001",
        items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
        total_price=60.0,
    )
    error, event_id = await validate_event(db, req)
    assert error is None
    assert event_id == "evt_sess1_001"
