import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { theme } from "../../styles/theme";

const ZONES = [
  { id: "entry", label: "Entrance", x: 3, y: 32, w: 14, h: 36, color: "#10b981" },
  { id: "maybelline", label: "Maybelline", x: 20, y: 3, w: 30, h: 42, color: "#a855f7" },
  { id: "lakme", label: "Lakme", x: 52, y: 3, w: 30, h: 42, color: "#ec4899" },
  { id: "queue", label: "Checkout", x: 58, y: 48, w: 22, h: 20, color: "#f59e0b" },
  { id: "skincare", label: "Skincare", x: 20, y: 55, w: 35, h: 40, color: "#06b6d4" },
  { id: "exit", label: "Exit", x: 84, y: 32, w: 14, h: 36, color: "#ef4444" },
];

export function StoreIntelligence() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section ref={ref} style={{ padding: "6rem 2rem" }}>
      <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.5 }} style={{ textAlign: "center", marginBottom: "3rem" }}>
        <div style={{ fontSize: "0.65rem", color: theme.accent.purple, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Purplle Brigade Road</div>
        <h2 style={{ fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>Every Zone, Every Journey</h2>
        <p style={{ fontSize: "0.9rem", color: theme.text.secondary, maxWidth: 440, margin: "0.75rem auto 0" }}>Visitor movement tracked across all store zones in real time.</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.7, delay: 0.2 }}
        style={{ maxWidth: 720, margin: "0 auto", aspectRatio: "16/9", background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, position: "relative", overflow: "hidden", width: "100%" }}
      >
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(123,31,162,0.04) 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: "100%", position: "relative" }}>
          {ZONES.map((z, i) => (
            <motion.g key={z.id} initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ duration: 0.4, delay: 0.4 + i * 0.07 }}>
              <rect x={z.x} y={z.y} width={z.w} height={z.h} fill={`${z.color}10`} stroke={z.color} strokeWidth={0.3} rx={1.2} />
              <text x={z.x + z.w / 2} y={z.y + z.h / 2} textAnchor="middle" dominantBaseline="middle" fill={z.color} fontSize={2.8} fontWeight={600}>{z.label}</text>
            </motion.g>
          ))}
          {/* Visitor paths */}
          <motion.circle r={1} fill="#fff" animate={isInView ? { cx: [10, 35, 67, 69, 40, 91], cy: [50, 22, 22, 58, 75, 50], opacity: [0, 1, 1, 1, 1, 0] } : {}} transition={{ duration: 7, repeat: Infinity, repeatDelay: 0.5, ease: "easeInOut" }} />
          <motion.circle r={1} fill={theme.accent.purpleLight} animate={isInView ? { cx: [10, 35, 35, 69, 91], cy: [50, 75, 22, 58, 50], opacity: [0, 1, 1, 1, 0] } : {}} transition={{ duration: 5.5, repeat: Infinity, repeatDelay: 2, delay: 1.5, ease: "easeInOut" }} />
          <motion.circle r={0.8} fill={theme.accent.amber} animate={isInView ? { cx: [10, 67, 69, 91], cy: [50, 22, 58, 50], opacity: [0, 1, 1, 0] } : {}} transition={{ duration: 4, repeat: Infinity, repeatDelay: 3, delay: 3, ease: "easeInOut" }} />
        </svg>
      </motion.div>
    </section>
  );
}
