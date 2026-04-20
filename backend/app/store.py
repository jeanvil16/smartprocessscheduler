from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Optional

from .models import PriorityTier


@dataclass
class QueryRecord:
    query_id: str
    sql: str
    fingerprint: str
    predicted_runtime_ms: float
    priority_id: int
    tier: PriorityTier
    created_at_s: float
    status: str = "queued"
    observed_runtime_ms: Optional[float] = None
    started_at_s: Optional[float] = None
    finished_at_s: Optional[float] = None


class MemoryStore:
    def __init__(self) -> None:
        self.query_records: dict[str, QueryRecord] = {}
        self.fingerprint_history: dict[str, list[float]] = {}
        self.completed_wait_times_ms: list[float] = []
        self.prediction_errors_ms: list[float] = []
        self.throughput_events_s: list[float] = []

    def now(self) -> float:
        return perf_counter()

    def add_record(self, record: QueryRecord) -> None:
        self.query_records[record.query_id] = record

    def get_record(self, query_id: str) -> Optional[QueryRecord]:
        return self.query_records.get(query_id)

    def push_runtime_history(self, fingerprint: str, runtime_ms: float) -> None:
        self.fingerprint_history.setdefault(fingerprint, []).append(runtime_ms)

    def get_drift(self, fingerprint: str) -> float:
        prev = self.fingerprint_history.get(fingerprint)
        if not prev:
            return 0.0
        return sum(prev) / len(prev)
