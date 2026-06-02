import { Zap } from "lucide-react";
import { theme } from "../../styles/theme";

export function Footer() {
  return (
    <footer style={{ padding: "3rem 2rem", borderTop: `1px solid ${theme.border}` }}>
      <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <Zap size={14} color={theme.accent.purple} />
          <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>ReIntellect</span>
          <span style={{ fontSize: "0.6rem", color: theme.text.muted, marginLeft: "0.5rem" }}>Built for Purplle Tech Challenge 2026</span>
        </div>
        <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.68rem", color: theme.text.muted }}>
          <span>YOLOv8 · ByteTrack · FastAPI · React · WebSocket · SQLite</span>
        </div>
      </div>
    </footer>
  );
}
