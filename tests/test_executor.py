import tempfile
from pathlib import Path

import pytest

from homebus.database import init_db, insert_event, insert_executions, update_event_status, update_execution
from homebus.executor import TaskExecutor
from homebus.models import SubTask


class MockAdapter:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls: list[tuple[str, dict]] = []

    async def execute(self, action: str, params: dict) -> dict:
        self.calls.append((action, params))
        if self.should_fail:
            return {"success": False, "error": "mock error"}
        return {"success": True, "data": {"ok": True}}

    async def health_check(self) -> dict:
        return {"healthy": True}

    def list_actions(self) -> list:
        return []

    async def close(self) -> None:
        pass


@pytest.fixture
async def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = await init_db(db_path)
    yield conn
    await conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_executor_single_success(db):
    adapters = {"grocy": MockAdapter()}
    executor = TaskExecutor(adapters, db)

    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    subtasks = [
        SubTask(seq=0, service="grocy", action="add_stock", params={"items": []}),
    ]
    await insert_executions(db, subtasks, "evt_001")
    await update_event_status(db, "evt_001", "executing")

    completed = await executor.execute("evt_001", subtasks)
    assert len(completed) == 1
    assert completed[0].status == "success"


@pytest.mark.asyncio
async def test_executor_single_failure(db):
    adapters = {"grocy": MockAdapter(should_fail=True)}
    executor = TaskExecutor(adapters, db)

    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    subtasks = [
        SubTask(seq=0, service="grocy", action="add_stock", params={"items": []}),
    ]
    await insert_executions(db, subtasks, "evt_001")

    completed = await executor.execute("evt_001", subtasks)
    assert completed[0].status == "failed"


@pytest.mark.asyncio
async def test_executor_parallel_layer(db):
    adapters = {
        "grocy": MockAdapter(),
        "beancount": MockAdapter(),
    }
    executor = TaskExecutor(adapters, db)

    await insert_event(db, "evt_001", "purchase", '{"items":[]}')
    subtasks = [
        SubTask(seq=0, service="grocy", action="add_stock", params={}),
        SubTask(seq=1, service="beancount", action="record_expense",
                params={}, depends_on=[0]),
    ]
    await insert_executions(db, subtasks, "evt_001")

    completed = await executor.execute("evt_001", subtasks)
    assert len(completed) == 2
    assert all(st.status == "success" for st in completed)
