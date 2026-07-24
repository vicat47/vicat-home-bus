import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from homebus.models import (
    AdapterHealth,
    CreateEventRequest,
    CreateEventResponse,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    EventItem,
    EventStatusResponse,
    ExecutionItem,
    HealthResponse,
    QueryRequest,
    SubTask,
)


class TestEventItem:
    def test_valid_consumable(self):
        item = EventItem(name="牛奶", category="consumable", quantity=3, unit="盒", price=20.0)
        assert item.name == "牛奶"
        assert item.category == "consumable"

    def test_valid_durable(self):
        item = EventItem(name="洗衣机", category="durable", quantity=1, unit="台", price=3000.0)
        assert item.category == "durable"

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            EventItem(name="x", category="invalid", quantity=1, unit="个", price=1.0)

    def test_extra_fields_allowed(self):
        item = EventItem(name="牛奶", category="consumable", quantity=3, unit="盒", price=20.0,
                        homebox_location_id="loc_1")
        assert item.homebox_location_id == "loc_1"


class TestCreateEventRequest:
    def test_valid_purchase(self):
        req = CreateEventRequest(
            intent="purchase",
            items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
            total_price=60.0,
            store="京东",
        )
        assert req.intent == "purchase"
        assert len(req.items) == 1

    def test_valid_consume(self):
        req = CreateEventRequest(
            intent="consume",
            items=[{"name": "牛奶", "quantity": 1, "unit": "盒"}],
        )
        assert req.intent == "consume"

    def test_empty_items_raises(self):
        with pytest.raises(ValidationError):
            CreateEventRequest(intent="purchase", items=[])

    def test_invalid_intent_raises(self):
        with pytest.raises(ValidationError):
            CreateEventRequest(intent="invalid", items=[{"name": "x", "category": "consumable", "quantity": 1, "unit": "个", "price": 1.0}])

    def test_event_id_pattern(self):
        req = CreateEventRequest(
            intent="purchase",
            event_id="evt_sess1_001",
            items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
            total_price=60.0,
        )
        assert req.event_id == "evt_sess1_001"


class TestSubTask:
    def test_defaults(self):
        st = SubTask(seq=0, service="grocy", action="add_stock")
        assert st.seq == 0
        assert st.timeout == 30.0
        assert st.max_retries == 3
        assert st.depends_on == []

    def test_with_deps(self):
        st = SubTask(seq=1, service="beancount", action="record_expense", depends_on=[0])
        assert st.depends_on == [0]


class TestErrorCode:
    def test_values(self):
        assert ErrorCode.INVALID_EVENT_SCHEMA == "INVALID_EVENT_SCHEMA"
        assert ErrorCode.EVENT_NOT_FOUND == "EVENT_NOT_FOUND"
        assert ErrorCode.ADAPTER_UNAVAILABLE == "ADAPTER_UNAVAILABLE"


class TestHealthResponse:
    def test_healthy(self):
        resp = HealthResponse(status="healthy", adapters=AdapterHealth())
        assert resp.status == "healthy"

    def test_degraded(self):
        resp = HealthResponse(
            status="degraded",
            adapters=AdapterHealth(grocy="ok", beancount="error", homebox="ok"),
        )
        assert resp.status == "degraded"
