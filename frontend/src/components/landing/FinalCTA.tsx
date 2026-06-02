import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { theme } from "../../styles/theme";

export function FinalCTA() {
  const navigate = useNavigate();

  return (
    <section style={{ padding: "6rem 2rem", position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 600, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(123,31,162,0.1) 0%, transparent 70%)", filter: "blur(60px)", pointerEvents: "none" }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: "center", position: "relative", zIndex: 1 }}
      >
        <h2 style={{ fontSize: "2.2rem", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: "1rem" }}>
          Ready to See Your Store <span style={{ color: theme.accent.purpleMid }}>Think</span>?
        </h2>
        <p style={{ fontSize: "0.9rem", color: theme.text.secondary, marginBottom: "2rem" }}>
          Explore the live retail intelligence dashboard with real demo data.
        </p>
        <button
          onClick={() => navigate("/dashboard")}
          style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.85rem 2rem", background: theme.accent.purple, color: "#fff", border: "none", borderRadius: theme.radiusXs, fontSize: "0.88rem", fontWeight: 600, cursor: "pointer" }}
        >
          Launch Live Dashboard <ArrowRight size={16} />
        </button>
      </motion.div>
    </section>
  );
}
