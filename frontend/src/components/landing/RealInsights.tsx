import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { AlertTriangle, TrendingUp, Clock, Users, Zap } from "lucide-react";
import { theme } from "../../styles/theme";

const INSIGHTS = [
  { Icon: AlertTriangle, label: "Anomaly Detected", detail: "Queue buildup: depth 7 sustained for 3+ minutes at checkout", time: "14:15 IST", color: "#ef4444", sev: "HIGH" },
  { Icon: TrendingUp, label: "Conversion Spike", detail: "Conversion rate increased 12% following staff deployment to skincare zone", time: "13:42 IST", color: "#10b981", sev: "GOOD" },
  { Icon: Clock, label: "Peak Traffic", detail: "Highest footfall between 17:00–19:00 with 35 visitors/hour", time: "Today", color: "#8b5cf6", sev: "INFO" },
  { Icon: Users, label: "Zone Engagement", detail: "Lakme zone shows highest dwell time (avg 68s) — 40% above store average", time: "Today", color: "#3b82f6", sev: "INFO" },
  { Icon: Zap, label: "Camera Conflict", detail: "Track 47 detected in non-adjacent zones MAYBELLINE & SKINCARE within 1.2s", time: "08:52 IST", color: "#f59e0b", sev: "WARN" },
];

export function RealInsights() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section ref={ref} style={{ padding: "6rem clamp(1rem,4vw,3rem)" }}>
      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purpleLight, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Actionable Intelligence</div>
        <h2 style={{ fontSize: "clamp(1.8rem,3vw,2.4rem)", fontWeight: 700, letterSpacing: "-0.03em", fontFamily: "'Space Grotesk',sans-serif" }}>Insights Generated Today</h2>
        <p style={{ fontSize: "0.95rem", color: theme.text.secondary, maxWidth: 440, margin: "0.75rem auto 0" }}>Real insights from actual Purplle Brigade Road store data.</p>
      </motion.div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", maxWidth: 700, margin: "0 auto" }}>
        {INSIGHTS.map((ins, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -16 }} animate={isInView ? { opacity: 1, x: 0 } : {}} transition={{ duration: 0.4, delay: i * 0.1 }}
            whileHover={{ x: 4 }}
            style={{ display: "flex", alignItems: "flex-start", gap: "1rem", padding: "1rem 1.25rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderLeft: `3px solid ${ins.color}`, borderRadius: theme.radiusSm, cursor: "default", transition: "transform 0.2s" }}
          >
            <div style={{ width: 32, height: 32, borderRadius: theme.radiusXs, background: `${ins.color}12`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: "0.1rem" }}>
              <ins.Icon size={14} color={ins.color} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>{ins.label}</span>
                <span style={{ fontSize: "0.56rem", fontWeight: 700, color: ins.color, background: `${ins.color}12`, padding: "0.1rem 0.4rem", borderRadius: 4 }}>{ins.sev}</span>
              </div>
              <div style={{ fontSize: "0.75rem", color: theme.text.secondary, lineHeight: 1.5 }}>{ins.detail}</div>
            </div>
            <div style={{ fontSize: "0.62rem", color: theme.text.muted, flexShrink: 0, marginTop: "0.1rem" }}>{ins.time}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
