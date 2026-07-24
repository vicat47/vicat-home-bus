from __future__ import annotations

import json
import uuid
from datetime import datetime

import aiosqlite

from homebus.adapters.base import AdapterBase


def _generate_query_event_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"evt_q_{ts}_{suffix}"


class QueryRouter:

    def __init__(self, adapters: dict[str, AdapterBase], db: aiosqlite.Connection):
        self.adapters = adapters
        self.db = db

    async def route(
        self, target: str, operation: str, params: dict
    ) -> dict:
        event_id = _generate_query_event_id()

        payload_json = json.dumps(
            {"target": target, "operation": operation, "params": params},
            ensure_ascii=False,
        )

        try:
            await self.db.execute(
                "INSERT INTO events (event_id, intent, payload) VALUES (?, 'query', ?)",
                (event_id, payload_json),
            )
            await self.db.commit()
        except Exception:
            pass

        adapter = self.adapters.get(target)
        if adapter is None:
            return {
                "success": False,
                "error": f"Unknown target: {target}",
                "event_id": event_id,
            }

        try:
            result = await adapter.execute(operation, params)
            result["event_id"] = event_id
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "event_id": event_id,
            }
