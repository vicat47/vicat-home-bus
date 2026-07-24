from __future__ import annotations

import aiosqlite

from homebus.database import get_executions, update_event_status


class Aggregator:

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def aggregate(self, event_id: str) -> str:
        executions = await get_executions(self.db, event_id)

        normal = [e for e in executions if not e["is_compensation"]]
        compensations = [e for e in executions if e["is_compensation"]]

        if not normal:
            status = "accepted"
            await update_event_status(self.db, event_id, status)
            return status

        all_normal_success = all(e["status"] == "success" for e in normal)
        any_normal_failed = any(
            e["status"] in ("failed", "retrying") for e in normal
        )

        if all_normal_success:
            status = "success"
        elif any_normal_failed:
            if compensations:
                all_comp_success = all(
                    e["status"] == "success" for e in compensations
                )
                if all_comp_success:
                    status = "compensated"
                else:
                    status = "failed"
            else:
                status = "failed"
        else:
            status = "executing"

        await update_event_status(self.db, event_id, status)
        return status
