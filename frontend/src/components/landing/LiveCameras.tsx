import { useRef, useCallback, useState, useEffect } from "react";
import { motion, useInView } from "framer-motion";
import { Users, Activity } from "lucide-react";
import { theme } from "../../styles/theme";

const CAMERAS = [
  {
    name: "Entry Camera 1",
    zone: "Main Entrance · CAM3",
    fps: 30,
    tracks: 4,
    visitors: 2,
    src: "/videos/entry-camera-1.mp4",
    poster: "/thumbnails/entry-camera-1.jpg",
  },
  {
    name: "Entry Camera 2",
    zone: "Secondary Entrance · CAM2",
    fps: 30,
    tracks: 2,
    visitors: 1,
    src: "/videos/entry-camera-2.mp4",
    poster: "/thumbnails/entry-camera-2.jpg",
  },
  {
    name: "Shopping Zone",
    zone: "Cosmetics & Skincare · CAM5",
    fps: 30,
    tracks: 7,
    visitors: 6,
    src: "/videos/shopping-zone.mp4",
    poster: "/thumbnails/shopping-zone.jpg",
  },
  {
    name: "Billing Area",
    zone: "Checkout Counter · CAM1",
    fps: 30,
    tracks: 3,
    visitors: 3,
    src: "/videos/billing-area.mp4",
    poster: "/thumbnails/billing-area.jpg",
  },
];

export function LiveCameras() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section id="product" ref={ref} style={{ padding: "6rem clamp(1rem,4vw,3rem)" }}>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6 }}
        style={{ textAlign: "center", marginBottom: "3.5rem" }}
      >
        <div style={{ fontSize: "0.65rem", color: theme.accent.purpleLight, textTransform: "uppercase", letterSpacing: "0.2em", fontWeight: 600, marginBottom: "0.75rem" }}>Live Camera Intelligence</div>
        <h2 style={{ fontSize: "clamp(1.8rem,3vw,2.4rem)", fontWeight: 700, letterSpacing: "-0.03em", fontFamily: "'Space Grotesk',sans-serif" }}>
          5 Cameras. 1 Intelligence Layer.
        </h2>
        <p style={{ fontSize: "0.95rem", color: theme.text.secondary, maxWidth: 500, margin: "0.75rem auto 0" }}>
          Real CCTV footage from Purplle Brigade Road, processed by YOLOv8 and ByteTrack in real time.
        </p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(min(100%,260px),1fr))", gap: "1rem", maxWidth: 1100, margin: "0 auto" }}>
        {CAMERAS.map((cam, i) => (
          <CameraCard key={i} cam={cam} index={i} sectionInView={isInView} />
        ))}
      </div>
    </section>
  );
}

function CameraCard({
  cam,
  index,
  sectionInView,
}: {
  cam: typeof CAMERAS[0];
  index: number;
  sectionInView: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={sectionInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.45, delay: index * 0.1 }}
      whileHover={{ borderColor: "rgba(139,92,246,0.45)", boxShadow: "0 0 28px rgba(139,92,246,0.12)" }}
      style={{ background: theme.bg.card, border: `1px solid ${theme.border}`, borderRadius: theme.radius, overflow: "hidden", transition: "border-color 0.2s, box-shadow 0.2s" }}
    >
      <CameraPreview src={cam.src} poster={cam.poster} fps={cam.fps} inView={sectionInView} />

      <div style={{ padding: "0.85rem 1rem" }}>
        <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "0.2rem" }}>{cam.name}</div>
        <div style={{ fontSize: "0.68rem", color: theme.text.muted, marginBottom: "0.7rem" }}>{cam.zone}</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.45rem" }}>
          <StatChip icon={<Activity size={10} />} label="Tracks" value={cam.tracks} color={theme.accent.purpleMid} />
          <StatChip icon={<Users size={10} />} label="Visitors" value={cam.visitors} color={theme.accent.green} />
        </div>
      </div>
      <div style={{ height: 2, background: `linear-gradient(90deg, transparent, ${theme.accent.green}70, transparent)` }} />
    </motion.div>
  );
}

