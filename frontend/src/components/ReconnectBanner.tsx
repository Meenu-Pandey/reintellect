/**
 * WebSocket reconnect indicator banner.
 *
 * Shows "Reconnecting…" when connectionStatus === "reconnecting".
 * Shows "Connection lost" with Manual Retry button when "failed".
 * Hidden when "connected".
 */

import { useWebSocketStore } from "../store/websocket";

export function ReconnectBanner() {
  const connectionStatus = useWebSocketStore((s) => s.connectionStatus);
  const connect = useWebSocketStore((s) => s.connect);

  if (connectionStatus === "connected") {
    return null;
  }

  const isReconnecting = connectionStatus === "reconnecting";

  return (
    <div
      role="alert"
      style={{
        padding: "0.5rem 1rem",
        marginBottom: "0.75rem",
        borderRadius: "4px",
        background: isReconnecting ? "#fef3c7" : "#fee2e2",
        color: isReconnecting ? "#92400e" : "#991b1b",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        fontSize: "0.85rem",
      }}
    >
      {isReconnecting && (
        <>
          <span aria-hidden>⟳</span>
          <span>Reconnecting…</span>
        </>
      )}

      {connectionStatus === "failed" && (
        <>
          <span aria-hidden>✕</span>
          <span>Connection lost. Live updates paused.</span>
          <button
            onClick={() => {
              // Re-trigger connect — uses the last known store ID internally
              const storeId =
                document.querySelector<HTMLSelectElement>(
                  'select[aria-label="Select store"]'
                )?.value;
              if (storeId) {
                connect(storeId);
              }
            }}
            style={{
              marginLeft: "auto",
              padding: "0.3rem 0.75rem",
              borderRadius: "4px",
              border: "1px solid #991b1b",
              background: "#fff",
              color: "#991b1b",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: 600,
            }}
          >
            Manual Retry
          </button>
        </>
      )}
    </div>
  );
}
