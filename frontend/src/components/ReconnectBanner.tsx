/**
 * WebSocket reconnect indicator — dark themed.
 */

import { theme } from "../styles/theme";
import { useWebSocketStore } from "../store/websocket";

export function ReconnectBanner() {
  const connectionStatus = useWebSocketStore((s) => s.connectionStatus);
  const connect = useWebSocketStore((s) => s.connect);

  if (connectionStatus === "connected") return null;

  const isReconnecting = connectionStatus === "reconnecting";

  return (
    <div
      role="alert"
      style={{
        padding: "0.5rem 1.25rem",
        background: isReconnecting ? "#292524" : "#1c1917",
        borderBottom: `1px solid ${isReconnecting ? theme.accent.amber : theme.accent.red}`,
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        fontSize: "0.78rem",
      }}
    >
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: isReconnecting ? theme.accent.amber : theme.accent.red,
          animation: isReconnecting ? "pulse 1s infinite" : undefined,
        }}
      />

      {isReconnecting && (
        <span style={{ color: theme.accent.amber }}>Reconnecting to live feed...</span>
      )}

      {connectionStatus === "failed" && (
        <>
          <span style={{ color: theme.accent.red }}>Connection lost. Live updates paused.</span>
          <button
            onClick={() => {
              const sel = document.querySelector<HTMLSelectElement>('select[aria-label="Select store"]');
              if (sel?.value) connect(sel.value);
            }}
            style={{
              marginLeft: "auto",
              padding: "0.3rem 0.75rem",
              borderRadius: theme.radiusSm,
              border: `1px solid ${theme.accent.red}`,
              background: "transparent",
              color: theme.accent.red,
              cursor: "pointer",
              fontSize: "0.72rem",
              fontWeight: 600,
            }}
          >
            Retry
          </button>
        </>
      )}
    </div>
  );
}
