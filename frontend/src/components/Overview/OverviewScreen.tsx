/**
 * Overview screen displaying 4 KPI cards:
 * - Visitor count
 * - Conversion rate
 * - Average dwell
 * - Queue depth
 *
 * Values sourced from Zustand WebSocket store for real-time updates.
 */

import { useWebSocketStore } from "../../store/websocket";
import { useMetrics } from "../../api/hooks/useMetrics";

interface Props {
  storeId: string;
}

export function OverviewScreen({ storeId }: Props) {
  const visitorCount = useWebSocketStore((s) => s.visitorCount);
  const queueDepth = useWebSocketStore((s) => s.queueDepth);
  const { data: metrics } = useMetrics(storeId);

  const conversionRate = metrics?.conversion_rate ?? 0;
  const avgDwell = metrics?.avg_visit_duration_seconds ?? 0;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
      }}
    >
      <KpiCard title="Visitors" value={visitorCount} unit="in store" />
      <KpiCard title="Conversion Rate" value={conversionRate} unit="%" />
      <KpiCard title="Avg Dwell" value={Math.round(avgDwell)} unit="seconds" />
      <KpiCard title="Queue Depth" value={queueDepth} unit="in queue" />
    </div>
  );
}

function KpiCard({
  title,
  value,
  unit,
}: {
  title: string;
  value: number;
  unit: string;
}) {
  return (
    <div
      style={{
        padding: "1.5rem",
        border: "1px solid #e0e0e0",
        borderRadius: "8px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.5rem" }}>
        {title}
      </div>
      <div style={{ fontSize: "2rem", fontWeight: 700 }}>{value}</div>
      <div style={{ fontSize: "0.75rem", color: "#999" }}>{unit}</div>
    </div>
  );
}
