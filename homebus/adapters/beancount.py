from __future__ import annotations

from datetime import datetime
from pathlib import Path

from homebus.adapters.base import ActionMeta, AdapterBase
from homebus.adapters import beancount_writer as writer


class BeancountAdapter(AdapterBase):

    def __init__(self, ledger_path: str, fava_url: str | None = None):
        self.ledger_path = ledger_path
        self.fava_url = fava_url

    async def execute(self, action: str, params: dict) -> dict:
        if action == "record_expense":
            return await self._record_expense(params)
        elif action == "delete_entry":
            return await self._delete_entry(params)
        elif action == "verify_entry":
            return await self._verify_entry(params)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _record_expense(self, params: dict) -> dict:
        event_id = params["event_id"]
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        items = params.get("items", [])
        total_price = params.get("total_price", 0.0)
        store = params.get("store")
        account = params.get("account", "Expenses:Unknown")
        liability = params.get("liability")
        note = params.get("note")

        existing = writer.find_entry_by_event_id(self.ledger_path, event_id)
        if existing is not None:
            return {
                "success": True,
                "data": {
                    "event_id": event_id,
                    "already_exists": True,
                    "file": str(existing[0]),
                },
            }

        entry_text = writer.generate_entry(
            event_id=event_id,
            date=date,
            items=items,
            total_price=total_price,
            store=store,
            account=account,
            liability=liability,
            note=note,
        )

        target_file = writer.write_entry(self.ledger_path, entry_text, date)

        check_ok, check_msg = writer.run_bean_check(self.ledger_path)
        if not check_ok:
            return {
                "success": False,
                "error": f"bean-check failed: {check_msg}",
            }

        committed = writer.git_commit(
            self.ledger_path,
            f"homebus: record expense {event_id}",
        )

        return {
            "success": True,
            "data": {
                "event_id": event_id,
                "file": str(target_file),
                "bean_check": check_ok,
                "git_committed": committed,
            },
        }

    async def _delete_entry(self, params: dict) -> dict:
        event_id = params["event_id"]
        deleted = writer.delete_entry_by_event_id(self.ledger_path, event_id)

        committed = writer.git_commit(
            self.ledger_path,
            f"homebus: delete entry {event_id} (compensation)",
        )

        return {
            "success": True,
            "data": {
                "event_id": event_id,
                "removed": deleted,
                "git_committed": committed,
            },
        }

    async def _verify_entry(self, params: dict) -> dict:
        event_id = params.get("event_id", "")
        result = writer.find_entry_by_event_id(self.ledger_path, event_id)

        if result is None:
            return {
                "success": True,
                "data": {"found": False, "event_id": event_id},
            }

        bean_file, start, end = result
        lines = bean_file.read_text(encoding="utf-8").splitlines()
        entry_text = "\n".join(lines[start:end])

        return {
            "success": True,
            "data": {
                "found": True,
                "event_id": event_id,
                "entry": entry_text,
                "file": str(bean_file),
                "line": start + 1,
            },
        }

    async def health_check(self) -> dict:
        ledger_path = Path(self.ledger_path).expanduser()
        if not ledger_path.exists():
            return {"healthy": False, "detail": f"ledger path not found: {self.ledger_path}"}

        bean_files = list(ledger_path.rglob("*.bean"))
        if not bean_files:
            return {"healthy": False, "detail": "no .bean files found"}

        ok, detail = writer.check_bean_check_available()
        if ok:
            return {"healthy": True, "detail": detail}
        return {"healthy": False, "detail": detail}

    def list_actions(self) -> list[ActionMeta]:
        return [
            ActionMeta(
                name="record_expense",
                description="记录支出分录",
                params_schema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "date": {"type": "string"},
                        "items": {"type": "array"},
                        "total_price": {"type": "number"},
                        "store": {"type": "string"},
                        "account": {"type": "string"},
                        "liability": {"type": "string"},
                    },
                    "required": ["event_id", "items", "total_price"],
                },
                returns_schema={"type": "object"},
            ),
            ActionMeta(
                name="delete_entry",
                description="删除分录（补偿）",
                params_schema={
                    "type": "object",
                    "properties": {"event_id": {"type": "string"}},
                    "required": ["event_id"],
                },
                returns_schema={"type": "object"},
            ),
            ActionMeta(
                name="verify_entry",
                description="验证分录是否存在",
                params_schema={
                    "type": "object",
                    "properties": {"event_id": {"type": "string"}},
                    "required": ["event_id"],
                },
                returns_schema={"type": "object"},
            ),
        ]
