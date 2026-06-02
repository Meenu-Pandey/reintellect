/**
 * Heatmap screen.
 *
 * Renders a canvas overlay with grid cells coloured by density.
 * Colour scale: green (low) → yellow (mid) → red (high).
 * Density 0.0 = transparent, density 1.0 = fully opaque red.
 * Time-window selector: "Last 1h", "Last 4h", "Today".
 */

import { useEffect, useRef, useState } from "react";
import { useHeatmap } from "../../api/hooks/useHeatmap";

interface Props {
  storeId: string;
}

type TimeWindow = "1h" | "4h" | "today";

function getTimeWindow(window: TimeWindow): { start: string; end: string } {
  const now = new Date();
  const end = now.toISOString();
  let start: string;

  switch (window) {
    case "1h":
      start = new Date(now.getTime() - 60 * 60 * 1000).toISOString();
      break;
    case "4h":
      start = new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString();
      break;
    case "today":
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
      break;
  }

  return { start, end };
}

function densityToColor(density: number): string {
  // Green → Yellow → Red gradient
  if (density <= 0) return "rgba(0,0,0,0)";

  const r = density < 0.5 ? Math.round(density * 2 * 255) : 255;
  const g = density < 0.5 ? 255 : Math.round((1 - (density - 0.5) * 2) * 255);
  const b = 0;
  const a = Math.min(1, density * 0.8 + 0.1);

  return `rgba(${r},${g},${b},${a})`;
}

export function HeatmapScreen({ storeId }: Props) {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>("today");
  const [resolution, setResolution] = useState<"low" | "medium" | "high">("medium");
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const tw = getTimeWindow(timeWindow);
  const { data, isLoading } = useHeatmap(storeId, tw);

  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Draw background
    ctx.fillStyle = "#f8f9fa";
    ctx.fillRect(0, 0, width, height);

    // Draw grid cells
    for (const cell of data.grid) {
      const px = cell.x * width;
      const py = cell.y * height;
      const pw = cell.width * width;
      const ph = cell.height * height;

      ctx.fillStyle = densityToColor(cell.density);
      ctx.fillRect(px, py, pw, ph);
    }

    // Draw grid lines (subtle)
    ctx.strokeStyle = "rgba(0,0,0,0.05)";
    ctx.lineWidth = 0.5;
    const gridSize = data.grid_size;
    const cellW = width / gridSize;
    const cellH = height / gridSize;
    for (let i = 0; i <= gridSize; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cellW, 0);
      ctx.lineTo(i * cellW, height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * cellH);
      ctx.lineTo(width, i * cellH);
      ctx.stroke();
    }
  }, [data]);

  const buttons: { id: TimeWindow; label: string }[] = [
    { id: "1h", label: "Last 1h" },
    { id: "4h", label: "Last 4h" },
    { id: "today", label: "Today" },
  ];

  const resolutions: { id: "low" | "medium" | "high"; label: string }[] = [
    { id: "low", label: "Low (10×10)" },
    { id: "medium", label: "Medium (20×20)" },
    { id: "high", label: "High (40×40)" },
  ];

  return (
    <div>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Heatmap</h2>

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
        {buttons.map((btn) => (
          <button
            key={btn.id}
            onClick={() => setTimeWindow(btn.id)}
            style={{
              padding: "0.4rem 0.75rem",
              border: "1px solid #ccc",
              borderRadius: "4px",
              background: timeWindow === btn.id ? "#333" : "#fff",
              color: timeWindow === btn.id ? "#fff" : "#333",
              cursor: "pointer",
              fontSize: "0.8rem",
            }}
          >
            {btn.label}
          </button>
        ))}

        <select
          value={resolution}
          onChange={(e) => setResolution(e.target.value as "low" | "medium" | "high")}
          style={{ marginLeft: "auto", padding: "0.4rem", fontSize: "0.8rem" }}
          aria-label="Heatmap resolution"
        >
          {resolutions.map((r) => (
            <option key={r.id} value={r.id}>{r.label}</option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div style={{ height: "400px", background: "#f3f4f6", borderRadius: "8px" }} />
      )}

      <canvas
        ref={canvasRef}
        width={600}
        height={400}
        style={{
          width: "100%",
          maxWidth: "600px",
          height: "auto",
          aspectRatio: "3/2",
          border: "1px solid #e0e0e0",
          borderRadius: "8px",
          display: isLoading ? "none" : "block",
        }}
      />

      {data && (
        <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#888" }}>
          Resolution: {data.grid_size}×{data.grid_size} ({data.total_cells} cells)
        </div>
      )}
    </div>
  );
}
