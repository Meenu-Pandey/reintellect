import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Eye, GitBranch, Server, Monitor, Radio, Database, Box, Code2 } from "lucide-react";
import { theme } from "../../styles/theme";

const TECH = [
  { Icon: Eye, name: "YOLOv8", role: "Person detection", detail: "10+ FPS on CPU", color: "#3b82f6" },
  { Icon: GitBranch, name: "ByteTrack", role: "Multi-object tracking", detail: "30-frame re-ID window", color: "#8b5cf6" },
  { Icon: Server, name: "FastAPI", role: "Event engine & APIs", detail: "<500ms processing", color: "#10b981" },
  { Icon: Monitor, name: "React + TS", role: "Live dashboard", detail: "WebSocket-driven", color: "#06b6d4" },
  { Icon: Radio, name: "WebSockets", role: "Real-time streaming", detail: "Sub-100ms broadcast", color: "#ec4899" },
  { Icon: Database, name: "SQLite WAL", role: "Analytics store", detail: "Idempotent writes", color: "#f59e0b" },
  { Icon: Box, name: "Docker", role: "One-command deploy", detail: "Compose stack", color: "#0ea5e9" },
  { Icon: Code2, name: "Shapely", role: "Zone geometry", detail: "Polygon containment", color: "#a78bfa" },
];

export function TechStack() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="technology" ref={ref} style={{ padding: "6rem clamp(1rem,4vw,3rem)" }}>
      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purpleLight, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Built With</div>
        <h2 style={{ fontSize: "clamp(1.8rem,3vw,2.4rem)", fontWeight: 700, letterSpacing: "-0.03em", fontFamily: "'Space Grotesk',sans-serif" }}>Production-Grade Stack</h2>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))", gap: "0.75rem", maxWidth: 920, margin: "0 auto" }}>
        {TECH.map((t, i) => (
          <motion.div key={t.name} initial={{ opacity: 0, y: 14 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.35, delay: i * 0.05 }}
            whileHover={{ borderColor: `${t.color}40`, y: -2 }}
            style={{ padding: "1.1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, transition: "all 0.2s", cursor: "default" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.5rem" }}>
              <div style={{ width: 30, height: 30, borderRadius: theme.radiusXs, background: `${t.color}12`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <t.Icon size={14} color={t.color} />
              </div>
              <span style={{ fontWeight: 600, fontSize: "0.85rem" }}>{t.name}</span>
            </div>
            <div style={{ fontSize: "0.72rem", color: theme.text.secondary }}>{t.role}</div>
            <div style={{ fontSize: "0.62rem", color: theme.text.muted, marginTop: "0.2rem" }}>{t.detail}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
