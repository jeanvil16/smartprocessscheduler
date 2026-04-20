from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PriorityTier(str, Enum):
    EXPRESS = "express"
    STANDARD = "standard"
    BATCH = "batch"


class QuerySubmitRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="Raw SQL text")


class QuerySubmitResponse(BaseModel):
    query_id: str
    predicted_runtime_ms: float
    priority_id: int
    tier: PriorityTier


class QueryPriorityResponse(BaseModel):
    query_id: str
    priority_id: int
    tier: PriorityTier
    predicted_runtime_ms: float
    observed_runtime_ms: Optional[float] = None
    status: str


class MetricsResponse(BaseModel):
    average_wait_time_ms: float
    throughput_qps: float
    prediction_rmse_ms: float
