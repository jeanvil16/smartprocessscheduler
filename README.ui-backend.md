# Aethelgard UI + Backend Explanation

## Purpose

This document explains:

1. All UI components and their responsibilities
2. The algorithmic flow in the UI
3. The algorithmic flow in the backend scheduler and ML pipeline

---

## Total Workflow of the App

This section describes the complete lifecycle from user action to model feedback:

1. **SQL authoring in UI**  
   User writes/pastes SQL in the Monaco input console and clicks submit.

2. **Query submission to backend**  
   Frontend sends `POST /api/v1/query/submit` with raw SQL text.

3. **Feature extraction and fingerprinting**  
   Backend normalizes SQL, creates a query fingerprint, and extracts predictive features:
   - token counts (`SELECT`, `JOIN`, `WHERE`)
   - scan heuristic (index/sequential)
   - estimated rows heuristic
   - historical drift from similar fingerprint history

4. **Runtime prediction (ML)**  
   Random Forest model predicts expected runtime in milliseconds.

5. **Initial scheduling (P-MLFQ)**  
   Scheduler assigns priority tier:
   - Express (fast queries)
   - Standard (medium queries)
   - Batch (heavy queries)

6. **Immediate UI reflection**  
   Frontend receives `query_id`, predicted runtime, priority/tier and:
   - adds a row in live results table
   - spawns a 3D monolith in the mapped lane
   - updates queue counters/progress UI

7. **Execution lifecycle simulation**  
   Backend async task moves query state:
   - `queued` -> `running` -> `completed`
   - calculates observed runtime
   - applies demotion if runtime drift exceeds threshold (35%)

8. **Realtime synchronization loop**  
   Frontend polls `GET /api/v1/query/{query_id}/priority` for active queries every ~900ms and merges updated status/tier/runtime fields into state.

9. **Visual state transitions**  
   GSAP animates each monolith:
   - lane changes by tier updates
   - completion exit movement
   - demotion pulse effects for traceability

10. **System metrics aggregation**  
    Backend updates AWT, QPS, and RMSE continuously. Frontend polls `GET /api/v1/metrics` every ~1500ms and renders analytics cards.

11. **Online learning feedback**  
    Observed runtime is appended to training data and model is refit incrementally, improving future runtime predictions for similar query shapes.

In short, the app runs a closed feedback loop: **submit -> predict -> schedule -> execute -> observe -> learn -> visualize**.

### Workflow Diagram

```mermaid
flowchart TD
    A[User writes SQL in Monaco] --> B[Frontend: POST /api/v1/query/submit]
    B --> C[Backend: fingerprint + feature extraction]
    C --> D[Random Forest runtime prediction]
    D --> E[P-MLFQ tier assignment<br/>Express / Standard / Batch]
    E --> F[Store query as queued]
    F --> G[Frontend receives query_id + predicted runtime + tier]
    G --> H[UI table row + 3D monolith created]

    F --> I[Async execution task starts]
    I --> J[State: running]
    J --> K[Observed runtime collected]
    K --> L{Drift > 35%?}
    L -- Yes --> M[Demote tier]
    L -- No --> N[Keep tier]
    M --> O[State: completed]
    N --> O

    O --> P[Update AWT / QPS / RMSE]
    O --> Q[Append sample and partial refit model]

    R[Frontend polling ~900ms] --> S[GET /api/v1/query/{id}/priority]
    S --> T[Merge live status/tier/runtime into UI state]
    T --> U[GSAP lane animation + demotion pulse]

    V[Metrics polling ~1500ms] --> W[GET /api/v1/metrics]
    W --> X[Analytics sidebar update]
```

### Architecture Diagram (Viva/Demo)

