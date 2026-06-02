import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Layers } from "lucide-react";
import { theme } from "../../styles/theme";

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        padding: "8rem 2rem 4rem",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background grid */}
      <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle at 1px 1px, rgba(123,31,162,0.03) 1px, transparent 0)", backgroundSize: "48px 48px", pointerEvents: "none" }} />
      {/* Radial glow */}
      <div style={{ position: "absolute", top: "10%", left: "50%", transform: "translateX(-50%)", width: 700, height: 500, borderRadius: "50%", background: "radial-gradient(ellipse, rgba(123,31,162,0.12) 0%, transparent 70%)", filter: "blur(40px)", pointerEvents: "none" }} />

      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.35rem 0.85rem", background: theme.bg.elevated, border: `1px solid ${theme.border}`, borderRadius: "9999px", marginBottom: "2rem", fontSize: "0.68rem", color: theme.text.secondary }}
      >
        <Layers size={12} color={theme.accent.purple} />
        Built for Purplle Tech Challenge 2026
      </motion.div>

      {/* Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.9, delay: 0.1 }}
        style={{ fontSize: "clamp(2.5rem, 5.5vw, 4.2rem)", fontWeight: 800, lineHeight: 1.05, maxWidth: "820px", letterSpacing: "-0.04em", marginBottom: "1.5rem" }}
      >
        Transform Retail CCTV{" "}
        <br />
        <span style={{ background: "linear-gradient(135deg, #9C27B0, #CE93D8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Into Business Intelligence
        </span>
      </motion.h1>

      {/* Subheadline */}
      <motion.p
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        style={{ fontSize: "1.05rem", color: theme.text.secondary, maxWidth: "540px", lineHeight: 1.65, marginBottom: "2.5rem" }}
      >
        Track visitor journeys, measure dwell time, detect queue abandonment, and uncover store insights — in real time.
      </motion.p>

      {/* Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
        style={{ display: "flex", gap: "0.75rem" }}
      >
        <button
          onClick={() => navigate("/dashboard")}
          style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.7rem 1.5rem", background: theme.accent.purple, color: "#fff", border: "none", borderRadius: theme.radiusXs, fontSize: "0.82rem", fontWeight: 600, cursor: "pointer" }}
        >
          View Live Dashboard <ArrowRight size={14} />
        </button>
        <button
          onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })}
          style={{ padding: "0.7rem 1.5rem", background: "transparent", color: theme.text.secondary, border: `1px solid ${theme.borderLight}`, borderRadius: theme.radiusXs, fontSize: "0.82rem", fontWeight: 500, cursor: "pointer" }}
        >
          Explore Architecture
        </button>
      </motion.div>

      {/* Floating mini dashboard preview */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.7 }}
        style={{ marginTop: "4rem", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "0.6rem", maxWidth: "620px", width: "100%" }}
      >
        <MetricChip label="Visitors" value="143" color={theme.accent.blue} />
        <MetricChip label="Conversion" value="35%" color={theme.accent.green} />
        <MetricChip label="Dwell" value="47s" color={theme.accent.purpleMid} />
        <MetricChip label="Anomalies" value="3" color={theme.accent.amber} />
      </motion.div>
    </section>
  );
}

function MetricChip({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: "1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, textAlign: "center" }}>
      <div style={{ fontSize: "1.4rem", fontWeight: 700, color, marginBottom: "0.25rem" }}>{value}</div>
      <div style={{ fontSize: "0.62rem", color: theme.text.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
    </div>
  );
}
