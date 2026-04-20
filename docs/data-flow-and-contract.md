# Realtime Data Flow and Contract

This document defines the backend payloads consumed by the UI and how they appear in live components.

## End-to-End Realtime Flow

1. User submits SQL in Monaco (`Input Console`).
2. Frontend calls `POST /api/v1/query/submit`.
3. Backend returns initial prediction and tier assignment.
4. Frontend adds a new row to the live results table and a monolith in the 3D lane.
5. Frontend polls `GET /api/v1/query/{query_id}/priority` every 900ms until `status=completed`.
6. Each poll response updates:
   - results table (`status`, `tier`, `predicted_runtime_ms`, `observed_runtime_ms`)
   - 3D monolith lane position via GSAP animation.
7. Analytics panel polls `GET /api/v1/metrics` every 1500ms.

## API Contracts Used by UI

### Submit Query

`POST /api/v1/query/submit`

Request:

```json
{
  "sql": "SELECT id FROM users WHERE id = 1;"
}
```

Response:

```json
{
  "query_id": "f8a4c1cb-6788-4ee3-a3a0-e6e6e34b0e0c",
  "predicted_runtime_ms": 84.3,
  "priority_id": 0,
  "tier": "express"
}
```

### Poll Priority

`GET /api/v1/query/{query_id}/priority`

Response:

```json
{
  "query_id": "f8a4c1cb-6788-4ee3-a3a0-e6e6e34b0e0c",
  "priority_id": 1,
  "tier": "standard",
  "predicted_runtime_ms": 84.3,
  "observed_runtime_ms": 131.6,
  "status": "completed"
}
```

### Metrics

`GET /api/v1/metrics`

Response:

```json
{
  "average_wait_time_ms": 9.43,
  "throughput_qps": 0.667,
  "prediction_rmse_ms": 45.92
}
```

## UI Mapping

- `tier` -> 3D lane selection (`express`, `standard`, `batch`).
- `status` -> query state shown in table (`queued`, `running`, `completed`).
- `observed_runtime_ms` -> appears when execution ends.
- tier change between polls -> GSAP demotion pulse (scale + rotation) for visual traceability.
