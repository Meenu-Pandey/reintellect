import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap, Github, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";
import { theme } from "../../styles/theme";

export function Navbar() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const scroll = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <motion.nav
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 200,
        padding: "0 clamp(1rem, 4vw, 3rem)",
        height: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: scrolled ? "rgba(8,8,16,0.85)" : "transparent",
        backdropFilter: scrolled ? "blur(20px)" : "none",
        WebkitBackdropFilter: scrolled ? "blur(20px)" : "none",
        borderBottom: scrolled ? `1px solid ${theme.border}` : "1px solid transparent",
        transition: "all 0.4s ease",
      }}
    >
      {/* Logo */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "none", border: "none", cursor: "pointer" }}
      >
        <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg,#7c3aed,#a78bfa)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Zap size={14} color="#fff" />
        </div>
        <span style={{ fontWeight: 700, fontSize: "0.95rem", color: theme.text.primary, letterSpacing: "-0.02em" }}>ReIntellect</span>
      </button>

      {/* Center nav */}
      <div className="hide-mobile" style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
        {[["product","Features"],["architecture","Architecture"],["technology","Technology"]].map(([id, label]) => (
          <button key={id} onClick={() => scroll(id)} style={{ padding: "0.4rem 0.75rem", background: "none", border: "none", cursor: "pointer", fontSize: "0.82rem", color: theme.text.secondary, borderRadius: theme.radiusXs, transition: "color 0.15s" }}
            onMouseEnter={e => (e.currentTarget.style.color = theme.text.primary)}
            onMouseLeave={e => (e.currentTarget.style.color = theme.text.secondary)}
          >{label}</button>
        ))}
        <button onClick={() => navigate("/dashboard")} style={{ padding: "0.4rem 0.75rem", background: "none", border: "none", cursor: "pointer", fontSize: "0.82rem", color: theme.text.secondary, borderRadius: theme.radiusXs, transition: "color 0.15s" }}
          onMouseEnter={e => (e.currentTarget.style.color = theme.text.primary)}
          onMouseLeave={e => (e.currentTarget.style.color = theme.text.secondary)}
        >Dashboard</button>
        <a href="#" style={{ padding: "0.4rem 0.75rem", display: "flex", alignItems: "center", gap: "0.3rem", textDecoration: "none", fontSize: "0.82rem", color: theme.text.secondary, borderRadius: theme.radiusXs }}
          onMouseEnter={e => (e.currentTarget.style.color = theme.text.primary)}
          onMouseLeave={e => (e.currentTarget.style.color = theme.text.secondary)}
        ><Github size={14} /></a>
      </div>

      {/* CTA */}
      <button
        onClick={() => navigate("/dashboard")}
        style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem 1.1rem", background: "linear-gradient(135deg,#7c3aed,#6d28d9)", color: "#fff", border: "none", borderRadius: theme.radiusXs, fontSize: "0.8rem", fontWeight: 600, cursor: "pointer", transition: "opacity 0.15s" }}
        onMouseEnter={e => (e.currentTarget.style.opacity = "0.85")}
        onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
      >
        Launch Demo <ExternalLink size={12} />
      </button>
    </motion.nav>
  );
}
