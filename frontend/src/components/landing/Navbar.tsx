import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Zap } from "lucide-react";
import { theme } from "../../styles/theme";

export function Navbar() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        padding: "0.75rem clamp(1rem, 3vw, 2rem)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: scrolled ? "rgba(9,9,11,0.85)" : "transparent",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        borderBottom: scrolled ? `1px solid ${theme.border}` : "1px solid transparent",
        transition: "all 0.3s ease",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <Zap size={18} color={theme.accent.purple} />
        <span style={{ fontWeight: 700, fontSize: "0.95rem", letterSpacing: "-0.02em" }}>
          ReIntellect
        </span>
        <span className="hide-mobile" style={{ fontSize: "0.65rem", color: theme.text.muted, marginLeft: "0.3rem" }}>
          AI Retail Intelligence
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "clamp(0.75rem, 2vw, 1.5rem)" }}>
        <span className="hide-mobile"><NavLink href="#features">Features</NavLink></span>
        <span className="hide-mobile"><NavLink href="#architecture">Architecture</NavLink></span>
        <span className="hide-mobile"><NavLink href="#technology">Technology</NavLink></span>
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            padding: "0.45rem 1rem",
            background: theme.accent.purple,
            color: "#fff",
            border: "none",
            borderRadius: theme.radiusXs,
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Live Demo
        </button>
      </div>
    </nav>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      style={{ fontSize: "0.8rem", color: theme.text.secondary, textDecoration: "none" }}
      onMouseEnter={(e) => (e.currentTarget.style.color = theme.text.primary)}
      onMouseLeave={(e) => (e.currentTarget.style.color = theme.text.secondary)}
    >
      {children}
    </a>
  );
}
