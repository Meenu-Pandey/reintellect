import { motion } from "framer-motion";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { theme, SEVERITY_COLORS } from "../../styles/theme";
import { useAnomalies } from "../../api/hooks/useAnomalies";
import type { Anomaly, AnomalySeverity } from "../../types/events";

interface Props { storeId: string; }

const ICONS: Record<string, typeof AlertTriangle> = { high: AlertTriangle, medium: AlertCircle, low: Info };
const RECS: Record<string, string> = {
  QUEUE_BUILDUP: "Deploy additional cashier or open express lane",
  EMPTY_STORE: "Verify operating hours or check for events",
  UNUSUAL_DWELL: "Review for security concern or high-engagement customer",
  CAMERA_OVERLAP_CONFLICT: "Review camera calibration and zone boundaries",
};

export function AnomaliesScreen({ storeId }: Props) {
  const { data, isLoading } = useAnomalies(storeId);
  if (isLoading) return <div style={{ color: theme.text.muted, padding: "2rem", textAlign: "center" }}>Loading...</div>;

  const anomalies = data?.anomalies ?? [];
  const counts = { high: 0, medium: 0, low: 0 };
  anomalies.forEach(a => { counts[a.severity as keyof typeof counts]++; });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      {/* Summary */}
      <div style={{ display: "flex", gap: "0.75rem", padding: "0.7rem 1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm }}>
        {(["high", "medium", "low"] as AnomalySeverity[]).map(s => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: SEVERITY_COLORS[s] }} />
            <span style={{ fontSize: "0.85rem", fontWeight: 600, color: SEVERITY_COLORS[s] }}>{counts[s]}</span>
            <span style={{ fontSize: "0.75rem", color: theme.text.muted }}>{s}</span>
          </div>
        ))}
      </div>

      {anomalies.length === 0 && <div style={{ padding: "2rem", textAlign: "center", color: theme.text.muted, background: theme.bg.card, borderRadius: theme.radiusSm, border: `1px solid ${theme.border}` }}>No anomalies detected.</div>}

      {anomalies.map((a, i) => <AnomalyCard key={a.anomaly_id} anomaly={a} index={i} />)}
    </div>
  );
}

function AnomalyCard({ anomaly, index }: { anomaly: Anomaly; index: number }) {
  const color = SEVERITY_COLORS[anomaly.severity];
  const Icon = ICONS[anomaly.severity] || Info;
  const rec = RECS[anomaly.anomaly_type] || "Investigate and take action";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      style={{ padding: "0.85rem 1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderLeft: `3px solid ${color}`, borderRadius: theme.radiusSm }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
        <Icon size={15} color={color} />
        <span style={{ fontSize: "0.88rem", fontWeight: 600 }}>{anomaly.anomaly_type.replace(/_/g, " ")}</span>
        <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: theme.text.muted }}>{new Date(anomaly.detected_at).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit" })}</span>
      </div>
      <div style={{ fontSize: "0.82rem", color: theme.text.secondary, marginBottom: "0.35rem" }}>{anomaly.description}</div>
      <div style={{ fontSize: "0.78rem", color: theme.accent.purpleMid, fontStyle: "italic" }}>→ {rec}</div>
    </motion.div>
  );
}
