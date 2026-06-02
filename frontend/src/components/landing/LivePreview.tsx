import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Users, TrendingUp, Clock, AlertTriangle } from "lucide-react";
import { theme } from "../../styles/theme";

const KPIS = [
  { icon: Users, label: "Unique Visitors", value: 143, suffix: "", color: theme.accent.blue },
  { icon: TrendingUp, label: "Conversion Rate", value: 34.9, suffix: "%", color: theme.accent.green },
  { icon: Clock, label: "Average Dwell", value: 47, suffix: "s", color: theme.accent.purpleMid },
  { icon: AlertTriangle, label: "Anomalies Detected", value: 5, suffix: "", color: theme.accent.amber },
];

const FUNNEL = [
  { stage: "Store Entry", count: 143, pct: 100 },
  { stage: "Lakme Zone", count: 77, pct: 54 },
  { stage: "Maybelline Zone", count: 51, pct: 36 },
  { stage: "Checkout Queue", count: 40, pct: 28 },
  { stage: "Purchase", count: 50, pct: 35 },
];

export function LivePreview() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="features" ref={ref} style={{ padding: "5rem 2rem" }}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : {}}
        transition={{ duration: 0.5 }}
        style={{ textAlign: "center", marginBottom: "3rem" }}
      >
        <div style={{ fontSize: "0.65rem", color: theme.accent.purple, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Live Intelligence</div>
        <h2 style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>Real Metrics, Real Time</h2>
      </motion.div>

      <div style={{ maxWidth: "1000px", margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 400px), 1fr))", gap: "1.5rem" }}>
        {/* KPI Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.75rem" }}>
          {KPIS.map((kpi, i) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              style={{ padding: "1.25rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius }}
            >
              <kpi.icon size={16} color={kpi.color} style={{ marginBottom: "0.6rem" }} />
              <div style={{ fontSize: "1.6rem", fontWeight: 700, color: kpi.color }}>{kpi.value}{kpi.suffix}</div>
              <div style={{ fontSize: "0.65rem", color: theme.text.muted, marginTop: "0.2rem" }}>{kpi.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Mini Funnel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.3 }}
          style={{ padding: "1.25rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius }}
        >
          <div style={{ fontSize: "0.72rem", color: theme.text.secondary, fontWeight: 500, marginBottom: "1rem" }}>Customer Journey Funnel</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {FUNNEL.map((s, i) => (
              <div key={s.stage} style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <div style={{ flex: 1, height: 24, background: theme.bg.elevated, borderRadius: 4, overflow: "hidden", position: "relative" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={isInView ? { width: `${s.pct}%` } : {}}
                    transition={{ duration: 0.6, delay: 0.4 + i * 0.08 }}
                    style={{ height: "100%", background: i === FUNNEL.length - 1 ? theme.accent.green : `rgba(123,31,162,${1 - i * 0.15})`, borderRadius: 4 }}
                  />
                  <span style={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", fontSize: "0.6rem", fontWeight: 500, color: theme.text.primary }}>{s.stage}</span>
                </div>
                <span style={{ fontSize: "0.68rem", color: theme.text.secondary, minWidth: 32, textAlign: "right" }}>{s.count}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
