from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    INVALID_EVENT_SCHEMA = "INVALID_EVENT_SCHEMA"
    INVALID_QUERY_PARAMS = "INVALID_QUERY_PARAMS"
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"
    ADAPTER_TIMEOUT = "ADAPTER_TIMEOUT"
    COMPENSATION_FAILED = "COMPENSATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class EventItem(BaseModel):
    name: str
    category: Optional[Literal["consumable", "durable"]] = None
    quantity: float
    unit: str
    price: float = 0.0
    grocy_product_id: Optional[str] = None

    model_config = {"extra": "allow"}


class CreateEventRequest(BaseModel):
    intent: Literal["purchase", "consume"]
    event_id: Optional[str] = Field(
        None, pattern=r"^evt_[a-z0-9_]+$",
        description="Agent custom event_id. Auto-generated if not provided."
    )
    items: list[EventItem] = Field(min_length=1)

    total_price: Optional[float] = None
    store: Optional[str] = None
    purchased_at: Optional[datetime] = None

    consumed_at: Optional[datetime] = None

    note: Optional[str] = None

    model_config = {"extra": "allow"}


class ExecutionItem(BaseModel):
    seq: int
    service: Literal["grocy", "beancount", "homebox"]
    action: str
    status: Literal["pending", "running", "success", "failed", "compensated"]
    result: Optional[dict] = None
    is_compensation: bool = False
    retry_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EventStatusResponse(BaseModel):
    event_id: str
    status: Literal["accepted", "executing", "success", "compensated", "failed"]
    intent: str
    executions: list[ExecutionItem] = []
    created_at: str
    updated_at: str
    duplicate: bool = False
    message: Optional[str] = None


class CreateEventResponse(BaseModel):
    event_id: str
    status: str
    message: str
    duplicate: bool = False


class QueryRequest(BaseModel):
    target: Literal["grocy", "beancount", "homebox"]
    operation: str
    params: dict


class QueryResponse(BaseModel):
    data: Optional[dict] = None
    event_id: str
    found: Optional[bool] = None
    entry: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None

    model_config = {"extra": "allow"}


class AdapterHealth(BaseModel):
    grocy: str = "ok"
    beancount: dict | str = "ok"
    homebox: str = "ok"


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"] = "healthy"
    adapters: AdapterHealth


@dataclass
class SubTask:
    seq: int
    service: Literal["grocy", "beancount", "homebox"]
    action: str
    params: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    timeout: float = 30.0
    max_retries: int = 3
    retry_count: int = 0
    status: str = "pending"
