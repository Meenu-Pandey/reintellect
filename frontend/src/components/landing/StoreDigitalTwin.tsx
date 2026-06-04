import { useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { theme } from "../../styles/theme";

// Zone definitions mapped to the actual store layout (approximate normalised positions)
const ZONES = [
  { id: "entrance", label: "Entrance", x: 2, y: 40, w: 10, h: 20, color: "#10b981", visitors: 4, dwell: "12s", engagement: "High", anomalies: 0 },
  { id: "gondola-a", label: "Gondola A", x: 20, y: 10, w: 22, h: 35, color: "#8b5cf6", visitors: 6, dwell: "48s", engagement: "Very High", anomalies: 1 },
  { id: "gondola-b", label: "Gondola B", x: 55, y: 10, w: 22, h: 35, color: "#ec4899", visitors: 5, dwell: "42s", engagement: "High", anomalies: 0 },
  { id: "wall-display", label: "Wall Displays", x: 20, y: 55, w: 57, h: 18, color: "#06b6d4", visitors: 3, dwell: "28s", engagement: "Medium", anomalies: 0 },
  { id: "cash-counter", label: "Cash Counter", x: 80, y: 30, w: 17, h: 22, color: "#f59e0b", visitors: 2, dwell: "95s", engagement: "Queue", anomalies: 1 },
  { id: "foh", label: "FOH", x: 20, y: 78, w: 25, h: 18, color: "#3b82f6", visitors: 1, dwell: "20s", engagement: "Low", anomalies: 0 },
  { id: "boh", label: "BOH", x: 55, y: 78, w: 22, h: 18, color: "#6b7280", visitors: 0, dwell: "—", engagement: "Staff Only", anomalies: 0 },
];

export function StoreDigitalTwin() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const [tooltip, setTooltip] = useState<{ zone: typeof ZONES[0]; x: number; y: number } | null>(null);

  return (
    <section ref={ref} style={{ padding: "6rem clamp(1rem,4vw,3rem)" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purpleLight, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Store Digital Twin</div>
        <h2 style={{ fontSize: "clamp(1.8rem,3vw,2.4rem)", fontWeight: 700, letterSpacing: "-0.03em", fontFamily: "'Space Grotesk',sans-serif" }}>Your Store, Brought to Life</h2>
        <p style={{ fontSize: "0.95rem", color: theme.text.secondary, maxWidth: 480, margin: "0.75rem auto 0" }}>
          Real-time visitor tracking overlaid on the actual Brigade Road store layout.
        </p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 30 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.8, delay: 0.2 }}
        style={{ maxWidth: 860, margin: "0 auto", position: "relative" }}
        onMouseLeave={() => setTooltip(null)}
      >
        <div style={{ position: "relative", borderRadius: theme.radius, overflow: "hidden", border: `1px solid ${theme.border}`, background: theme.bg.card }}>
          {/* Real store layout image */}
          <img src="/store-layout.png" alt="Purplle Brigade Road Store Layout" style={{ width: "100%", display: "block", opacity: 0.45, filter: "contrast(1.1) brightness(0.8)" }} />

          {/* SVG overlay with zones and animated paths */}
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
            {/* Zone highlights */}
            {ZONES.map((z, i) => (
              <motion.g key={z.id} initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ delay: 0.3 + i * 0.07 }}>
                <rect x={z.x} y={z.y} width={z.w} height={z.h}
                  fill={`${z.color}14`} stroke={z.color} strokeWidth={0.4} rx={1.5}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={_e => {
                    const svgRect = (_e.currentTarget.ownerSVGElement!).getBoundingClientRect();
                    setTooltip({ zone: z, x: (z.x + z.w / 2) / 100 * svgRect.width, y: z.y / 100 * svgRect.height - 8 });
                  }}
                />
                <text x={z.x + z.w / 2} y={z.y + z.h / 2} textAnchor="middle" dominantBaseline="middle" fill={z.color} fontSize={2.8} fontWeight={600}>{z.label}</text>
                {/* Visitor count dot */}
                {z.visitors > 0 && <circle cx={z.x + z.w - 3} cy={z.y + 3} r={2} fill={z.color} opacity={0.9} />}
                {z.visitors > 0 && <text x={z.x + z.w - 3} y={z.y + 3} textAnchor="middle" dominantBaseline="middle" fill="#fff" fontSize={1.6} fontWeight={700}>{z.visitors}</text>}
              </motion.g>
            ))}

            {/* Animated visitor paths */}
            <motion.circle r={1.2} fill="#fff" opacity={0.9}
              animate={isInView ? { cx: [6, 31, 66, 88, 31, 6], cy: [50, 26, 26, 41, 65, 50], opacity: [0, 1, 1, 1, 1, 0] } : {}}
              transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle r={1.0} fill={theme.accent.purpleLight} opacity={0.85}
              animate={isInView ? { cx: [6, 66, 88, 6], cy: [50, 26, 41, 50], opacity: [0, 1, 1, 0] } : {}}
              transition={{ duration: 5.5, repeat: Infinity, delay: 2, ease: "easeInOut" }}
            />
            <motion.circle r={1.0} fill={theme.accent.amber} opacity={0.85}
              animate={isInView ? { cx: [6, 31, 31, 6], cy: [50, 26, 65, 50], opacity: [0, 1, 1, 0] } : {}}
              transition={{ duration: 4, repeat: Infinity, delay: 3.5, ease: "easeInOut" }}
            />
          </svg>

          {/* Tooltip */}
          {tooltip && (
            <div style={{ position: "absolute", left: tooltip.x, top: tooltip.y, transform: "translate(-50%,-100%)", background: "rgba(8,8,16,0.95)", border: `1px solid ${tooltip.zone.color}40`, borderRadius: theme.radiusSm, padding: "0.75rem 1rem", minWidth: 160, pointerEvents: "none", zIndex: 10 }}>
              <div style={{ fontWeight: 600, fontSize: "0.8rem", marginBottom: "0.5rem", color: tooltip.zone.color }}>{tooltip.zone.label}</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.25rem 0.75rem" }}>
                {[["Visitors", tooltip.zone.visitors], ["Dwell", tooltip.zone.dwell], ["Engagement", tooltip.zone.engagement], ["Anomalies", tooltip.zone.anomalies]].map(([k, v]) => (
                  <div key={String(k)} style={{ fontSize: "0.65rem" }}>
                    <span style={{ color: theme.text.muted }}>{k}: </span>
                    <span style={{ color: theme.text.primary, fontWeight: 500 }}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginTop: "1rem", justifyContent: "center" }}>
          {ZONES.map(z => (
            <div key={z.id} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: z.color, opacity: 0.8 }} />
              <span style={{ fontSize: "0.65rem", color: theme.text.muted }}>{z.label}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