function CameraPreview({ src, poster, fps, inView }: { src: string; poster: string; fps: number; inView: boolean }) {
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleCanPlay = useCallback(() => {
    videoRef.current?.play().catch(() => {
      // Autoplay blocked — poster image is shown
    });
  }, []);

  return (
    <div style={{ position: "relative", height: 172, overflow: "hidden", background: "#06060e" }}>
      {/* Real video — lazy loaded, only renders when section is in viewport */}
      {inView ? (
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          muted
          loop
          playsInline
          preload="none"
          onCanPlay={handleCanPlay}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
        />
      ) : (
        <img src={poster} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.7 }} />
      )}

      {/* Dark gradient bottom overlay */}
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(6,6,14,0.1) 0%, rgba(6,6,14,0.55) 100%)", pointerEvents: "none" }} />

      {/* Scan line */}
      <motion.div
        animate={{ top: ["0%", "100%"] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "linear" }}
        style={{ position: "absolute", left: 0, right: 0, height: 1, background: "linear-gradient(90deg, transparent, rgba(139,92,246,0.4), transparent)", pointerEvents: "none" }}
      />

      {/* Decorative tracking boxes */}
      <TrackingBoxes />

      {/* LIVE badge */}
      <div style={{ position: "absolute", top: 9, right: 9, display: "flex", alignItems: "center", gap: "0.3rem", padding: "0.18rem 0.48rem", background: "rgba(239,68,68,0.18)", border: "1px solid rgba(239,68,68,0.35)", borderRadius: "9999px" }}>
        <motion.div animate={{ opacity: [1, 0.2, 1] }} transition={{ duration: 1.3, repeat: Infinity }} style={{ width: 5, height: 5, borderRadius: "50%", background: "#ef4444" }} />
        <span style={{ fontSize: "0.52rem", color: "#ef4444", fontWeight: 700, letterSpacing: "0.04em" }}>LIVE</span>
      </div>

      {/* FPS counter */}
      <div style={{ position: "absolute", top: 9, left: 9, padding: "0.18rem 0.42rem", background: "rgba(6,6,14,0.75)", borderRadius: 4, fontSize: "0.52rem", color: theme.text.secondary, fontFamily: theme.fontMono }}>{fps} FPS</div>

      {/* Live timestamp */}
      <LiveClock />
    </div>
  );
}

/** Decorative bounding-box overlays — purely visual, not real detections */
function TrackingBoxes() {
  const BOXES = [
    { left: "18%", top: "20%", w: 18, h: 28 },
    { left: "54%", top: "16%", w: 16, h: 26 },
    { left: "37%", top: "34%", w: 14, h: 22 },
  ];
  return (
    <>
      {BOXES.map((b, i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0, 0.75, 0.75, 0] }}
          transition={{ duration: 4.5, delay: i * 1.4, repeat: Infinity, ease: "easeInOut" }}
          style={{ position: "absolute", left: b.left, top: b.top, width: b.w, height: b.h, border: "1px solid rgba(139,92,246,0.6)", borderRadius: 2, pointerEvents: "none" }}
        >
          <div style={{ position: "absolute", top: -1, left: -1, width: 5, height: 5, borderTop: "1.5px solid #8b5cf6", borderLeft: "1.5px solid #8b5cf6" }} />
          <div style={{ position: "absolute", top: -1, right: -1, width: 5, height: 5, borderTop: "1.5px solid #8b5cf6", borderRight: "1.5px solid #8b5cf6" }} />
          <div style={{ position: "absolute", bottom: -1, left: -1, width: 5, height: 5, borderBottom: "1.5px solid #8b5cf6", borderLeft: "1.5px solid #8b5cf6" }} />
          <div style={{ position: "absolute", bottom: -1, right: -1, width: 5, height: 5, borderBottom: "1.5px solid #8b5cf6", borderRight: "1.5px solid #8b5cf6" }} />
        </motion.div>
      ))}
    </>
  );
}

function LiveClock() {
  const [time, setTime] = useState(getIST());
  useEffect(() => {
    const id = setInterval(() => setTime(getIST()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <div style={{ position: "absolute", bottom: 8, right: 9, fontSize: "0.5rem", color: "rgba(255,255,255,0.45)", fontFamily: "monospace" }}>
      {time} IST
    </div>
  );
}

function getIST() {
  return new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function StatChip({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", padding: "0.32rem 0.5rem", background: theme.bg.elevated, borderRadius: theme.radiusXs }}>
      <span style={{ color }}>{icon}</span>
      <span style={{ fontSize: "0.62rem", color: theme.text.muted }}>{label}</span>
      <span style={{ marginLeft: "auto", fontSize: "0.78rem", fontWeight: 700, color }}>{value}</span>
    </div>
  );
}
