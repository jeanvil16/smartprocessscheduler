from __future__ import annotations

import asyncio
import logging
import random
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .feature_extractor import QueryFeatures, parse_sql_token_features
from .ml_runtime import RuntimePredictor, make_fingerprint
from .models import (
    MetricsResponse,
    QueryPriorityResponse,
    QuerySubmitRequest,
    QuerySubmitResponse,
)
from .scheduler import PMLFQScheduler
from .store import MemoryStore, QueryRecord

app = FastAPI(title="Aethelgard API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = MemoryStore()
predictor = RuntimePredictor()
scheduler = PMLFQScheduler()
logger = logging.getLogger("aethelgard.scheduler")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def infer_scan_type(sql: str) -> str:
    # Placeholder: in production, inspect EXPLAIN output.
    return "index" if "where" in sql.lower() else "sequential"


def infer_estimated_rows(sql: str) -> float:
    # Placeholder: map text complexity to cardinality heuristic.
    length_factor = max(1, len(sql.split()))
    return float(length_factor * 350)


def build_features(sql: str, fingerprint: str) -> QueryFeatures:
    select_count, join_count, where_count = parse_sql_token_features(sql)
    return QueryFeatures(
        sql_select_tokens=select_count,
        sql_join_tokens=join_count,
        sql_where_tokens=where_count,
        scan_type_index=1 if infer_scan_type(sql) == "index" else 0,
        estimated_rows=infer_estimated_rows(sql),
        historical_drift=store.get_drift(fingerprint),
    )


async def simulate_execution(query_id: str, features: QueryFeatures) -> None:
    record = store.get_record(query_id)
    if not record:
        logger.warning("simulate_execution skipped | query_id=%s reason=missing_record", query_id)
        return

    record.status = "running"
    record.started_at_s = store.now()
    logger.info(
        "execution_start | query_id=%s tier=%s predicted_ms=%.2f",
        record.query_id,
        record.tier.value,
        record.predicted_runtime_ms,
    )

    runtime_ms = record.predicted_runtime_ms * random.uniform(0.7, 1.6)
    await asyncio.sleep(min(runtime_ms / 1000.0, 3.0))

    record.observed_runtime_ms = runtime_ms
    record.finished_at_s = store.now()
    record.status = "completed"

    decision = scheduler.demote_if_needed(record.tier, record.predicted_runtime_ms, runtime_ms)
    record.priority_id = decision.priority_id
    record.tier = decision.tier

    if record.started_at_s is not None:
        wait_ms = max(0.0, (record.started_at_s - record.created_at_s) * 1000.0)
        store.completed_wait_times_ms.append(wait_ms)
    store.throughput_events_s.append(store.now())
    store.prediction_errors_ms.append(abs(runtime_ms - record.predicted_runtime_ms))
    store.push_runtime_history(record.fingerprint, runtime_ms)
    predictor.partial_refit(features, runtime_ms)
    logger.info(
        "execution_done | query_id=%s final_tier=%s observed_ms=%.2f drift_ms=%.2f",
        record.query_id,
        record.tier.value,
        runtime_ms,
        runtime_ms - record.predicted_runtime_ms,
    )


@app.post("/api/v1/query/submit", response_model=QuerySubmitResponse)
async def submit_query(payload: QuerySubmitRequest) -> QuerySubmitResponse:
    query_id = str(uuid.uuid4())
    fingerprint = make_fingerprint(payload.sql)
    features = build_features(payload.sql, fingerprint)
    prediction = predictor.predict(features)
    decision = scheduler.assign_priority(prediction.runtime_ms)
    logger.info(
        "submit_received | query_id=%s fingerprint=%s select=%d join=%d where=%d est_rows=%.2f drift=%.2f",
        query_id,
        fingerprint,
        features.sql_select_tokens,
        features.sql_join_tokens,
        features.sql_where_tokens,
        features.estimated_rows,
        features.historical_drift,
    )

    record = QueryRecord(
        query_id=query_id,
        sql=payload.sql,
        fingerprint=fingerprint,
        predicted_runtime_ms=prediction.runtime_ms,
        priority_id=decision.priority_id,
        tier=decision.tier,
        created_at_s=store.now(),
    )
    store.add_record(record)
    asyncio.create_task(simulate_execution(query_id, features))
    logger.info(
        "scheduled | query_id=%s tier=%s priority_id=%d predicted_ms=%.2f",
        query_id,
        decision.tier.value,
        decision.priority_id,
        prediction.runtime_ms,
    )

    return QuerySubmitResponse(
        query_id=query_id,
        predicted_runtime_ms=prediction.runtime_ms,
        priority_id=decision.priority_id,
        tier=decision.tier,
    )


@app.get("/api/v1/query/{query_id}/priority", response_model=QueryPriorityResponse)
async def get_priority(query_id: str) -> QueryPriorityResponse:
    record = store.get_record(query_id)
    if not record:
        logger.warning("priority_lookup_miss | query_id=%s", query_id)
        raise HTTPException(status_code=404, detail="Query not found")
    logger.info(
        "priority_lookup | query_id=%s status=%s tier=%s priority_id=%d",
        query_id,
        record.status,
        record.tier.value,
        record.priority_id,
    )
    return QueryPriorityResponse(
        query_id=record.query_id,
        priority_id=record.priority_id,
        tier=record.tier,
        predicted_runtime_ms=record.predicted_runtime_ms,
        observed_runtime_ms=record.observed_runtime_ms,
        status=record.status,
    )


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    awt = (
        sum(store.completed_wait_times_ms) / len(store.completed_wait_times_ms)
        if store.completed_wait_times_ms
        else 0.0
    )
    rmse = (
        (sum(err * err for err in store.prediction_errors_ms) / len(store.prediction_errors_ms)) ** 0.5
        if store.prediction_errors_ms
        else 0.0
    )

    now = store.now()
    recent = [t for t in store.throughput_events_s if now - t <= 15]
    qps = len(recent) / 15.0
    logger.info("metrics_snapshot | awt_ms=%.2f qps=%.3f rmse_ms=%.2f", awt, qps, rmse)
    return MetricsResponse(
        average_wait_time_ms=awt,
        throughput_qps=qps,
        prediction_rmse_ms=rmse,
    )


@app.on_event("startup")
async def on_startup() -> None:
    configure_logging()
    logger.info("aethelgard_api_started")
