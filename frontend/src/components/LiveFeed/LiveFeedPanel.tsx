/**
 * Live Event Feed panel.
 *
 * Renders last 20 events from Zustand liveEvents in reverse chronological order.
 * Each row: event type badge, visitor ID (truncated), timestamp (relative).
 * Updates within 500ms of WS event receipt (driven by Zustand).
 */

import { useEffect, useState } from "react";
import { useWebSocketStore } from "../../store/websocket";
import type { Event } from "../../types/events";

export function LiveFeedPanel() {
  const liveEvents = useWebSocketStore((s) => s.liveEvents);
  const [, setTick] = useState(0);

  // Force re-render every second to update relative timestamps
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        border: "1px solid #e0e0e0",
        borderRadius: "8px",
        padding: "0.75rem",
        maxHeight: "500px",
        overflowY: "auto",
      }}
    >
      <h3 style={{ margin: "0 0 0.75rem 0", fontSize: "0.9rem" }}>
        Live Events ({liveEvents.length})
      </h3>

      {liveEvents.length === 0 && (
        <p style={{ color: "#999", fontSize: "0.8rem" }}>
          No events yet. Waiting for data...
        </p>
      )}

      {liveEvents.map((event) => (
        <EventRow key={event.event_id} event={event} />
      ))}
    </div>
  );
}

function EventRow({ event }: { event: Event }) {
  const relTime = getRelativeTime(event.timestamp);
  const visitorShort = event.visitor_id.slice(0, 8);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.4rem 0",
        borderBottom: "1px solid #f0f0f0",
        fontSize: "0.8rem",
      }}
    >
      <EventBadge type={event.event_type} />
      <span style={{ color: "#555", fontFamily: "monospace" }}>
        {visitorShort}
      </span>
      <span style={{ marginLeft: "auto", color: "#999", fontSize: "0.75rem" }}>
        {relTime}
      </span>
    </div>
  );
}

function EventBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    ENTRY: "#22c55e",
    EXIT: "#ef4444",
    ZONE_ENTER: "#3b82f6",
    ZONE_EXIT: "#93c5fd",
    ZONE_DWELL: "#8b5cf6",
    BILLING_QUEUE_JOIN: "#f59e0b",
    BILLING_QUEUE_ABANDON: "#dc2626",
    REENTRY: "#06b6d4",
  };

  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.15rem 0.4rem",
        borderRadius: "3px",
        fontSize: "0.65rem",
        fontWeight: 600,
        color: "#fff",
        background: colors[type] || "#6b7280",
        whiteSpace: "nowrap",
      }}
    >
      {type}
    </span>
  );
}

function getRelativeTime(isoTimestamp: string): string {
  const now = Date.now();
  const then = new Date(isoTimestamp).getTime();
  const diffMs = now - then;

  if (diffMs < 0) return "just now";

  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}
