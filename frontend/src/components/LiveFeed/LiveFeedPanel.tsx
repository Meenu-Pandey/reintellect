import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radio } from "lucide-react";
import { theme, EVENT_COLORS } from "../../styles/theme";
import { useWebSocketStore } from "../../store/websocket";
import type { Event } from "../../types/events";

const TYPE_LABEL: Record<string, string> = {
  ENTRY: "Entry", EXIT: "Exit", ZONE_ENTER: "Zone In", ZONE_EXIT: "Zone Out",
  ZONE_DWELL: "Dwell", BILLING_QUEUE_JOIN: "Queue", BILLING_QUEUE_ABANDON: "Abandon", REENTRY: "Re-entry",
};

export function LiveFeedPanel() {
  const events = useWebSocketStore(s => s.liveEvents);
  const [, tick] = useState(0);
  useEffect(() => { const i = setInterval(() => tick(t => t + 1), 1000); return () => clearInterval(i); }, []);

  return (
    <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, display: "flex", flexDirection: "column", height: "100%", maxHeight: "calc(100vh - 150px)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem 0.9rem", borderBottom: `1px solid ${theme.border}`, flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
          <motion.div animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 1.5, repeat: Infinity }}>
            <Radio size={12} color={theme.accent.green} />
          </motion.div>
          <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Live Activity</span>
        </div>
        <span style={{ fontSize: "0.65rem", color: theme.text.muted, background: theme.bg.elevated, padding: "0.12rem 0.4rem", borderRadius: 4 }}>{events.length}</span>
      </div>

      {/* Event list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.35rem" }}>
        {events.length === 0 && (
          <div style={{ padding: "2rem 1rem", textAlign: "center", color: theme.text.muted, fontSize: "0.8rem" }}>
            Waiting for events...
          </div>
        )}
        <AnimatePresence initial={false}>
          {events.map((e, i) => (
            <motion.div key={e.event_id} initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
              <EventRow event={e} isNew={i === 0} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

function EventRow({ event, isNew }: { event: Event; isNew: boolean }) {
  const color = EVENT_COLORS[event.event_type] || theme.text.muted;
  const diff = Date.now() - new Date(event.timestamp).getTime();
  const rel = diff < 60000 ? `${Math.floor(diff / 1000)}s` : diff < 3600000 ? `${Math.floor(diff / 60000)}m` : `${Math.floor(diff / 3600000)}h`;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", padding: "0.38rem 0.5rem", borderRadius: theme.radiusXs, marginBottom: "0.15rem", background: isNew ? theme.bg.elevated : "transparent" }}>
      {/* Pulsing dot */}
      <div style={{ position: "relative", flexShrink: 0, width: 8, height: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
        {isNew && <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: color, animation: "ping 1s ease-out" }} />}
      </div>

      {/* Badge */}
      <span style={{ fontSize: "0.62rem", fontWeight: 600, color, background: `${color}14`, padding: "0.1rem 0.35rem", borderRadius: 3, minWidth: 52, textAlign: "center", flexShrink: 0 }}>
        {TYPE_LABEL[event.event_type] || event.event_type}
      </span>

      {/* Visitor */}
      <span style={{ fontSize: "0.65rem", color: theme.text.muted, fontFamily: theme.fontMono, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
        {event.visitor_id.slice(0, 8)}
      </span>

      {/* Time */}
      <span style={{ fontSize: "0.6rem", color: theme.text.muted, flexShrink: 0 }}>{rel}</span>
    </div>
  );
}
