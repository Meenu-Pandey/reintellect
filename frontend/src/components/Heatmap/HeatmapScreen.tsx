import { useEffect, useRef, useState } from "react";
import { theme } from "../../styles/theme";
import { useHeatmap } from "../../api/hooks/useHeatmap";

interface Props { storeId: string; }
type TW = "1h" | "4h" | "today";

const ZONES = [
  { label: "Entry", x: 0.03, y: 0.30, w: 0.14, h: 0.40, color: "#10b981" },
  { label: "Maybelline", x: 0.20, y: 0.03, w: 0.28, h: 0.42, color: "#a855f7" },
  { label: "Lakme", x: 0.52, y: 0.03, w: 0.28, h: 0.42, color: "#ec4899" },
  { label: "Checkout", x: 0.58, y: 0.48, w: 0.22, h: 0.20, color: "#f59e0b" },
  { label: "Skincare", x: 0.20, y: 0.55, w: 0.56, h: 0.40, color: "#06b6d4" },
  { label: "Exit", x: 0.84, y: 0.30, w: 0.14, h: 0.40, color: "#ef4444" },
];

function getWindow(tw: TW) {
  const now = new Date();
  const ms = { "1h": 3600000, "4h": 14400000, today: now.getHours() * 3600000 + now.getMinutes() * 60000 };
  return { start: new Date(now.getTime() - ms[tw]).toISOString(), end: now.toISOString() };
}

function densityColor(d: number): string {
  if (d <= 0) return "rgba(0,0,0,0)";
  const r = Math.min(255, Math.round(120 + d * 135));
  const g = Math.round(40 * (1 - d));
  const b = Math.round(200 * (1 - d * 0.6));
  return `rgba(${r},${g},${b},${d * 0.7})`;
}

export function HeatmapScreen({ storeId }: Props) {
  const [tw, setTw] = useState<TW>("today");
  const [res, setRes] = useState<"low" | "medium" | "high">("medium");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { data } = useHeatmap(storeId, getWindow(tw));
  const W = 560, H = 340;

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, W, H);
    for (const c of data.grid) {
      if (c.density <= 0) continue;
      ctx.fillStyle = densityColor(c.density);
      ctx.fillRect(c.x * W, c.y * H, c.width * W, c.height * H);
    }
  }, [data]);

  return (
    <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.25rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <div><div style={{ fontSize: "0.9rem", fontWeight: 600 }}>Store Floor Heatmap</div><div style={{ fontSize: "0.72rem", color: theme.text.muted }}>Visitor density overlay</div></div>
        <div style={{ display: "flex", gap: "0.25rem" }}>
          {(["1h", "4h", "today"] as TW[]).map(t => (
            <button key={t} onClick={() => setTw(t)} style={{ padding: "0.35rem 0.65rem", border: "none", borderRadius: theme.radiusXs, background: tw === t ? theme.accent.purple : theme.bg.elevated, color: tw === t ? "#fff" : theme.text.muted, fontSize: "0.75rem", fontWeight: 500, cursor: "pointer" }}>{t === "today" ? "Today" : `${t}`}</button>
          ))}
          <select value={res} onChange={e => setRes(e.target.value as "low"|"medium"|"high")} aria-label="Resolution" style={{ padding: "0.35rem", background: theme.bg.elevated, border: `1px solid ${theme.border}`, borderRadius: theme.radiusXs, color: theme.text.muted, fontSize: "0.75rem" }}>
            <option value="low">10×10</option><option value="medium">20×20</option><option value="high">40×40</option>
          </select>
        </div>
      </div>

      <div style={{ position: "relative", width: "100%", maxWidth: W, aspectRatio: `${W}/${H}`, background: theme.bg.primary, borderRadius: theme.radiusXs, overflow: "hidden", border: `1px solid ${theme.border}` }}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 2, pointerEvents: "none" }}>
          {ZONES.map(z => (
            <g key={z.label}>
              <rect x={z.x * W} y={z.y * H} width={z.w * W} height={z.h * H} fill="none" stroke={z.color} strokeWidth={1} strokeDasharray="3 2" opacity={0.6} />
              <text x={(z.x + z.w / 2) * W} y={(z.y + z.h / 2) * H} textAnchor="middle" dominantBaseline="middle" fill={z.color} fontSize={10} fontWeight={600} opacity={0.8}>{z.label}</text>
            </g>
          ))}
        </svg>
        <canvas ref={canvasRef} width={W} height={H} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 1 }} />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "0.6rem" }}>
        <span style={{ fontSize: "0.72rem", color: theme.text.muted }}>Cold</span>
        <div style={{ flex: 1, maxWidth: 150, height: 6, borderRadius: 3, background: `linear-gradient(90deg, rgba(120,40,200,0.1), rgba(200,40,150,0.5), rgba(255,50,50,0.8))` }} />
        <span style={{ fontSize: "0.72rem", color: theme.text.muted }}>Hot</span>
        {data && <span style={{ fontSize: "0.7rem", color: theme.text.muted, marginLeft: "auto" }}>{data.grid.filter(c => c.density > 0).length} active cells</span>}
      </div>
    </div>
  );
}
