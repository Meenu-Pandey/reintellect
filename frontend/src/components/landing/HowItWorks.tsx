import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Camera, Scan, Fingerprint, MapPin, AlertTriangle, BarChart3 } from "lucide-react";
import { theme } from "../../styles/theme";

const STAGES = [
  { Icon: Camera, title: "CCTV Cameras", detail: "5 live feeds · 30 FPS · Brigade Road", color: "#10b981" },
  { Icon: Scan, title: "YOLOv8 Detection", detail: "Person detection · 10+ FPS on CPU", color: "#3b82f6" },
  { Icon: Fingerprint, title: "ByteTrack", detail: "Persistent IDs · 30-frame re-association", color: "#8b5cf6" },
  { Icon: MapPin, title: "Event Engine", detail: "Entry · Zone · Queue · Exit events", color: "#ec4899" },
  { Icon: AlertTriangle, title: "Anomaly Engine", detail: "Queue buildup · Empty store · Overlap", color: "#f59e0b" },
  { Icon: BarChart3, title: "Retail Intelligence", detail: "Conversion · Funnel · Heatmap · Insights", color: "#06b6d4" },
];

const LIVE = [
  { label: "Visitors", value: "143", trend: "+12%" },
  { label: "Conversion", value: "35%", trend: "+3.2%" },
  { label: "Avg Dwell", value: "47s", trend: "-5s" },
  { label: "Queue Depth", value: "3", trend: "normal" },
];

export function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section id="architecture" ref={ref} style={{ padding: "6rem clamp(1rem,4vw,3rem)", position: "relative" }}>
      <div style={{ position: "absolute", top: "20%", left: "5%", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(124,58,237,0.05) 0%, transparent 70%)", filter: "blur(80px)", pointerEvents: "none" }} />

      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "4rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purpleLight, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>System Architecture</div>
        <h2 style={{ fontSize: "clamp(1.8rem,3vw,2.4rem)", fontWeight: 700, letterSpacing: "-0.03em", fontFamily: "'Space Grotesk',sans-serif" }}>
          From Camera to <span style={{ color: theme.accent.purpleMid }}>Business Intelligence</span>
        </h2>
        <p style={{ fontSize: "0.95rem", color: theme.text.secondary, maxWidth: 460, margin: "0.75rem auto 0" }}>
          Six stages. One pipeline. Raw footage becomes actionable retail analytics in under 500ms.
        </p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(min(100%,440px),1fr))", gap: "3rem", maxWidth: 1060, margin: "0 auto", position: "relative", zIndex: 1 }}>
        {/* Pipeline */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
          {STAGES.map((s, i) => (
            <div key={s.title}>
              <motion.div initial={{ opacity: 0, x: -20 }} animate={isInView ? { opacity: 1, x: 0 } : {}} transition={{ duration: 0.4, delay: i * 0.08 }}
                whileHover={{ borderColor: `${s.color}50`, boxShadow: `0 0 20px ${s.color}10` }}
                style={{ display: "flex", alignItems: "center", gap: "0.85rem", padding: "0.85rem 1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, cursor: "default", transition: "all 0.2s" }}
              >
                <div style={{ width: 36, height: 36, borderRadius: theme.radiusXs, background: `${s.color}12`, border: `1px solid ${s.color}25`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <s.Icon size={15} color={s.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 600, color: theme.text.primary }}>{s.title}</div>
                  <div style={{ fontSize: "0.66rem", color: theme.text.muted }}>{s.detail}</div>
                </div>
                <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.8, 0.4, 0.8] }} transition={{ duration: 2 + i * 0.3, repeat: Infinity }} style={{ width: 6, height: 6, borderRadius: "50%", background: theme.accent.green, flexShrink: 0 }} />
              </motion.div>
              {i < STAGES.length - 1 && (
                <div style={{ display: "flex", justifyContent: "center", height: 18, position: "relative" }}>
                  <div style={{ width: 1, height: "100%", background: `linear-gradient(to bottom, ${s.color}40, ${STAGES[i + 1].color}40)` }} />
                  <motion.div animate={{ y: [0, 14] }} transition={{ duration: 0.9, repeat: Infinity, ease: "linear", delay: i * 0.15 }} style={{ position: "absolute", top: 0, width: 3, height: 3, borderRadius: "50%", background: s.color, boxShadow: `0 0 6px ${s.color}` }} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Live metrics */}
        <motion.div initial={{ opacity: 0, x: 30 }} animate={isInView ? { opacity: 1, x: 0 } : {}} transition={{ duration: 0.6, delay: 0.3 }} style={{ display: "flex", alignItems: "center" }}>
          <div style={{ width: "100%", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.5rem", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", width: "60%", height: 1, background: `linear-gradient(90deg, transparent, ${theme.accent.purple}, transparent)` }} />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
              <div>
                <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>Live Store Intelligence</div>
                <div style={{ fontSize: "0.65rem", color: theme.text.muted, marginTop: "0.15rem" }}>Purplle Brigade Road · Today</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", padding: "0.22rem 0.55rem", background: theme.accent.greenDim, border: "1px solid rgba(16,185,129,0.25)", borderRadius: "9999px" }}>
                <motion.div animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.4, repeat: Infinity }} style={{ width: 5, height: 5, borderRadius: "50%", background: theme.accent.green }} />
                <span style={{ fontSize: "0.6rem", color: theme.accent.green, fontWeight: 600 }}>LIVE</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
              {LIVE.map((m, i) => (
                <motion.div key={m.label} initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ delay: 0.5 + i * 0.08 }} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem 0.85rem", background: theme.bg.elevated, borderRadius: theme.radiusXs, border: `1px solid ${theme.border}` }}>
                  <span style={{ fontSize: "0.78rem", color: theme.text.secondary }}>{m.label}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
                    <span style={{ fontSize: "1.05rem", fontWeight: 700 }}>{m.value}</span>
                    <span style={{ fontSize: "0.6rem", color: theme.accent.green, background: theme.accent.greenDim, padding: "0.1rem 0.35rem", borderRadius: 4, fontWeight: 600 }}>{m.trend}</span>
                  </div>
                </motion.div>
              ))}
            </div>
            <div style={{ marginTop: "1rem", textAlign: "center", fontSize: "0.62rem", color: theme.text.muted }}>5 cameras · 8 event types · &lt;500ms latency</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
