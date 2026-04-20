import { useEffect, useState } from "react";
import { fetchMetrics } from "./api";

function MiniChart({ label, value }) {
  return (
    <div className="border-2 border-ink p-2">
      <p className="text-xs uppercase tracking-wide">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      <svg viewBox="0 0 100 30" className="mt-2 h-8 w-full">
        <polyline
          fill="none"
          stroke="#1A1A1A"
          strokeWidth="2"
          points="0,22 20,20 40,16 60,17 80,9 100,7"
        />
      </svg>
    </div>
  );
}

export default function AnalyticsSidebar() {
  const [metrics, setMetrics] = useState({
    average_wait_time_ms: 0,
    throughput_qps: 0,
    prediction_rmse_ms: 0,
  });

  useEffect(() => {
    let stopped = false;
    const run = async () => {
      try {
        const latest = await fetchMetrics();
        if (!stopped) setMetrics(latest);
      } catch {
        // Keep prior metrics when backend is unavailable.
      }
    };
    run();
    const t = setInterval(run, 1500);
    return () => {
      stopped = true;
      clearInterval(t);
    };
  }, []);

  return (
    <aside className="brutal-panel">
      <h2 className="panel-title">Analytics</h2>
      <div className="space-y-3">
        <MiniChart label="AWT (ms)" value={metrics.average_wait_time_ms.toFixed(2)} />
        <MiniChart label="Throughput (QPS)" value={metrics.throughput_qps.toFixed(3)} />
        <MiniChart label="Prediction RMSE" value={metrics.prediction_rmse_ms.toFixed(2)} />
      </div>
    </aside>
  );
}