```mermaid
flowchart LR
    subgraph FE[Frontend Layer]
      FE1[Monaco SQL Console]
      FE2[React State + Polling]
      FE3[R3F 3D Conveyor]
      FE4[GSAP Animations]
      FE5[Analytics Sidebar]
    end

    subgraph BE[Backend API Layer - FastAPI]
      BE1[Submit API<br/>POST /query/submit]
      BE2[Priority API<br/>GET /query/{id}/priority]
      BE3[Metrics API<br/>GET /metrics]
      BE4[Async Execution Orchestrator]
    end

    subgraph ML[ML + Scheduling Layer]
      ML1[Feature Extractor<br/>SQL tokens, scan type, rows, drift]
      ML2[Runtime Predictor<br/>RandomForestRegressor]
      ML3[P-MLFQ Scheduler<br/>Express / Standard / Batch]
      ML4[Online Refit Loop]
    end

    subgraph ST[Runtime Store Layer]
      ST1[In-Memory Query Store]
      ST2[Fingerprint History]
      ST3[Metrics Aggregator<br/>AWT, QPS, RMSE]
    end

    subgraph DB[Database Layer]
      DB1[PostgreSQL]
      DB2[EXPLAIN / EXPLAIN ANALYZE<br/>Integration Point]
      DB3[Seed/Test Dataset]
    end

    FE1 --> FE2
    FE2 -->|submit SQL| BE1
    FE2 -->|poll priority| BE2
    FE5 -->|poll metrics| BE3

    BE1 --> ML1 --> ML2 --> ML3
    ML3 --> ST1
    ST1 --> BE2
    BE1 --> BE4
    BE4 --> ST1
    BE4 --> ST3
    BE4 --> ML4
    ML4 --> ML2
    ST3 --> BE3

    BE4 -.optional ground truth.-> DB2
    DB2 --> DB1
    DB3 --> DB1

    ST1 --> FE3
    FE3 --> FE4
    FE4 --> FE2
```

---

## UI Components

### 1) `App` (`frontend/src/App.jsx`)

Main orchestration component for the frontend.

Responsibilities:

- Holds global UI state:
  - `sql` (Monaco editor text)
  - `queries` (all query jobs returned by backend)
  - `busy`, `error`, `lastSync`
- Submits SQL using `submitQuery()` from `api.js`
- Starts realtime polling loop (every 900ms) for non-completed queries via `fetchPriority()`
- Computes progress stats:
  - queued count
  - completed count
  - completion percentage
- Renders:
  - input console section
  - 3D scheduler scene
  - realtime sync indicator
  - results table with status/predicted/observed runtime
  - analytics sidebar

---

### 2) `SchedulerScene` (`frontend/src/SchedulerScene.jsx`)

3D visualization of queue lanes and query blocks.

Responsibilities:

- Renders a React Three Fiber `Canvas`
- Draws three conveyor lanes:
  - Express
  - Standard
  - Batch
- Renders each query as a monolith (`QueryMonolith`)
- Applies GSAP animation when backend state changes:
  - Moves object to lane based on `tier`
  - Moves object out on completion (`x = 5`)
  - Applies demotion pulse (scale + slight rotation) when tier drops

---

### 3) `QueryMonolith` (inside `SchedulerScene.jsx`)

Visual unit representing a single query.

Responsibilities:

- Tracks previous `tier` and `status` using refs
- Detects demotion transitions
- Runs GSAP timeline on updates for smooth, traceable state transitions

---

### 4) `AnalyticsSidebar` (`frontend/src/AnalyticsSidebar.jsx`)

Realtime metrics panel.

Responsibilities:

- Polls backend metrics every 1500ms via `fetchMetrics()`
- Displays:
  - Average Wait Time (AWT)
  - Throughput (QPS)
  - Prediction RMSE
- Uses simple high-contrast mini line visuals for metric cards

---

### 5) `MiniChart` (inside `AnalyticsSidebar.jsx`)

Reusable metric card renderer for label/value + sparkline-style line.

---

### 6) API client module (`frontend/src/api.js`)

Backend communication layer.

Functions:

- `submitQuery(sql)` -> `POST /api/v1/query/submit`
- `fetchPriority(queryId)` -> `GET /api/v1/query/{query_id}/priority`
- `fetchMetrics()` -> `GET /api/v1/metrics`

