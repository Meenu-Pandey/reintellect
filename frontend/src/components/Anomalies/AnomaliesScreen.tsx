import { motion } from "framer-motion";
import { AlertTriangle, AlertCircle, Info, ShieldAlert } from "lucide-react";
import { theme, SEVERITY_COLORS } from "../../styles/theme";
import { useAnomalies } from "../../api/hooks/useAnomalies";
import type { Anomaly, AnomalySeverity } from "../../types/events";

interface Props { storeId: string; }

const ICONS: Record<string, typeof AlertTriangle> = { high: AlertTriangle, medium: AlertCircle, low: Info };

const RECS: Record<string, string> = {
  QUEUE_BUILDUP: "Deploy additional cashier or open express lane immediately",
  EMPTY_STORE: "Verify operating hours config or check for scheduled event",
  UNUSUAL_DWELL: "Review for high-engagement customer or security concern",
  CAMERA_OVERLAP_CONFLICT: "Calibrate zone boundaries and review camera overlap regions",
};

const AFFECTED: Record<string, string> = {
  QUEUE_BUILDUP: "Checkout Queue",
  EMPTY_STORE: "Full Store",
  UNUSUAL_DWELL: "Brand Zone",
  CAMERA_OVERLAP_CONFLICT: "Multi-Zone",
};

export function AnomaliesScreen({ storeId }: Props) {
  const { data, isLoading } = useAnomalies(storeId);

  if (isLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {[1, 2, 3].map(i => <div key={i} style={{ height: 80, background: theme.bg.card, borderRadius: theme.radiusSm, animation: "pulse 1.5s infinite" }} />)}
      </div>
    );
  }

  const anomalies = data?.anomalies ?? [];
  const counts: Record<AnomalySeverity, number> = { high: 0, medium: 0, low: 0 };
  anomalies.forEach(a => { counts[a.severity as AnomalySeverity]++; });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
      {/* SOC-style header */}
      <div style={{ display: "flex", gap: "0.75rem", padding: "0.85rem 1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, alignItems: "center" }}>
        <ShieldAlert size={16} color={theme.accent.purpleMid} />
        <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Anomaly Detection</span>
        <div style={{ flex: 1 }} />
        {(["high", "medium", "low"] as AnomalySeverity[]).map(s => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: SEVERITY_COLORS[s], boxShadow: counts[s] > 0 ? `0 0 8px ${SEVERITY_COLORS[s]}` : "none" }} />
            <span style={{ fontSize: "0.78rem", fontWeight: 600, color: SEVERITY_COLORS[s] }}>{counts[s]}</span>
            <span style={{ fontSize: "0.65rem", color: theme.text.muted }}>{s}</span>
          </div>
        ))}
        <span style={{ fontSize: "0.65rem", color: theme.text.muted, marginLeft: "0.5rem" }}>Auto-refresh 60s</span>
      </div>

      {anomalies.length === 0 && (
        <div style={{ padding: "3rem", textAlign: "center", color: theme.text.muted, background: theme.bg.card, borderRadius: theme.radiusSm, border: `1px solid ${theme.border}`, fontSize: "0.85rem" }}>
          ✓ No anomalies detected. System operating normally.
        </div>
      )}

      {anomalies.map((a, i) => <AnomalyCard key={a.anomaly_id} anomaly={a} index={i} />)}
    </div>
  );
}

function AnomalyCard({ anomaly, index }: { anomaly: Anomaly; index: number }) {
  const color = SEVERITY_COLORS[anomaly.severity];
  const Icon = ICONS[anomaly.severity] || Info;
  const rec = RECS[anomaly.anomaly_type] || "Investigate and take appropriate action";
  const zone = AFFECTED[anomaly.anomaly_type] || "Unknown";

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: index * 0.05 }}
      whileHover={{ x: 2 }}
      style={{ padding: "1rem 1.1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderLeft: `3px solid ${color}`, borderRadius: theme.radiusSm, cursor: "default", transition: "transform 0.15s" }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
        <Icon size={14} color={color} />
        <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{anomaly.anomaly_type.replace(/_/g, " ")}</span>
        <span style={{ fontSize: "0.58rem", fontWeight: 700, textTransform: "uppercase", color: "#fff", background: color, padding: "0.12rem 0.45rem", borderRadius: 4 }}>{anomaly.severity}</span>
        <span style={{ marginLeft: "auto", fontSize: "0.65rem", color: theme.text.muted }}>
          {new Date(anomaly.detected_at).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit" })} IST
        </span>
      </div>
      <div style={{ fontSize: "0.78rem", color: theme.text.secondary, marginBottom: "0.45rem", lineHeight: 1.5 }}>{anomaly.description}</div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: "0.72rem", color: theme.accent.purpleLight, fontStyle: "italic" }}>→ {rec}</div>
        <span style={{ fontSize: "0.6rem", color: theme.text.muted, padding: "0.15rem 0.4rem", background: theme.bg.elevated, borderRadius: 4 }}>{zone}</span>
      </div>
    </motion.div>
  );
}
