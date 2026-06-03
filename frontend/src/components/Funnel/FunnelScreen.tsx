import { motion } from "framer-motion";
import { theme } from "../../styles/theme";
import { useFunnel } from "../../api/hooks/useFunnel";
import { TrendingDown, TrendingUp } from "lucide-react";

interface Props { storeId: string; }

export function FunnelScreen({ storeId }: Props) {
  const { data, isLoading } = useFunnel(storeId);

  if (isLoading) return <Skeleton />;
  if (!data?.data_available) return <Empty />;

  const total = data.total_visitors;
  const stages = [{ name: "Store Entry", count: total, zone_id: "_entry" }, ...data.stages.map(s => ({ name: s.zone_name.replace("ZONE_", ""), count: s.visitor_count, zone_id: s.zone_id }))];
  const max = stages[0].count;
  const convRate = total > 0 ? ((stages[stages.length - 1].count / total) * 100).toFixed(1) : "0.0";

  return (
    <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <div>
          <div style={{ fontSize: "0.92rem", fontWeight: 600, letterSpacing: "-0.01em" }}>Customer Journey Funnel</div>
          <div style={{ fontSize: "0.7rem", color: theme.text.muted, marginTop: "0.15rem" }}>Visitor flow through store zones</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "1.6rem", fontWeight: 800, color: theme.accent.green, letterSpacing: "-0.04em" }}>{convRate}%</div>
          <div style={{ fontSize: "0.62rem", color: theme.text.muted }}>End-to-end conversion</div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
        {stages.map((s, i) => {
          const widthPct = max > 0 ? (s.count / max) * 100 : 0;
          const prev = i > 0 ? stages[i - 1].count : s.count;
          const drop = prev > 0 && i > 0 ? Math.round(((prev - s.count) / prev) * 100) : 0;
          const isLast = i === stages.length - 1;
          const opacity = 1 - (i / stages.length) * 0.4;

          return (
            <div key={s.zone_id}>
              {/* Drop-off indicator */}
              {i > 0 && drop > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", padding: "0.15rem 0.5rem", fontSize: "0.65rem", color: theme.accent.red }}>
                  <TrendingDown size={10} /> {drop}% drop-off between stages
                </div>
              )}

              {/* Stage bar */}
              <div style={{ position: "relative", height: 44, background: theme.bg.elevated, borderRadius: theme.radiusXs, overflow: "hidden" }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.7, delay: i * 0.08 }}
                  style={{
                    position: "absolute", top: 0, left: 0, height: "100%",
                    background: isLast
                      ? `linear-gradient(90deg, #10b981, #059669aa)`
                      : `linear-gradient(90deg, rgba(124,58,237,${opacity}), rgba(139,92,246,${opacity * 0.7}))`,
                    borderRadius: theme.radiusXs,
                  }}
                />
                <div style={{ position: "relative", height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 0.85rem", zIndex: 1 }}>
                  <span style={{ fontSize: "0.82rem", fontWeight: 500 }}>{s.name}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontSize: "0.8rem", fontWeight: 700 }}>{s.count}</span>
                    {max > 0 && <span style={{ fontSize: "0.62rem", color: theme.text.muted }}>{((s.count / max) * 100).toFixed(0)}%</span>}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom summary */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem", marginTop: "1.25rem" }}>
        <div style={{ padding: "0.75rem", background: theme.bg.elevated, borderRadius: theme.radiusXs }}>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: theme.accent.blue }}>{total}</div>
          <div style={{ fontSize: "0.65rem", color: theme.text.muted }}>Total store entries</div>
        </div>
        <div style={{ padding: "0.75rem", background: theme.bg.elevated, borderRadius: theme.radiusXs }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <span style={{ fontSize: "1.1rem", fontWeight: 700, color: theme.accent.green }}>{convRate}%</span>
            <TrendingUp size={14} color={theme.accent.green} />
          </div>
          <div style={{ fontSize: "0.65rem", color: theme.text.muted }}>Conversion rate</div>
        </div>
      </div>
    </div>
  );
}

function Skeleton() {
  return <div style={{ height: 300, background: theme.bg.card, borderRadius: theme.radius, animation: "pulse 1.5s infinite" }} />;
}

function Empty() {
  return (
    <div style={{ padding: "3rem", textAlign: "center", color: theme.text.muted, background: theme.bg.card, borderRadius: theme.radius, border: `1px solid ${theme.border}` }}>
      No funnel data yet. Waiting for visitor events...
    </div>
  );
}
