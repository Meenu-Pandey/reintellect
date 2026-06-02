import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Camera, Scan, Fingerprint, MapPin, Cpu, BarChart3 } from "lucide-react";
import { theme } from "../../styles/theme";

const STAGES = [
  { Icon: Camera, title: "Camera Feed", detail: "5 CCTV streams, 30 FPS" },
  { Icon: Scan, title: "Person Detection", detail: "YOLOv8n real-time inference" },
  { Icon: Fingerprint, title: "Identity Tracking", detail: "ByteTrack persistent IDs" },
  { Icon: MapPin, title: "Journey Mapping", detail: "Zone entry, dwell, exit" },
  { Icon: Cpu, title: "Event Engine", detail: "Conversion & anomaly logic" },
  { Icon: BarChart3, title: "Store Intelligence", detail: "Live retail analytics" },
];

const METRICS = [
  { label: "Visitors", value: "143", trend: "+12%" },
  { label: "Conversion", value: "35%", trend: "+3.2%" },
  { label: "Avg Dwell", value: "47s", trend: "-5s" },
  { label: "Queue Depth", value: "3", trend: "normal" },
];

export function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section id="architecture" ref={ref} style={{ padding: "6rem 2rem", position: "relative" }}>
      {/* Background glow */}
      <div style={{ position: "absolute", top: "30%", left: "5%", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(123,31,162,0.06) 0%, transparent 70%)", filter: "blur(80px)", pointerEvents: "none" }} />

      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "4rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purple, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>System Architecture</div>
        <h2 style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>From Camera to <span style={{ color: theme.accent.purpleMid }}>Business Intelligence</span></h2>
        <p style={{ fontSize: "0.9rem", color: theme.text.secondary, maxWidth: 480, margin: "0.75rem auto 0", lineHeight: 1.6 }}>Raw CCTV footage becomes actionable retail insights through our six-stage AI pipeline.</p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 420px), 1fr))", gap: "3rem", maxWidth: 1050, margin: "0 auto", position: "relative", zIndex: 1 }}>
        {/* Pipeline */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          {STAGES.map((s, i) => (
            <div key={s.title}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                whileHover={{ borderColor: "rgba(123,31,162,0.5)", boxShadow: "0 0 24px rgba(123,31,162,0.1)" }}
                style={{ display: "flex", alignItems: "center", gap: "0.85rem", padding: "0.85rem 1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, cursor: "default", transition: "all 0.2s" }}
              >
                <div style={{ width: 34, height: 34, borderRadius: theme.radiusXs, background: "rgba(123,31,162,0.08)", border: "1px solid rgba(123,31,162,0.2)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <s.Icon size={15} color={theme.accent.purpleMid} />
                </div>
                <div>
                  <div style={{ fontSize: "0.78rem", fontWeight: 600 }}>{s.title}</div>
                  <div style={{ fontSize: "0.65rem", color: theme.text.muted }}>{s.detail}</div>
                </div>
                <div style={{ marginLeft: "auto", width: 5, height: 5, borderRadius: "50%", background: theme.accent.green, opacity: 0.8, flexShrink: 0 }} />
              </motion.div>
              {i < STAGES.length - 1 && (
                <div style={{ display: "flex", justifyContent: "center", height: 16, position: "relative" }}>
                  <div style={{ width: 1, height: "100%", background: `linear-gradient(to bottom, ${theme.borderLight}, rgba(123,31,162,0.3))` }} />
                  <motion.div animate={{ y: [0, 12] }} transition={{ duration: 1, repeat: Infinity, ease: "linear", delay: i * 0.15 }} style={{ position: "absolute", top: 0, width: 3, height: 3, borderRadius: "50%", background: theme.accent.purpleMid, boxShadow: `0 0 6px ${theme.accent.purpleMid}` }} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Live metrics card */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
          style={{ display: "flex", alignItems: "center" }}
        >
          <div style={{ width: "100%", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.5rem", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", width: "50%", height: 1, background: `linear-gradient(90deg, transparent, ${theme.accent.purple}, transparent)` }} />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
              <div><div style={{ fontSize: "0.85rem", fontWeight: 600 }}>Live Store Intelligence</div><div style={{ fontSize: "0.62rem", color: theme.text.muted }}>Purplle Brigade Road</div></div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", padding: "0.2rem 0.5rem", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "9999px" }}>
                <div style={{ width: 5, height: 5, borderRadius: "50%", background: theme.accent.green, animation: "pulse 2s infinite" }} />
                <span style={{ fontSize: "0.58rem", color: theme.accent.green, fontWeight: 600 }}>LIVE</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {METRICS.map((m, i) => (
                <motion.div key={m.label} initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ delay: 0.5 + i * 0.08 }} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem 0.85rem", background: theme.bg.elevated, borderRadius: theme.radiusXs, border: `1px solid ${theme.border}` }}>
                  <span style={{ fontSize: "0.72rem", color: theme.text.secondary }}>{m.label}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontSize: "1rem", fontWeight: 700 }}>{m.value}</span>
                    <span style={{ fontSize: "0.58rem", color: theme.accent.green, background: "rgba(16,185,129,0.08)", padding: "0.1rem 0.35rem", borderRadius: 4 }}>{m.trend}</span>
                  </div>
                </motion.div>
              ))}
            </div>
            <div style={{ marginTop: "1rem", fontSize: "0.62rem", color: theme.text.muted, textAlign: "center" }}>Processing 5 cameras · 8 event types · &lt;500ms latency</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
