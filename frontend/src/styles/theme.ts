/**
 * ReIntellect Design System — Premium Dark Enterprise Theme.
 */

export const theme = {
  bg: {
    primary: "#09090b",
    card: "#141419",
    elevated: "#1c1c24",
    hover: "#22222c",
  },
  border: "#1f1f2e",
  borderLight: "#2a2a3d",
  text: {
    primary: "#fafafa",
    secondary: "#a1a1aa",
    muted: "#52525b",
  },
  accent: {
    purple: "#7B1FA2",
    purpleMid: "#9C27B0",
    purpleLight: "#CE93D8",
    green: "#10b981",
    red: "#ef4444",
    amber: "#f59e0b",
    blue: "#3b82f6",
    cyan: "#06b6d4",
  },
  radius: "12px",
  radiusSm: "8px",
  radiusXs: "6px",
  font: "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
} as const;

export const EVENT_COLORS: Record<string, string> = {
  ENTRY: "#10b981",
  EXIT: "#ef4444",
  ZONE_ENTER: "#3b82f6",
  ZONE_EXIT: "#60a5fa",
  ZONE_DWELL: "#a855f7",
  BILLING_QUEUE_JOIN: "#f59e0b",
  BILLING_QUEUE_ABANDON: "#dc2626",
  REENTRY: "#06b6d4",
};

export const SEVERITY_COLORS: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#6b7280",
};
