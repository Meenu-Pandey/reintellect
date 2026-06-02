import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Eye, GitBranch, Server, Monitor, Radio, Database } from "lucide-react";
import { theme } from "../../styles/theme";

const TECH = [
  { Icon: Eye, name: "YOLOv8", role: "Real-time person detection at 10+ FPS on CPU" },
  { Icon: GitBranch, name: "ByteTrack", role: "Multi-object tracking with 30-frame re-association" },
  { Icon: Server, name: "FastAPI", role: "Async event engine with <500ms processing latency" },
  { Icon: Monitor, name: "React", role: "Real-time dashboard with WebSocket-driven state" },
  { Icon: Radio, name: "WebSockets", role: "Live event streaming to all connected clients" },
  { Icon: Database, name: "SQLite WAL", role: "Persistent analytics with idempotent writes" },
];

export function TechStack() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="technology" ref={ref} style={{ padding: "6rem 2rem" }}>
      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purple, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Technology</div>
        <h2 style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>Built for Production</h2>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.75rem", maxWidth: 800, margin: "0 auto" }}>
        {TECH.map((t, i) => (
          <motion.div
            key={t.name}
            initial={{ opacity: 0, y: 15 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.35, delay: i * 0.06 }}
            whileHover={{ borderColor: "rgba(123,31,162,0.4)" }}
            style={{ padding: "1.25rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, transition: "border-color 0.2s" }}
          >
            <t.Icon size={16} color={theme.accent.purpleMid} style={{ marginBottom: "0.7rem" }} />
            <div style={{ fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.25rem" }}>{t.name}</div>
            <div style={{ fontSize: "0.65rem", color: theme.text.muted, lineHeight: 1.5 }}>{t.role}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
