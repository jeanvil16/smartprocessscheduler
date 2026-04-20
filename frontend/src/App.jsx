import { useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { fetchPriority, submitQuery } from "./api";
import SchedulerScene from "./SchedulerScene";
import AnalyticsSidebar from "./AnalyticsSidebar";

const STARTER_SQL = `SELECT u.id, u.email
FROM users u
JOIN subscriptions s ON s.user_id = u.id
WHERE s.plan = 'pro';`;

export default function App() {
  const [sql, setSql] = useState(STARTER_SQL);
  const [queries, setQueries] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState("");

  const queuedCount = useMemo(
    () => queries.filter((q) => q.status !== "completed").length,
    [queries],
  );
  const completedCount = useMemo(
    () => queries.filter((q) => q.status === "completed").length,
    [queries],
  );
  const completionRate = useMemo(() => {
    if (!queries.length) return 0;
    return (completedCount / queries.length) * 100;
  }, [completedCount, queries.length]);

  useEffect(() => {
    const timer = setInterval(() => {
      setQueries((prev) => {
        const pending = prev.filter((q) => q.status !== "completed");
        if (!pending.length) return prev;
        Promise.all(
          pending.map(async (q) => {
            try {
              return await fetchPriority(q.query_id);
            } catch {
              return null;
            }
          }),
        ).then((updates) => {
          const byId = new Map(updates.filter(Boolean).map((entry) => [entry.query_id, entry]));
          if (!byId.size) return;
          setQueries((current) =>
            current.map((item) => (byId.has(item.query_id) ? { ...item, ...byId.get(item.query_id) } : item)),
          );
          setLastSync(new Date().toLocaleTimeString());
        });
        return prev;
      });
    }, 900);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = async () => {
    setBusy(true);
    setError("");
    try {
      const created = await submitQuery(sql);
      setQueries((prev) => [created, ...prev]);
    } catch (e) {
      setError(e.message || "Unable to submit query");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-sand text-ink">
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-4 p-4 lg:grid-cols-[1.2fr_2fr_1fr]">
        <section className="brutal-panel flex min-h-[340px] flex-col">
          <h2 className="panel-title">Input Console</h2>
          <p className="mb-2 text-sm">Paste SQL here...</p>
          <div className="h-[260px] border-2 border-ink">
            <Editor
              theme="vs-light"
              defaultLanguage="sql"
              value={sql}
              onChange={(val) => setSql(val || "")}
              options={{ minimap: { enabled: false }, fontSize: 14 }}
            />
          </div>
          <div className="mt-3 flex items-center gap-2">
            <button
              className="brutal-btn"
              onClick={handleSubmit}
              disabled={busy || !sql.trim()}
            >
              {busy ? "Predicting..." : "Submit for Scheduling"}
            </button>
            <span className="text-sm">Queued: {queuedCount}</span>
            <span className="text-sm">Completed: {completedCount}</span>
          </div>
          <div className="mt-2 h-3 w-full overflow-hidden border-2 border-ink bg-[#ece8de]">
            <div className="h-full bg-forest transition-all" style={{ width: `${completionRate}%` }} />
          </div>
          <p className="mt-1 text-xs">
            Completion Progress: {completedCount}/{queries.length || 0} ({completionRate.toFixed(0)}%)
          </p>
          {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
        </section>

        <section className="brutal-panel min-h-[520px]">
          <h2 className="panel-title">3D Kinetic Conveyor</h2>
          <SchedulerScene queries={queries} />
          <div className="mt-3 border-2 border-ink p-2 text-xs">
            <span className="font-semibold">Realtime Sync:</span>{" "}
            {lastSync || "Waiting for backend updates..."}
          </div>
          <div className="mt-3 max-h-48 overflow-auto border-2 border-ink">
            <table className="w-full border-collapse text-xs">
              <thead className="bg-[#eeeae0]">
                <tr>
                  <th className="border-b-2 border-ink p-2 text-left">Query ID</th>
                  <th className="border-b-2 border-ink p-2 text-left">Tier</th>
                  <th className="border-b-2 border-ink p-2 text-left">Status</th>
                  <th className="border-b-2 border-ink p-2 text-left">Pred (ms)</th>
                  <th className="border-b-2 border-ink p-2 text-left">Obs (ms)</th>
                </tr>
              </thead>
              <tbody>
                {queries.map((q) => (
                  <tr
                    key={q.query_id}
                    className={q.status === "completed" ? "bg-[#e5f0e3]" : ""}
                  >
                    <td className="border-b border-ink p-2 font-mono">{q.query_id.slice(0, 8)}</td>
                    <td className="border-b border-ink p-2 uppercase">{q.tier}</td>
                    <td className="border-b border-ink p-2">
                      <span
                        className={
                          q.status === "completed"
                            ? "status-pill status-completed"
                            : q.status === "running"
                              ? "status-pill status-running"
                              : "status-pill status-queued"
                        }
                      >
                        {q.status || "queued"}
                      </span>
                    </td>
                    <td className="border-b border-ink p-2">{Number(q.predicted_runtime_ms || 0).toFixed(2)}</td>
                    <td className="border-b border-ink p-2">
                      {q.observed_runtime_ms ? Number(q.observed_runtime_ms).toFixed(2) : "-"}
                    </td>
                  </tr>
                ))}
                {!queries.length ? (
                  <tr>
                    <td className="p-2" colSpan={5}>
                      No results yet. Submit a query to start real-time tracking.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>

        <AnalyticsSidebar />
      </div>
    </div>
  );
}
