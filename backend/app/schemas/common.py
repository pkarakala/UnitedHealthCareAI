from pydantic import BaseModel
from typing import Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime
    database: str = "connected"
    redis: str = "connected"


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    timestamp: datetime
