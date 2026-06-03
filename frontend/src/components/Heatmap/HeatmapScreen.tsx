/**
 * Heatmap screen — Real store layout image with canvas density overlay.
 * The actual Brigade Road store PNG is used as the base layer.
 */

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { theme } from "../../styles/theme";
import { useHeatmap } from "../../api/hooks/useHeatmap";

interface Props { storeId: string; }
type TW = "1h" | "4h" | "today";

const ZONES = [
  { label: "Entrance", x: 0.03, y: 0.30, w: 0.10, h: 0.40, color: "#10b981" },
  { label: "Gondola A", x: 0.20, y: 0.05, w: 0.28, h: 0.42, color: "#8b5cf6" },
  { label: "Gondola B", x: 0.52, y: 0.05, w: 0.26, h: 0.42, color: "#ec4899" },
  { label: "Cash Counter", x: 0.60, y: 0.48, w: 0.22, h: 0.20, color: "#f59e0b" },
  { label: "Wall Displays", x: 0.20, y: 0.58, w: 0.60, h: 0.38, color: "#06b6d4" },
  { label: "Exit", x: 0.84, y: 0.30, w: 0.14, h: 0.40, color: "#ef4444" },
];

function getWindow(tw: TW) {
  const now = new Date();
  const ms = { "1h": 3600000, "4h": 14400000, today: now.getHours() * 3600000 + now.getMinutes() * 60000 };
  return { start: new Date(now.getTime() - ms[tw]).toISOString(), end: now.toISOString() };
}

function densityColor(d: number): string {
  if (d <= 0) return "rgba(0,0,0,0)";
  const r = Math.min(255, Math.round(80 + d * 175));
  const g = Math.round(30 * (1 - d));
  const b = Math.round(220 * (1 - d * 0.65));
  return `rgba(${r},${g},${b},${d * 0.72})`;
}

export function HeatmapScreen({ storeId }: Props) {
  const [tw, setTw] = useState<TW>("today");
  const [res, setRes] = useState<"low" | "medium" | "high">("medium");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [imgLoaded, setImgLoaded] = useState(false);
  const { data, isLoading } = useHeatmap(storeId, getWindow(tw));
  const W = 620, H = 400;

  // Preload store layout image
  useEffect(() => {
    const img = new Image();
    img.src = "/store-layout.png";
    img.onload = () => { imgRef.current = img; setImgLoaded(true); };
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, W, H);

    // Draw store layout as dark-tinted base
    if (imgRef.current) {
      ctx.globalAlpha = 0.35;
      ctx.drawImage(imgRef.current, 0, 0, W, H);
      ctx.globalAlpha = 1;
    }

    // Draw heatmap density overlay
    for (const c of data.grid) {
      if (c.density <= 0) continue;
      ctx.fillStyle = densityColor(c.density);
      ctx.fillRect(c.x * W, c.y * H, c.width * W, c.height * H);
    }
  }, [data, imgLoaded]);

  const buttons: { id: TW; label: string }[] = [
    { id: "1h", label: "Last 1h" },
    { id: "4h", label: "Last 4h" },
    { id: "today", label: "Today" },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
      style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}
    >
      {/* Card */}
      <div style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, padding: "1.25rem" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <div>
            <div style={{ fontSize: "0.92rem", fontWeight: 600, letterSpacing: "-0.01em" }}>Store Floor Heatmap</div>
            <div style={{ fontSize: "0.7rem", color: theme.text.muted, marginTop: "0.15rem" }}>Visitor density — Purplle Brigade Road</div>
          </div>
          <div style={{ display: "flex", gap: "0.3rem", alignItems: "center", flexWrap: "wrap" }}>
            {buttons.map((b) => (
              <button key={b.id} onClick={() => setTw(b.id)} style={{ padding: "0.35rem 0.65rem", border: "none", borderRadius: theme.radiusXs, background: tw === b.id ? theme.accent.purple : theme.bg.elevated, color: tw === b.id ? "#fff" : theme.text.secondary, fontSize: "0.75rem", fontWeight: 500, cursor: "pointer" }}>{b.label}</button>
            ))}
            <select value={res} onChange={e => setRes(e.target.value as "low" | "medium" | "high")} aria-label="Resolution"
              style={{ padding: "0.35rem 0.5rem", background: theme.bg.elevated, border: `1px solid ${theme.border}`, borderRadius: theme.radiusXs, color: theme.text.secondary, fontSize: "0.75rem" }}>
              <option value="low">10×10</option>
              <option value="medium">20×20</option>
              <option value="high">40×40</option>
            </select>
          </div>
        </div>

        {/* Map container */}
        <div style={{ position: "relative", width: "100%", maxWidth: W, aspectRatio: `${W}/${H}`, background: theme.bg.primary, borderRadius: theme.radiusSm, overflow: "hidden", border: `1px solid ${theme.border}` }}>
          {/* Zone SVG labels */}
          <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 2, pointerEvents: "none" }}>
            {ZONES.map(z => (
              <g key={z.label}>
                <rect x={z.x * W} y={z.y * H} width={z.w * W} height={z.h * H}
                  fill="none" stroke={z.color} strokeWidth={1.2} strokeDasharray="4 3" opacity={0.65} rx={4} />
                <text x={(z.x + z.w / 2) * W} y={(z.y + z.h / 2) * H} textAnchor="middle" dominantBaseline="middle"
                  fill={z.color} fontSize={11} fontWeight={600} opacity={0.9}>{z.label}</text>
              </g>
            ))}
          </svg>
          {/* Density canvas */}
          <canvas ref={canvasRef} width={W} height={H} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 1 }} />
          {isLoading && (
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 3, background: "rgba(8,8,16,0.5)", fontSize: "0.8rem", color: theme.text.muted }}>Loading...</div>
          )}
        </div>

        {/* Legend */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem" }}>
          <span style={{ fontSize: "0.7rem", color: theme.text.muted }}>Cold</span>
          <div style={{ flex: 1, maxWidth: 180, height: 6, borderRadius: 3, background: "linear-gradient(90deg, rgba(80,30,220,0.15), rgba(180,40,160,0.5), rgba(255,50,50,0.8))" }} />
          <span style={{ fontSize: "0.7rem", color: theme.text.muted }}>Hot</span>
          {data && <span style={{ fontSize: "0.68rem", color: theme.text.muted, marginLeft: "auto" }}>{data.grid.filter(c => c.density > 0).length} active cells · {data.grid_size}×{data.grid_size}</span>}
        </div>
      </div>

      {/* Zone stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: "0.6rem" }}>
        {ZONES.map((z) => (
          <div key={z.label} style={{ padding: "0.75rem", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radiusSm, borderLeft: `3px solid ${z.color}` }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 600, color: z.color, marginBottom: "0.25rem" }}>{z.label}</div>
            <div style={{ fontSize: "0.62rem", color: theme.text.muted }}>Active zone</div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
