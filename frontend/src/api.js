const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000/api/v1"
    : "/_/backend/api/v1");

export async function submitQuery(sql) {
  const res = await fetch(`${API_BASE}/query/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sql }),
  });
  if (!res.ok) {
    throw new Error(`Submit failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchPriority(queryId) {
  const res = await fetch(`${API_BASE}/query/${queryId}/priority`);
  if (!res.ok) {
    throw new Error(`Priority poll failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) {
    throw new Error(`Metrics fetch failed: ${res.status}`);
  }
  return res.json();
}
