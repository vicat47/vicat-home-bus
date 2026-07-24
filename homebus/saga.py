from __future__ import annotations

import aiosqlite


COMPENSATION_MAP: dict[tuple[str, str], dict] = {
    ("grocy", "add_stock"): {
        "action": "consume_stock",
        "params": lambda params, _result: {
            "items": [
                {
                    "name": i.get("name", ""),
                    "quantity": abs(i.get("quantity", 0)),
                    "unit": i.get("unit", ""),
                    "grocy_product_id": i.get("grocy_product_id"),
                }
                for i in params.get("items", [])
            ],
        },
    },
    ("beancount", "record_expense"): {
        "action": "delete_entry",
        "params": lambda params, _result: {
            "event_id": params.get("event_id", ""),
        },
    },
    ("homebox", "create_asset"): {
        "action": "delete_asset",
        "params": lambda params, result: {
            "asset_id": result.get("asset_id", ""),
        },
    },
}


class UncompensatableError(Exception):
    def __init__(self, service: str, action: str):
        self.service = service
        self.action = action
        super().__init__(f"No compensation defined for ({service}, {action})")


class SagaCompensator:

    def __init__(self, adapters: dict, db: aiosqlite.Connection):
        self.adapters = adapters
        self.db = db

    def _derive_compensation(self, subtask) -> tuple[str, str, dict]:
        key = (subtask.service, subtask.action)
        if key not in COMPENSATION_MAP:
            raise UncompensatableError(subtask.service, subtask.action)

        mapping = COMPENSATION_MAP[key]
        result_data = subtask.params.get("_result", {})
        comp_params = mapping["params"](subtask.params, result_data)
        return (subtask.service, mapping["action"], comp_params)

    async def compensate(
        self, event_id: str, completed_subtasks: list
    ) -> bool:
        from homebus.database import insert_executions, update_execution

        all_compensated = True
        compensation_seq_base = 1000

        for i, subtask in enumerate(completed_subtasks):
            try:
                service, action, params = self._derive_compensation(subtask)
            except UncompensatableError:
                continue

            comp_st = type("CompSubTask", (), {})()
            comp_st.seq = compensation_seq_base + i
            comp_st.service = service
            comp_st.action = action
            comp_st.params = params
            comp_st.depends_on = []

            await insert_executions(
                self.db, [comp_st], event_id, is_compensation=1
            )

            adapter = self.adapters.get(service)
            if adapter is None:
                all_compensated = False
                await update_execution(
                    self.db, event_id, comp_st.seq, "failed",
                    result={
                        "success": False,
                        "error": f"Unknown service: {service}",
                    },
                )
                continue

            await update_execution(
                self.db, event_id, comp_st.seq, "running",
            )

            result = await adapter.execute(action, params)
            if result.get("success"):
                await update_execution(
                    self.db, event_id, comp_st.seq, "success",
                    result=result,
                )
                await update_execution(
                    self.db, event_id, subtask.seq, "compensated",
                )
            else:
                all_compensated = False
                await update_execution(
                    self.db, event_id, comp_st.seq, "failed",
                    result=result,
                )

        return all_compensated
