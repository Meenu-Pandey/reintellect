import { useEffect, useState } from "react";
import { Radio } from "lucide-react";
import { theme, EVENT_COLORS } from "../../styles/theme";
import { useWebSocketStore } from "../../store/websocket";
import type { Event } from "../../types/events";

const TYPE_SHORT: Record<string, string> = {
  ENTRY: "ENTRY", EXIT: "EXIT", ZONE_ENTER: "ZONE IN", ZONE_EXIT: "ZONE OUT",
  ZONE_DWELL: "DWELL", BILLING_QUEUE_JOIN: "QUEUE", BILLING_QUEUE_ABANDON: "ABANDON", REENTRY: "RE-ENTRY",
};

export function LiveFeedPanel() {
  const events = useWebSocketStore(s => s.liveEvents);
  const [, tick] = useState(0);
  useEffect(() => { const i = setInterval(() => tick(t => t + 1), 1000); return () => clearInterval(i); }, []);

  return (
    <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 0.85rem", borderBottom: `1px solid ${theme.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <Radio size={13} color={theme.accent.green} />
          <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Live Feed</span>
        </div>
        <span style={{ fontSize: "0.72rem", color: theme.text.muted, background: theme.bg.elevated, padding: "0.1rem 0.4rem", borderRadius: 4 }}>{events.length}</span>
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "0.4rem" }}>
        {events.length === 0 && <div style={{ padding: "1.5rem", textAlign: "center", fontSize: "0.82rem", color: theme.text.muted }}>Waiting for events...</div>}
        {events.map((e, i) => <Row key={e.event_id} event={e} isNew={i === 0} />)}
      </div>
    </div>
  );
}

function Row({ event, isNew }: { event: Event; isNew: boolean }) {
  const color = EVENT_COLORS[event.event_type] || theme.text.muted;
  const diff = Date.now() - new Date(event.timestamp).getTime();
  const rel = diff < 60000 ? `${Math.floor(diff / 1000)}s` : diff < 3600000 ? `${Math.floor(diff / 60000)}m` : `${Math.floor(diff / 3600000)}h`;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.4rem 0.5rem", borderRadius: theme.radiusXs, marginBottom: "0.15rem", background: isNew ? theme.bg.elevated : "transparent", animation: isNew ? "fadeSlideIn 0.25s ease" : undefined }}>
      <div style={{ width: 6, height: 6, borderRadius: "50%", background: color, flexShrink: 0 }} />
      <span style={{ fontSize: "0.7rem", fontWeight: 600, color, background: `${color}12`, padding: "0.1rem 0.35rem", borderRadius: 3, minWidth: 52, textAlign: "center" }}>{TYPE_SHORT[event.event_type] || event.event_type}</span>
      <span style={{ fontSize: "0.72rem", color: theme.text.muted, fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{event.visitor_id.slice(0, 8)}</span>
      <span style={{ fontSize: "0.68rem", color: theme.text.muted, marginLeft: "auto" }}>{rel}</span>
    </div>
  );
}
