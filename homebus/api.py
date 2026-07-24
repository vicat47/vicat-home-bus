from __future__ import annotations

import json
from contextlib import asynccontextmanager

from pydantic import ValidationError

import aiosqlite
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from homebus.adapters.base import AdapterBase
from homebus.models import (
    AdapterHealth,
    CreateEventRequest,
    CreateEventResponse,
    ErrorCode,
    ErrorResponse,
    EventStatusResponse,
    ExecutionItem,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from homebus.aggregator import Aggregator
from homebus.config import load_config
from homebus.database import (
    get_event,
    get_executions,
    init_db,
    insert_event,
    insert_executions,
    update_event_status,
)
from homebus.dispatch import DispatchEngine
from homebus.executor import TaskExecutor
from homebus.models import SubTask
from homebus.query_router import QueryRouter
from homebus.registry import Registry

from homebus.validators import validate_event

_db: aiosqlite.Connection | None = None
_adapters: dict[str, AdapterBase] = {}
_registry: Registry | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db, _adapters, _registry
    config = load_config()
    _db = await init_db(config.database.path)
    _registry = Registry.load()
    yield
    for adapter in _adapters.values():
        if hasattr(adapter, "close"):
            await adapter.close()
    if _db:
        await _db.close()


app = FastAPI(
    title="HomeBus",
    description="HomeBus — 家庭服务总线 (Family Service Bus)",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_db() -> aiosqlite.Connection:
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db


def _get_adapters() -> dict[str, AdapterBase]:
    return _adapters


def _build_execution_items(executions: list[dict]) -> list[ExecutionItem]:
    result = []
    for e in executions:
        parsed_result = None
        if e["result"]:
            try:
                parsed_result = json.loads(e["result"])
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(ExecutionItem(
            seq=e["seq"],
            service=e["service"],
            action=e["action"],
            status=e["status"],
            result=parsed_result,
            is_compensation=bool(e["is_compensation"]),
            retry_count=e["retry_count"],
            created_at=e["created_at"],
            updated_at=e["updated_at"],
        ))
    return result


@app.post("/v1/events", response_model=CreateEventResponse)
async def create_event(
    request: CreateEventRequest, background_tasks: BackgroundTasks
):
    db = _get_db()

    error_resp, event_id = await validate_event(db, request)
    if error_resp is not None:
        return JSONResponse(status_code=400, content=error_resp)

    if event_id is not None and error_resp is None:
        existing = await get_event(db, event_id)
        if existing and existing["event_id"] == event_id:
            return CreateEventResponse(
                event_id=event_id,
                status=existing["status"],
                message="事件已存在（幂等命中）",
                duplicate=True,
            )

    event_id = event_id or request.event_id
    payload_json = request.model_dump_json()

    inserted = await insert_event(db, event_id, request.intent, payload_json)
    if not inserted:
        existing = await get_event(db, event_id)
        return CreateEventResponse(
            event_id=event_id,
            status=existing["status"] if existing else "accepted",
            message="事件已存在（幂等命中）",
            duplicate=True,
        )

    adapter_instances = _get_adapters()

    async def process_event(event_id: str, req: CreateEventRequest):
        dispatch_engine = DispatchEngine(_registry)
        subtasks = dispatch_engine.derive_subtasks(req)

        await update_event_status(db, event_id, "executing")
        await insert_executions(db, subtasks, event_id)

        executor = TaskExecutor(adapter_instances, db)
        completed = await executor.execute(event_id, subtasks)

        aggregator = Aggregator(db)
        await aggregator.aggregate(event_id)

    background_tasks.add_task(process_event, event_id, request)

    return CreateEventResponse(
        event_id=event_id,
        status="accepted",
        message="事件已接收",
    )


@app.get("/v1/events/{event_id}", response_model=EventStatusResponse)
async def get_event_status(event_id: str):
    db = _get_db()
    event = await get_event(db, event_id)
    if event is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": ErrorCode.EVENT_NOT_FOUND,
                    "message": f"event_id '{event_id}' 不存在",
                }
            },
        )
    executions = await get_executions(db, event_id)
    return EventStatusResponse(
        event_id=event["event_id"],
        status=event["status"],
        intent=event["intent"],
        executions=_build_execution_items(executions),
        created_at=event["created_at"],
        updated_at=event["updated_at"],
    )


@app.post("/v1/query", response_model=QueryResponse)
async def query_backend(request: QueryRequest):
    db = _get_db()
    query_router = QueryRouter(_get_adapters(), db)
    result = await query_router.route(
        request.target, request.operation, request.params
    )

    if not result.get("success", True) and "error" in result:
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": ErrorCode.ADAPTER_UNAVAILABLE,
                    "message": result.get("error", "Unknown error"),
                    "details": {
                        "adapter": request.target,
                        "operation": request.operation,
                    },
                }
            },
        )

    return QueryResponse(
        data=result.get("data"),
        event_id=result.get("event_id", ""),
    )


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    adapters = _get_adapters()
    adapter_health = AdapterHealth()

    grocy = adapters.get("grocy")
    if grocy:
        hc = await grocy.health_check()
        adapter_health.grocy = "ok" if hc.get("healthy") else "error"

    beancount = adapters.get("beancount")
    if beancount:
        hc = await beancount.health_check()
        if hc.get("healthy"):
            adapter_health.beancount = {"status": "ok", "detail": hc.get("detail", "")}
        else:
            adapter_health.beancount = "error"

    homebox = adapters.get("homebox")
    if homebox:
        hc = await homebox.health_check()
        adapter_health.homebox = "ok" if hc.get("healthy") else "error"

    all_healthy = (
        adapter_health.grocy == "ok"
        and adapter_health.homebox == "ok"
    )
    beancount_ok = (
        isinstance(adapter_health.beancount, dict)
        and adapter_health.beancount.get("status") == "ok"
    ) or adapter_health.beancount == "ok"

    status = "healthy" if (all_healthy and beancount_ok) else "degraded"
    return HealthResponse(status=status, adapters=adapter_health)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    msg = "; ".join(
        f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
        for e in errors
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": ErrorCode.INVALID_EVENT_SCHEMA,
                "message": msg,
                "details": {"errors": errors},
            }
        },
    )
