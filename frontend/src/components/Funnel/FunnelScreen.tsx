import { motion } from "framer-motion";
import { theme } from "../../styles/theme";
import { useFunnel } from "../../api/hooks/useFunnel";

interface Props { storeId: string; }

export function FunnelScreen({ storeId }: Props) {
  const { data, isLoading } = useFunnel(storeId);

  if (isLoading) return <div style={{ padding: "2rem", textAlign: "center", color: theme.text.muted }}>Loading funnel...</div>;
  if (!data?.data_available) return <div style={{ padding: "2rem", textAlign: "center", color: theme.text.muted }}>No funnel data available.</div>;

  const total = data.total_visitors;
  const stages = [{ name: "Store Entry", count: total, zone_id: "_entry" }, ...data.stages.map(s => ({ name: s.zone_name.replace("ZONE_", ""), count: s.visitor_count, zone_id: s.zone_id }))];
  const max = stages[0].count;

  return (
    <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.25rem" }}>
      <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.25rem" }}>Customer Journey Funnel</div>
      <div style={{ fontSize: "0.75rem", color: theme.text.muted, marginBottom: "1.25rem" }}>Visitor progression through store zones</div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
        {stages.map((s, i) => {
          const pct = max > 0 ? (s.count / max) * 100 : 0;
          const prev = i > 0 ? stages[i - 1].count : s.count;
          const drop = prev > 0 ? Math.round(((prev - s.count) / prev) * 100) : 0;
          const isLast = i === stages.length - 1;

          return (
            <div key={s.zone_id}>
              {i > 0 && drop > 0 && (
                <div style={{ padding: "0.15rem 0 0.15rem 1rem", fontSize: "0.72rem", color: theme.accent.red }}>↓ {drop}% drop-off</div>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <div style={{ flex: 1, height: 36, background: theme.bg.elevated, borderRadius: theme.radiusXs, position: "relative", overflow: "hidden" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, delay: i * 0.08 }}
                    style={{ height: "100%", background: isLast ? theme.accent.green : `rgba(123,31,162,${0.9 - i * 0.12})`, borderRadius: theme.radiusXs }}
                  />
                  <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 0.7rem" }}>
                    <span style={{ fontSize: "0.82rem", fontWeight: 500, zIndex: 1 }}>{s.name}</span>
                    <span style={{ fontSize: "0.82rem", fontWeight: 700, zIndex: 1 }}>{s.count}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: "1rem", padding: "0.6rem 0.75rem", background: theme.bg.elevated, borderRadius: theme.radiusXs, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.8rem", color: theme.text.secondary }}>End-to-end conversion</span>
        <span style={{ fontSize: "0.9rem", fontWeight: 700, color: theme.accent.green }}>{total > 0 ? ((stages[stages.length - 1].count / total) * 100).toFixed(1) : 0}%</span>
      </div>
    </div>
  );
}