---

## UI Algorithm (Realtime Flow)

1. User enters SQL in Monaco editor.
2. On submit:
   - frontend calls `submitQuery(sql)`
   - backend returns `query_id`, predicted runtime, initial tier/priority
   - frontend appends this query into `queries` state
3. Polling loop (900ms):
   - selects only non-completed queries
   - calls `fetchPriority(query_id)` for each
   - merges latest backend state into existing query state
   - updates `lastSync`
4. Rendering updates:
   - results table reflects latest status/tier/predicted/observed values
   - `SchedulerScene` animates monolith movement between lanes
   - completed jobs are highlighted and progress bar updates
5. Analytics polling (1500ms):
   - fetches live AWT/QPS/RMSE
   - updates sidebar cards

---

## Backend Components

### 1) API + Orchestration (`backend/app/main.py`)

Core entry point with FastAPI endpoints and async execution simulation.

Endpoints:

- `POST /api/v1/query/submit`
- `GET /api/v1/query/{query_id}/priority`
- `GET /api/v1/metrics`

Additional behavior:

- Structured logging for traceability
- CORS enabled for frontend access
- Startup hook initializes logging format

---

### 2) Feature Extraction (`backend/app/feature_extractor.py`)

Extracts ML feature vector from SQL and metadata.

Features used:

- `sql_select_tokens`
- `sql_join_tokens`
- `sql_where_tokens`
- `scan_type_index` (index vs sequential heuristic)
- `estimated_rows` (heuristic)
- `historical_drift` (from fingerprint history)

---

### 3) Runtime Prediction (`backend/app/ml_runtime.py`)

Random Forest model for query runtime prediction.

Responsibilities:

- Creates SQL fingerprint via normalized SHA-256 prefix
- Bootstraps model with synthetic seed samples
- Predicts runtime (`predict`)
- Performs incremental retraining by appending observed samples (`partial_refit`)

---

### 4) Scheduler (`backend/app/scheduler.py`)

Implements P-MLFQ style tiering and demotion.

Initial assignment thresholds:

- `<= 100 ms` -> Express (`priority_id = 0`)
- `<= 600 ms` -> Standard (`priority_id = 1`)
- `> 600 ms` -> Batch (`priority_id = 2`)

Demotion policy:

- If observed runtime > predicted runtime * 1.35
  - Express -> Standard
  - Standard -> Batch
  - Batch stays Batch

---

### 5) In-memory State Store (`backend/app/store.py`)

Tracks query lifecycle and metric aggregates.

Stores:

- query records
- fingerprint runtime history
- completed wait times
- prediction errors
- throughput timestamps

---

## Backend Algorithm (End-to-End)

1. Receive SQL (`/query/submit`)
2. Generate `query_id` and fingerprint
3. Build feature vector from SQL + history
4. Predict runtime with Random Forest
5. Assign initial priority/tier via scheduler thresholds
6. Save query record as queued
7. Launch async execution simulation task
8. During simulation:
   - mark query running
   - generate observed runtime (around prediction)
   - mark completed
   - apply demotion rule if drift too high
   - update wait-time, throughput, error metrics
   - update fingerprint history
   - retrain predictor with observed sample
9. Frontend polls `/priority` until completed
10. Frontend polls `/metrics` for AWT/QPS/RMSE

---

## Why this architecture works

- FastAPI + asyncio enables non-blocking scheduling simulation.
- Random Forest gives nonlinear runtime estimation with simple features.
- Tiered queueing provides understandable priority control.
- Realtime polling keeps UI and backend state aligned.
- GSAP + R3F makes queue transitions visually explicit and traceable.

---

## Current limitations

- `scan_type` and `estimated_rows` are heuristics in current code.
- No persistent DB for scheduler state (in-memory only).
- Polling-based realtime (not websocket push yet).

These are suitable for prototype/demo stage and can be upgraded in production.
