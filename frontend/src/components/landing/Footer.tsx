import { Zap, Github } from "lucide-react";
import { theme } from "../../styles/theme";

export function Footer() {
  return (
    <footer style={{ padding: "2.5rem clamp(1rem,4vw,3rem)", borderTop: `1px solid ${theme.border}` }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ width: 22, height: 22, borderRadius: 6, background: "linear-gradient(135deg,#7c3aed,#a78bfa)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Zap size={11} color="#fff" />
          </div>
          <span style={{ fontWeight: 700, fontSize: "0.85rem" }}>ReIntellect</span>
          <span style={{ fontSize: "0.6rem", color: theme.text.muted, marginLeft: "0.5rem" }}>AI-Powered Retail Intelligence Platform</span>
        </div>
        <div style={{ display: "flex", gap: "0.6rem", fontSize: "0.65rem", color: theme.text.muted, flexWrap: "wrap" }}>
          {["YOLOv8", "ByteTrack", "FastAPI", "React", "WebSocket", "SQLite", "Docker"].map(t => (
            <span key={t} style={{ padding: "0.2rem 0.5rem", background: theme.bg.elevated, borderRadius: 4 }}>{t}</span>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <a href="#" style={{ color: theme.text.muted, textDecoration: "none" }}><Github size={16} /></a>
          <span style={{ fontSize: "0.62rem", color: theme.text.muted }}>Built for Purplle Tech Challenge 2026</span>
        </div>
      </div>
    </footer>
  );
}
