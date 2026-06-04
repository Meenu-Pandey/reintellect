import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight, ChevronDown } from "lucide-react";
import { theme } from "../../styles/theme";

const METRICS = [
  { label: "Visitors Today", value: "143", color: theme.accent.blue },
  { label: "Conversion", value: "35%", color: theme.accent.green },
  { label: "Avg Dwell", value: "47s", color: theme.accent.purpleMid },
  { label: "Anomalies", value: "3", color: theme.accent.amber },
];

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", padding: "7rem 2rem 4rem", position: "relative", overflow: "hidden" }}>
      {/* Dot grid */}
      <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle at 1px 1px, rgba(139,92,246,0.04) 1px, transparent 0)", backgroundSize: "40px 40px", pointerEvents: "none" }} />
      {/* Glow orbs */}
      <div style={{ position: "absolute", top: "15%", left: "50%", transform: "translateX(-50%)", width: 800, height: 500, borderRadius: "50%", background: "radial-gradient(ellipse, rgba(124,58,237,0.14) 0%, transparent 70%)", filter: "blur(60px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: "10%", left: "20%", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)", filter: "blur(50px)", pointerEvents: "none" }} />

      {/* Badge */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.35rem 0.85rem", background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.25)", borderRadius: "9999px", marginBottom: "2rem", fontSize: "0.72rem", color: theme.accent.purpleLight, fontWeight: 500 }}
      >
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: theme.accent.green, animation: "pulse 2s infinite", flexShrink: 0 }} />
        Built for Purplle Tech Challenge 2026
      </motion.div>

      {/* Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 20, filter: "blur(12px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0)" }}
        transition={{ duration: 0.9, delay: 0.1 }}
        style={{ fontSize: "clamp(2.4rem, 5.5vw, 4.4rem)", fontWeight: 800, lineHeight: 1.08, maxWidth: 840, letterSpacing: "-0.04em", marginBottom: "1.5rem", fontFamily: "'Space Grotesk', sans-serif" }}
      >
        Transform Retail CCTV Into{" "}
        <span style={{ background: "linear-gradient(135deg, #a78bfa 0%, #7c3aed 50%, #ec4899 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
          Business Intelligence
        </span>
      </motion.h1>

      <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.25 }}
        style={{ fontSize: "1.1rem", color: theme.text.secondary, maxWidth: 560, lineHeight: 1.65, marginBottom: "2.5rem" }}
      >
        Convert ordinary security cameras into real-time visitor analytics, conversion insights, queue intelligence, and anomaly detection.
      </motion.p>

      {/* Buttons */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.4 }}
        style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", justifyContent: "center" }}
      >
        <button onClick={() => navigate("/dashboard")} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.78rem 1.75rem", background: "linear-gradient(135deg,#7c3aed,#6d28d9)", color: "#fff", border: "none", borderRadius: theme.radiusSm, fontSize: "0.88rem", fontWeight: 600, cursor: "pointer", boxShadow: "0 0 30px rgba(124,58,237,0.35)", transition: "box-shadow 0.2s" }}
          onMouseEnter={e => (e.currentTarget.style.boxShadow = "0 0 50px rgba(124,58,237,0.55)")}
          onMouseLeave={e => (e.currentTarget.style.boxShadow = "0 0 30px rgba(124,58,237,0.35)")}
        >Launch Live Dashboard <ArrowRight size={16} /></button>
        <button onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })} style={{ padding: "0.78rem 1.75rem", background: "transparent", color: theme.text.secondary, border: `1px solid ${theme.borderLight}`, borderRadius: theme.radiusSm, fontSize: "0.88rem", fontWeight: 500, cursor: "pointer" }}>Explore Architecture</button>
      </motion.div>

      {/* Floating KPI chips */}
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }}
        style={{ marginTop: "4rem", display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: "0.65rem", maxWidth: 640, width: "100%" }}
      >
        {METRICS.map((m, i) => (
          <motion.div key={m.label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 + i * 0.07 }}
            style={{ padding: "1.1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, textAlign: "center", position: "relative", overflow: "hidden" }}
          >
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${m.color}, transparent)` }} />
            <div style={{ fontSize: "1.7rem", fontWeight: 800, color: m.color, letterSpacing: "-0.03em" }}>{m.value}</div>
            <div style={{ fontSize: "0.65rem", color: theme.text.muted, textTransform: "uppercase", letterSpacing: "0.06em", marginTop: "0.2rem" }}>{m.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Scroll hint */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }}
        style={{ position: "absolute", bottom: "2rem", left: "50%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.3rem", color: theme.text.muted, fontSize: "0.65rem" }}
      >
        <span>Scroll to explore</span>
        <motion.div animate={{ y: [0, 6, 0] }} transition={{ repeat: Infinity, duration: 1.8 }}><ChevronDown size={16} /></motion.div>
      </motion.div>
    </section>
  );
}
