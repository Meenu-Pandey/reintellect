/**
 * Canonical event types for the ReIntellect platform.
 * Mirrors the backend event schema.
 */

/** The 8 valid event types. */
export type EventType =
  | "ENTRY"
  | "EXIT"
  | "ZONE_ENTER"
  | "ZONE_EXIT"
  | "ZONE_DWELL"
  | "BILLING_QUEUE_JOIN"
  | "BILLING_QUEUE_ABANDON"
  | "REENTRY";

/** Canonical event object from the event stream. */
export interface Event {
  event_id: string;
  event_type: EventType;
  store_id: string;
  visitor_id: string;
  timestamp: string;
  camera_id: string;
  attributes: Record<string, unknown>;
}

/** Store-level KPI metrics returned by GET /stores/{id}/metrics. */
export interface StoreMetrics {
  store_id: string;
  start: string;
  end: string;
  unique_visitors: number;
  conversion_rate: number;
  avg_dwell_per_zone: Record<string, number>;
  queue_depth: number;
  abandonment_rate: number;
  avg_visit_duration_seconds: number;
  peak_hour: number | null;
}

/** A single funnel stage returned by GET /stores/{id}/funnel. */
export interface FunnelStage {
  zone_id: string;
  zone_name: string;
  visitor_count: number;
  entry_rate: number;
  avg_dwell_seconds: number;
}

/** Funnel response shape. */
export interface FunnelResponse {
  stages: FunnelStage[];
  conversion_funnel: Record<string, number>;
  data_available: boolean;
  total_visitors: number;
}

/** A single heatmap grid cell returned by GET /stores/{id}/heatmap. */
export interface HeatmapCell {
  x: number;
  y: number;
  width: number;
  height: number;
  density: number;
}

/** Heatmap response shape. */
export interface HeatmapResponse {
  store_id: string;
  resolution: "low" | "medium" | "high";
  grid_size: number;
  total_cells: number;
  grid: HeatmapCell[];
}

/** Anomaly severity levels. */
export type AnomalySeverity = "high" | "medium" | "low";

/** An anomaly record returned by GET /stores/{id}/anomalies. */
export interface Anomaly {
  anomaly_id: string;
  anomaly_type: string;
  severity: AnomalySeverity;
  detected_at: string;
  description: string;
  metadata: Record<string, unknown>;
}

/** Anomalies response shape. */
export interface AnomaliesResponse {
  store_id: string;
  anomalies: Anomaly[];
  count: number;
}
