/**
 * ReIntellect Design System — Hackathon Edition
 * Premium dark enterprise theme with Purplle brand identity
 */

export const theme = {
  bg: {
    primary: "#080810",
    card: "#0f0f1a",
    elevated: "#161625",
    hover: "#1e1e30",
    glass: "rgba(15,15,26,0.7)",
  },
  border: "#1a1a2e",
  borderLight: "#252540",
  borderGlow: "rgba(139,92,246,0.3)",
  text: {
    primary: "#f4f4f8",
    secondary: "#9898b0",
    muted: "#4a4a65",
  },
  accent: {
    purple: "#7c3aed",
    purpleMid: "#8b5cf6",
    purpleLight: "#a78bfa",
    purpleDim: "rgba(124,58,237,0.15)",
    green: "#10b981",
    greenDim: "rgba(16,185,129,0.15)",
    red: "#ef4444",
    amber: "#f59e0b",
    blue: "#3b82f6",
    cyan: "#06b6d4",
    pink: "#ec4899",
  },
  radius: "14px",
  radiusSm: "10px",
  radiusXs: "7px",
  font: "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
  fontMono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const EVENT_COLORS: Record<string, string> = {
  ENTRY: "#10b981",
  EXIT: "#ef4444",
  ZONE_ENTER: "#3b82f6",
  ZONE_EXIT: "#60a5fa",
  ZONE_DWELL: "#8b5cf6",
  BILLING_QUEUE_JOIN: "#f59e0b",
  BILLING_QUEUE_ABANDON: "#dc2626",
  REENTRY: "#06b6d4",
};

export const SEVERITY_COLORS: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#6b7280",
};
