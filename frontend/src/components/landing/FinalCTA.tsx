import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { theme } from "../../styles/theme";

export function FinalCTA() {
  const navigate = useNavigate();
  return (
    <section style={{ padding: "8rem clamp(1rem,4vw,3rem)", position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: 700, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)", filter: "blur(70px)", pointerEvents: "none" }} />
      <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }} style={{ textAlign: "center", position: "relative", zIndex: 1 }}>
        <h2 style={{ fontSize: "clamp(2rem,4vw,3rem)", fontWeight: 800, letterSpacing: "-0.04em", marginBottom: "1rem", fontFamily: "'Space Grotesk',sans-serif" }}>
          Ready to See Your Store <span style={{ color: theme.accent.purpleMid }}>Think</span>?
        </h2>
        <p style={{ fontSize: "0.95rem", color: theme.text.secondary, marginBottom: "2.5rem" }}>Live retail intelligence. Real store data. Zero setup required.</p>
        <button onClick={() => navigate("/dashboard")} style={{ display: "inline-flex", alignItems: "center", gap: "0.6rem", padding: "0.9rem 2.2rem", background: "linear-gradient(135deg,#7c3aed,#6d28d9)", color: "#fff", border: "none", borderRadius: theme.radiusSm, fontSize: "0.92rem", fontWeight: 600, cursor: "pointer", boxShadow: "0 0 40px rgba(124,58,237,0.4)", transition: "box-shadow 0.2s" }}
          onMouseEnter={e => (e.currentTarget.style.boxShadow = "0 0 60px rgba(124,58,237,0.6)")}
          onMouseLeave={e => (e.currentTarget.style.boxShadow = "0 0 40px rgba(124,58,237,0.4)")}
        >Launch Live Dashboard <ArrowRight size={18} /></button>
      </motion.div>
    </section>
  );
}
