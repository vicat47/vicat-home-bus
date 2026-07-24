from __future__ import annotations

import asyncio
from collections import defaultdict

import aiosqlite

from homebus.models import SubTask


class TaskExecutor:

    def __init__(self, adapters: dict, db: aiosqlite.Connection):
        self.adapters = adapters
        self.db = db

    async def execute(self, event_id: str, subtasks: list[SubTask]) -> list[SubTask]:
        layers = self._topological_sort(subtasks)
        completed: list[SubTask] = []

        for layer in layers:
            try:
                results = await asyncio.gather(
                    *[self._execute_one(event_id, st) for st in layer],
                    return_exceptions=True,
                )

                for st, result in zip(layer, results):
                    if isinstance(result, Exception):
                        for s in layer:
                            if s.status == "running":
                                s.status = "failed"
                        failed = [s for s in layer if s.status != "success"]
                        await self._trigger_compensation(event_id, completed)
                        return completed + layer

                    if result["success"]:
                        st.status = "success"
                        st.params["_result"] = result.get("data")
                        completed.append(st)
                    else:
                        st.status = "failed"
                        st.params["_error"] = result.get("error")
                        await self._trigger_compensation(event_id, completed)
                        return completed + layer

            except asyncio.CancelledError:
                for st in layer:
                    if st.status == "running":
                        st.status = "failed"
                await self._trigger_compensation(event_id, completed)
                return completed + layer

        return completed

    async def _execute_one(
        self, event_id: str, subtask: SubTask
    ) -> dict:
        adapter = self.adapters.get(subtask.service)
        if adapter is None:
            return {"success": False, "error": f"Unknown service: {subtask.service}"}

        from homebus.database import update_execution
        subtask.status = "running"
        await update_execution(
            self.db, event_id, subtask.seq, "running",
        )

        for attempt in range(subtask.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    adapter.execute(subtask.action, subtask.params),
                    timeout=subtask.timeout,
                )
                if result.get("success"):
                    await update_execution(
                        self.db, event_id, subtask.seq, "success",
                        result=result,
                        retry_count=subtask.retry_count,
                    )
                    return result
                else:
                    subtask.retry_count = attempt
                    if attempt < subtask.max_retries:
                        await update_execution(
                            self.db, event_id, subtask.seq, "retrying",
                            retry_count=subtask.retry_count,
                        )
                        await asyncio.sleep(0.5 * (attempt + 1))
            except asyncio.TimeoutError:
                subtask.retry_count = attempt
                if attempt < subtask.max_retries:
                    continue

        await update_execution(
            self.db, event_id, subtask.seq, "failed",
            result={"success": False, "error": "timeout or max retries exceeded"},
            retry_count=subtask.retry_count,
        )
        return {"success": False, "error": "timeout or max retries exceeded"}

    async def _trigger_compensation(
        self, event_id: str, completed: list[SubTask]
    ) -> None:
        if not completed:
            return
        from homebus.saga import SagaCompensator
        saga = SagaCompensator(self.adapters, self.db)
        await saga.compensate(event_id, completed)

    def _topological_sort(
        self, subtasks: list[SubTask]
    ) -> list[list[SubTask]]:
        seq_to_st: dict[int, SubTask] = {st.seq: st for st in subtasks}

        in_degree: dict[int, int] = {st.seq: len(st.depends_on) for st in subtasks}
        adj: dict[int, list[int]] = defaultdict(list)
        for st in subtasks:
            for dep_seq in st.depends_on:
                adj[dep_seq].append(st.seq)

        layers: list[list[SubTask]] = []
        processed: set[int] = set()

        while len(processed) < len(subtasks):
            ready = [
                seq_to_st[s]
                for s, deg in in_degree.items()
                if deg == 0 and s not in processed
            ]
            if not ready:
                break
            layers.append(ready)
            for st in ready:
                processed.add(st.seq)
                for neighbor in adj[st.seq]:
                    in_degree[neighbor] -= 1

        return layers
