# Aethelgard: Predictive Query Scheduler

Boilerplate implementation of a Predictive Multi-Level Feedback Queue (P-MLFQ):

- **Backend**: FastAPI + asyncio + scikit-learn RandomForestRegressor
- **Frontend**: React + TailwindCSS + GSAP + React Three Fiber
- **Database integration point**: PostgreSQL `EXPLAIN ANALYZE` hooks (stubbed client included)

## Project Structure

- `backend/` FastAPI scheduling and ML APIs
- `frontend/` React UI with Monaco, analytics panel, and 3D lane visualization

## Quick Start

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will call backend at `http://localhost:8000`.

## API Endpoints

- `POST /api/v1/query/submit`:
  - Input: SQL text
  - Output: `query_id`, predicted runtime, assigned tier (`express`, `standard`, `batch`)
- `GET /api/v1/query/{query_id}/priority`:
  - Poll current lane/priority status
- `GET /api/v1/metrics`:
  - Returns AWT, throughput, and RMSE

## Notes

- `EXPLAIN ANALYZE` collection is intentionally wrapped behind `GroundTruthService` so production DB credentials and hardening can be added safely.
- The scheduler supports demotion behavior when observed runtime exceeds prediction by threshold.

## Test Data and Load Testing

- Query samples: `test-data/sample_queries.json`
- Demo PostgreSQL schema + data: `test-data/postgres_seed.sql`
- Synthetic workload runner: `tools/push_workload.py`

### Run sample load against backend

```bash
python tools/push_workload.py
```

This will:

- Submit random SQL from all 3 queue tiers
- Poll each query until completed
- Print a final metrics snapshot (`AWT`, `QPS`, `RMSE`)

### Optional: seed a local PostgreSQL

```bash
psql -U <user> -d <db> -f test-data/postgres_seed.sql
```

## Realtime UI Data Contract

- Detailed contract and mapping: `docs/data-flow-and-contract.md`
- Full UI + backend component/algorithm explanation: `README.ui-backend.md`
- The UI shows live backend values for each query:
  - `status`
  - `tier`
  - `predicted_runtime_ms`
  - `observed_runtime_ms`
- GSAP transitions are tied to backend tier updates and demotion behavior.
