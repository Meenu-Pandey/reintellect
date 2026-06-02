/**
 * Anomalies screen.
 *
 * Renders a list of anomaly cards with severity badges.
 * Badge colours: high → red, medium → amber, low → grey.
 * Ordered by detected_at descending (newest first).
 * Auto-refreshes every 60s via useAnomalies hook.
 */

import { useAnomalies } from "../../api/hooks/useAnomalies";
import type { Anomaly, AnomalySeverity } from "../../types/events";

interface Props {
  storeId: string;
}

const SEVERITY_COLORS: Record<AnomalySeverity, string> = {
  high: "#ef4444",    // bg-red-500
  medium: "#f59e0b",  // bg-amber-500
  low: "#9ca3af",     // bg-gray-400
};

const SEVERITY_BG: Record<AnomalySeverity, string> = {
  high: "#fef2f2",
  medium: "#fffbeb",
  low: "#f9fafb",
};

export function AnomaliesScreen({ storeId }: Props) {
  const { data, isLoading, error } = useAnomalies(storeId);

  if (isLoading) {
    return (
      <div>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Anomalies</h2>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              height: "60px",
              background: "#f3f4f6",
              borderRadius: "8px",
              marginBottom: "0.5rem",
            }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return <div style={{ color: "#dc2626" }}>Failed to load anomalies.</div>;
  }

  const anomalies = data?.anomalies ?? [];

  return (
    <div>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
        Anomalies ({anomalies.length})
      </h2>

      {anomalies.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", color: "#888" }}>
          No anomalies detected.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {anomalies.map((anomaly) => (
          <AnomalyCard key={anomaly.anomaly_id} anomaly={anomaly} />
        ))}
      </div>
    </div>
  );
}

function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const badgeColor = SEVERITY_COLORS[anomaly.severity];
  const bgColor = SEVERITY_BG[anomaly.severity];

  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        background: bgColor,
        borderLeft: `4px solid ${badgeColor}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
        <SeverityBadge severity={anomaly.severity} />
        <span style={{ fontWeight: 600, fontSize: "0.85rem" }}>
          {anomaly.anomaly_type.replace(/_/g, " ")}
        </span>
        <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "#888" }}>
          {formatTimestamp(anomaly.detected_at)}
        </span>
      </div>
      <div style={{ fontSize: "0.8rem", color: "#555" }}>
        {anomaly.description}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: AnomalySeverity }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.15rem 0.5rem",
        borderRadius: "9999px",
        fontSize: "0.65rem",
        fontWeight: 700,
        textTransform: "uppercase",
        color: "#fff",
        background: SEVERITY_COLORS[severity],
      }}
    >
      {severity}
    </span>
  );
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}
