from __future__ import annotations

import uuid
from datetime import datetime

import aiosqlite
from pydantic import ValidationError

from homebus.database import get_event
from homebus.models import CreateEventRequest, ErrorCode, ErrorResponse


def _generate_event_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"evt_{ts}_{suffix}"


async def validate_event(
    db: aiosqlite.Connection, request: CreateEventRequest
) -> tuple[dict | None, str | None]:
    if request.intent == "purchase":
        if request.total_price is None or request.total_price <= 0:
            return {
                "error": {
                    "code": ErrorCode.INVALID_EVENT_SCHEMA,
                    "message": "purchase 事件必须提供有效的 total_price",
                    "details": {"field": "total_price"},
                }
            }, None

    if request.event_id:
        existing = await get_event(db, request.event_id)
        if existing is not None:
            return None, request.event_id
    else:
        request.event_id = _generate_event_id()

    return None, request.event_id
