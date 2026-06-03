import { motion } from "framer-motion";
import { Users, TrendingUp, Clock, Layers } from "lucide-react";
import { theme } from "../../styles/theme";
import { useWebSocketStore } from "../../store/websocket";
import { useMetrics } from "../../api/hooks/useMetrics";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

interface Props { storeId: string; }

const HOURLY = [
  { h: "10", v: 12 }, { h: "11", v: 15 }, { h: "12", v: 22 }, { h: "13", v: 30 },
  { h: "14", v: 18 }, { h: "15", v: 14 }, { h: "16", v: 20 }, { h: "17", v: 35 },
  { h: "18", v: 25 }, { h: "19", v: 15 },
];

export function OverviewScreen({ storeId }: Props) {
  const visitorCount = useWebSocketStore(s => s.visitorCount);
  const queueDepth = useWebSocketStore(s => s.queueDepth);
  const { data: m } = useMetrics(storeId);

  const kpis = [
    { Icon: Users, label: "Visitors Today", value: m?.unique_visitors ?? visitorCount, suffix: "", color: theme.accent.blue, trend: "+12%", up: true },
    { Icon: TrendingUp, label: "Conversion Rate", value: (m?.conversion_rate ?? 0).toFixed(1), suffix: "%", color: theme.accent.green, trend: "+3.2%", up: true },
    { Icon: Clock, label: "Avg Dwell", value: Math.round(m?.avg_visit_duration_seconds ?? 0), suffix: "s", color: theme.accent.purpleMid, trend: "−5s", up: false },
    { Icon: Layers, label: "Queue Depth", value: m?.queue_depth ?? queueDepth, suffix: "", color: theme.accent.amber, trend: "normal", up: null },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* KPI row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: "0.65rem" }}>
        {kpis.map((k, i) => (
          <motion.div key={k.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            whileHover={{ boxShadow: `0 0 24px ${k.color}20` }}
            style={{ padding: "1.1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, position: "relative", overflow: "hidden", transition: "box-shadow 0.2s", cursor: "default" }}
          >
            {/* Gradient top border */}
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${k.color}, transparent)` }} />
            <k.Icon size={14} color={k.color} style={{ marginBottom: "0.65rem" }} />
            <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
              <span style={{ fontSize: "1.7rem", fontWeight: 800, color: k.color, letterSpacing: "-0.04em" }}>{k.value}</span>
              <span style={{ fontSize: "0.8rem", color: theme.text.muted }}>{k.suffix}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "0.3rem" }}>
              <span style={{ fontSize: "0.65rem", color: theme.text.muted }}>{k.label}</span>
              <span style={{ fontSize: "0.62rem", fontWeight: 600, color: k.up === true ? theme.accent.green : k.up === false ? theme.accent.red : theme.text.muted }}>
                {k.trend}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Store Map */}
      <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, padding: "1rem", position: "relative" }}>
        <div style={{ fontSize: "0.78rem", color: theme.text.secondary, fontWeight: 500, marginBottom: "0.6rem" }}>Store Intelligence Map</div>
        <div style={{ aspectRatio: "2.4/1", background: theme.bg.primary, borderRadius: theme.radiusXs, overflow: "hidden", border: `1px solid ${theme.border}`, position: "relative" }}>
          <img src="/store-layout.png" alt="Store Layout" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.3 }} />
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
            {[{ l: "Gondola A", x: 20, y: 5, w: 28, h: 42, c: "#8b5cf6" }, { l: "Gondola B", x: 52, y: 5, w: 26, h: 42, c: "#ec4899" }, { l: "Cash", x: 60, y: 48, w: 22, h: 20, c: "#f59e0b" }, { l: "Wall", x: 20, y: 58, w: 60, h: 38, c: "#06b6d4" }, { l: "In", x: 3, y: 30, w: 10, h: 40, c: "#10b981" }].map(z => (
              <g key={z.l}>
                <rect x={z.x} y={z.y} width={z.w} height={z.h} fill={`${z.c}0d`} stroke={z.c} strokeWidth={0.3} rx={1} />
                <text x={z.x + z.w / 2} y={z.y + z.h / 2} textAnchor="middle" dominantBaseline="middle" fill={z.c} fontSize={2.8} fontWeight={600}>{z.l}</text>
              </g>
            ))}
            <motion.circle r={0.9} fill="#fff" animate={{ cx: [8, 34, 65, 71, 44, 91], cy: [50, 22, 22, 58, 77, 50], opacity: [0, 1, 1, 1, 1, 0] }} transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }} />
            <motion.circle r={0.8} fill={theme.accent.purpleLight} animate={{ cx: [8, 34, 91], cy: [50, 77, 50], opacity: [0, 1, 0] }} transition={{ duration: 5, repeat: Infinity, delay: 2, ease: "easeInOut" }} />
          </svg>
        </div>
      </div>

      {/* Hourly traffic */}
      <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, padding: "0.9rem 1rem" }}>
        <div style={{ fontSize: "0.75rem", color: theme.text.secondary, marginBottom: "0.35rem", fontWeight: 500 }}>Hourly Visitor Traffic</div>
        <ResponsiveContainer width="100%" height={90}>
          <AreaChart data={HOURLY} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={theme.accent.purple} stopOpacity={0.35} />
                <stop offset="95%" stopColor={theme.accent.purple} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="v" stroke={theme.accent.purple} fill="url(#grad)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
