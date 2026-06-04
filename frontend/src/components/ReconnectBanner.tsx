import { theme } from "../styles/theme";
import { useWebSocketStore } from "../store/websocket";

export function ReconnectBanner() {
  const connectionStatus = useWebSocketStore(s => s.connectionStatus);
  const connect = useWebSocketStore(s => s.connect);

  if (connectionStatus === "connected") return null;
  const isReconnecting = connectionStatus === "reconnecting";

  return (
    <div role="alert" style={{ padding: "0.4rem 1.25rem", background: isReconnecting ? "rgba(245,158,11,0.08)" : "rgba(239,68,68,0.08)", borderBottom: `1px solid ${isReconnecting ? "rgba(245,158,11,0.2)" : "rgba(239,68,68,0.2)"}`, display: "flex", alignItems: "center", gap: "0.65rem", fontSize: "0.78rem" }}>
      <div style={{ width: 7, height: 7, borderRadius: "50%", background: isReconnecting ? theme.accent.amber : theme.accent.red, animation: "pulse 1s infinite" }} />
      {isReconnecting && <span style={{ color: theme.accent.amber }}>Reconnecting to live feed...</span>}
      {connectionStatus === "failed" && (
        <>
          <span style={{ color: theme.accent.red }}>Connection lost.</span>
          <button onClick={() => { const s = document.querySelector<HTMLSelectElement>('select[aria-label="Select store"]'); if (s?.value) connect(s.value); }} style={{ marginLeft: "auto", padding: "0.25rem 0.65rem", borderRadius: theme.radiusXs, border: `1px solid ${theme.accent.red}`, background: "transparent", color: theme.accent.red, cursor: "pointer", fontSize: "0.72rem", fontWeight: 600 }}>Retry</button>
        </>
      )}
    </div>
  );
}
