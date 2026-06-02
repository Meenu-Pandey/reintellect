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

const ZONES = [
  { id: "entry", label: "Entry", x: 3, y: 30, w: 14, h: 40, color: "#10b981" },
  { id: "maybelline", label: "Maybelline", x: 20, y: 3, w: 28, h: 42, color: "#a855f7" },
  { id: "lakme", label: "Lakme", x: 52, y: 3, w: 28, h: 42, color: "#ec4899" },
  { id: "queue", label: "Checkout", x: 58, y: 48, w: 22, h: 20, color: "#f59e0b" },
  { id: "skincare", label: "Skincare", x: 20, y: 55, w: 58, h: 40, color: "#06b6d4" },
  { id: "exit", label: "Exit", x: 84, y: 30, w: 14, h: 40, color: "#ef4444" },
];

export function OverviewScreen({ storeId }: Props) {
  const visitorCount = useWebSocketStore((s) => s.visitorCount);
  const queueDepth = useWebSocketStore((s) => s.queueDepth);
  const { data: metrics } = useMetrics(storeId);

  const kpis = [
    { Icon: Users, label: "Visitors Today", value: metrics?.unique_visitors ?? visitorCount, suffix: "", color: theme.accent.blue },
    { Icon: TrendingUp, label: "Conversion", value: metrics?.conversion_rate ?? 0, suffix: "%", color: theme.accent.green, decimals: 1 },
    { Icon: Clock, label: "Avg Dwell", value: Math.round(metrics?.avg_visit_duration_seconds ?? 0), suffix: "s", color: theme.accent.purpleMid },
    { Icon: Layers, label: "Queue Depth", value: metrics?.queue_depth ?? queueDepth, suffix: "", color: theme.accent.amber },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* KPI Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.6rem" }}>
        {kpis.map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            style={{ padding: "1rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm }}
          >
            <k.Icon size={15} color={k.color} style={{ marginBottom: "0.5rem" }} />
            <div style={{ fontSize: "1.8rem", fontWeight: 700, color: k.color }}>{(k.decimals ? k.value.toFixed(k.decimals) : k.value)}{k.suffix}</div>
            <div style={{ fontSize: "0.75rem", color: theme.text.muted, marginTop: "0.15rem" }}>{k.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Store Map - Centerpiece */}
      <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1rem", position: "relative" }}>
        <div style={{ fontSize: "0.82rem", color: theme.text.secondary, fontWeight: 500, marginBottom: "0.6rem" }}>Store Intelligence Map — Purplle Brigade Road</div>
        <div style={{ aspectRatio: "2.2/1", background: theme.bg.primary, borderRadius: theme.radiusXs, position: "relative", overflow: "hidden", border: `1px solid ${theme.border}` }}>
          <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(123,31,162,0.03) 1px, transparent 1px)", backgroundSize: "20px 20px" }} />
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
            {ZONES.map((z) => (
              <g key={z.id}>
                <rect x={z.x} y={z.y} width={z.w} height={z.h} fill={`${z.color}0d`} stroke={z.color} strokeWidth={0.35} rx={1} />
                <text x={z.x + z.w / 2} y={z.y + z.h / 2} textAnchor="middle" dominantBaseline="middle" fill={z.color} fontSize={2.6} fontWeight={600}>{z.label}</text>
              </g>
            ))}
            <motion.circle r={0.9} fill="#fff" animate={{ cx: [10, 34, 66, 69, 45, 91], cy: [50, 22, 22, 58, 75, 50], opacity: [0, 1, 1, 1, 1, 0] }} transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }} />
            <motion.circle r={0.9} fill={theme.accent.purpleLight} animate={{ cx: [10, 34, 91], cy: [50, 75, 50], opacity: [0, 1, 0] }} transition={{ duration: 4, repeat: Infinity, delay: 2, ease: "easeInOut" }} />
          </svg>
        </div>
      </div>

      {/* Hourly Traffic */}
      <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, padding: "0.85rem 1rem" }}>
        <div style={{ fontSize: "0.8rem", color: theme.text.secondary, marginBottom: "0.4rem" }}>Hourly Traffic</div>
        <ResponsiveContainer width="100%" height={80}>
          <AreaChart data={HOURLY} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
            <defs><linearGradient id="pg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={theme.accent.purple} stopOpacity={0.3} /><stop offset="95%" stopColor={theme.accent.purple} stopOpacity={0} /></linearGradient></defs>
            <Area type="monotone" dataKey="v" stroke={theme.accent.purple} fill="url(#pg)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
