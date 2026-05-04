import json
import logging
import random
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError


API_BASE = "http://localhost:8000/api/v1"
SAMPLE_FILE = Path(__file__).resolve().parents[1] / "test-data" / "sample_queries.json"
LOGGER = logging.getLogger("aethelgard.workload")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def request_json(url: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except URLError as exc:
        LOGGER.error("request_failed | method=%s url=%s error=%s", method, url, str(exc))
        raise


def load_queries() -> list[str]:
    payload = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
    queries = []
    for bucket in ("express", "standard", "batch"):
        queries.extend(payload[bucket])
    return queries


def main(total_submits: int = 20, poll_seconds: float = 1.0) -> None:
    configure_logging()
    queries = load_queries()
    submitted_ids: list[str] = []

    LOGGER.info(
        "workload_start | total_submits=%d poll_seconds=%.2f query_pool=%d",
        total_submits,
        poll_seconds,
        len(queries),
    )
    for i in range(total_submits):
        sql = random.choice(queries)
        created = request_json(f"{API_BASE}/query/submit", "POST", {"sql": sql})
        submitted_ids.append(created["query_id"])
        LOGGER.info(
            "submit_ok | seq=%02d query_id=%s tier=%s predicted_ms=%.2f",
            i + 1,
            created["query_id"][:8],
            created["tier"],
            created["predicted_runtime_ms"],
        )
        time.sleep(0.1)

    LOGGER.info("polling_start | pending=%d", len(submitted_ids))
    pending = set(submitted_ids)
    while pending:
        finished = []
        for qid in pending:
            state = request_json(f"{API_BASE}/query/{qid}/priority")
            if state["status"] == "completed":
                LOGGER.info(
                    "query_done | query_id=%s tier=%s observed_ms=%.2f",
                    qid[:8],
                    state["tier"],
                    state.get("observed_runtime_ms", 0.0),
                )
                finished.append(qid)
        for qid in finished:
            pending.remove(qid)
        if pending:
            LOGGER.info("polling_tick | remaining=%d", len(pending))
            time.sleep(poll_seconds)

    metrics = request_json(f"{API_BASE}/metrics")
    LOGGER.info(
        "workload_done | awt_ms=%.2f qps=%.3f rmse_ms=%.2f",
        metrics["average_wait_time_ms"],
        metrics["throughput_qps"],
        metrics["prediction_rmse_ms"],
    )
    LOGGER.info("metrics_json | %s", json.dumps(metrics))


if __name__ == "__main__":
    main()
