import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { TrendingUp, UserX, Timer, ShieldAlert } from "lucide-react";
import { theme } from "../../styles/theme";

const IMPACTS = [
  { Icon: TrendingUp, metric: "35%", title: "Conversion Visibility", desc: "Track customer journeys from entry to purchase." },
  { Icon: UserX, metric: "26%", title: "Queue Intelligence", desc: "Detect abandoned purchases before they happen." },
  { Icon: Timer, metric: "68s", title: "Dwell Analytics", desc: "Identify high-engagement brand zones." },
  { Icon: ShieldAlert, metric: "5", title: "Anomaly Detection", desc: "Spot unusual patterns instantly." },
];

export function BusinessImpact() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section ref={ref} style={{ padding: "6rem 2rem" }}>
      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purple, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Business Impact</div>
        <h2 style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>Intelligence That Drives Revenue</h2>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", maxWidth: 1000, margin: "0 auto" }}>
        {IMPACTS.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            whileHover={{ borderColor: "rgba(123,31,162,0.4)", y: -4 }}
            style={{ padding: "1.5rem 1.25rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, cursor: "default", transition: "all 0.2s" }}
          >
            <item.Icon size={18} color={theme.accent.purpleMid} style={{ marginBottom: "1rem" }} />
            <div style={{ fontSize: "1.8rem", fontWeight: 800, color: theme.accent.purpleMid, marginBottom: "0.3rem" }}>{item.metric}</div>
            <div style={{ fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.4rem" }}>{item.title}</div>
            <div style={{ fontSize: "0.7rem", color: theme.text.muted, lineHeight: 1.5 }}>{item.desc}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
