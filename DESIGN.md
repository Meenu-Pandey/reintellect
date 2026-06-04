# ReIntellect — System Design Document

## Overview

ReIntellect is a monolithic AI-powered Store Intelligence Platform that transforms raw CCTV footage into real-time retail analytics. The backend runs as a single Python process containing the detection pipeline, event engine, and FastAPI service, communicating internally via `asyncio.Queue`. This eliminates network overhead and simplifies deployment.

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Stack                           │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  backend  (single Python process)                │  │
│  │                                                                  │  │
│  │  ┌─────────────────┐   asyncio.Queue   ┌──────────────────────┐ │  │
│  │  │ DetectionPipeline│ ──TrackFrames──► │    EventEngine       │ │  │
│  │  │                  │                  │                      │ │  │
│  │  │  YOLOv8n         │                  │  VisitorRegistry     │ │  │
│  │  │  ByteTrack       │                  │  ZoneTracker         │ │  │
│  │  │  Staff Filter    │                  │  QueueTracker        │ │  │
│  │  └─────────────────┘                  │  AnomalyDetector     │ │  │
│  │                                        └──────────┬───────────┘ │  │
│  │                                                   │ asyncio.Queue│  │
│  │                                        ┌──────────▼───────────┐ │  │
│  │                                        │  FastAPI + Uvicorn   │ │  │
│  │                                        │  event_consumer task │ │  │
│  │                                        │  REST endpoints      │ │  │
│  │                                        │  WebSocket push      │ │  │
│  │                                        │  SQLite WAL          │ │  │
│  │                                        └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              port 8000                                 │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  frontend — React SPA served by Nginx                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              port 3000                                 │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  db-init — one-shot: schema DDL + demo data, then exits 0        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### DetectionPipeline

Reads video frames from `cv2.VideoCapture`, runs YOLOv8n inference (person class only, confidence ≥ 0.5, bbox height ≥ 50px), applies ByteTrack multi-object tracking, and classifies each detection as `visitor` or `staff` using an HSV colour heuristic. Outputs `TrackFrame` objects onto `track_queue`.

**Key parameters:**
- Re-association window: lost tracks re-associated if absent < 30 frames
- Device selection: `torch.cuda.is_available()` → CUDA if available, else CPU
- On feed loss: logs timestamp, polls for reconnect every 2s, preserves track state

### EventEngine

Consumes `TrackFrame` objects and maintains per-visitor state machines:

| Sub-component | Responsibility |
|---|---|
| `VisitorRegistry` | Maps `track_id → visitor_id`; handles re-entry and camera handoff |
| `ZoneTracker` | OUTSIDE → IN_ZONE → DWELL_EMITTED state machine per (visitor, zone) |
| `QueueTracker` | Billing queue membership, depth counter, abandonment detection |
| `AnomalyDetector` | Threshold-based anomaly classification |

All events are assembled as `Event` objects and placed on `event_queue`.

**Emission latency target:** ≤ 500ms from triggering condition.

### FastAPI Layer

Three responsibilities:
1. `event_consumer` asyncio task: drains `event_queue`, calls `db.upsert_event()` (idempotent by `event_id`), calls `ws_manager.broadcast()`
2. REST endpoints: analytics queries against SQLite
3. WebSocket `ConnectionManager`: per-store connection registry, initial state payload (last 50 events), idle timeout 60s

---

## Canonical Event Schema

All events share this structure:

```json
{
  "event_id":   "<UUID v4, client-supplied>",
  "event_type": "<one of 8 values>",
  "store_id":   "<string>",
  "visitor_id": "<UUID v4>",
  "timestamp":  "<ISO 8601 UTC>",
  "camera_id":  "<string>",
  "attributes": { "<event-type-specific fields>" }
}
```

**Event types and their `attributes`:**

| event_type | attributes |
|---|---|
| `ENTRY` | _(none required)_ |
| `EXIT` | `duration_seconds: float` |
| `ZONE_ENTER` | `zone_id: str` |
| `ZONE_EXIT` | `zone_id: str`, `dwell_seconds: float` |
| `ZONE_DWELL` | `zone_id: str`, `dwell_seconds: float (≥30)` |
| `BILLING_QUEUE_JOIN` | `queue_position: int (≥1)` |
| `BILLING_QUEUE_ABANDON` | `wait_seconds: float` |
| `REENTRY` | `gap_seconds: float` |

**Key invariants:**
- `track_id` (ByteTrack internal) is **never** exposed in the public schema
- `event_id` is always **client-supplied** (idempotency key, not server-generated)
- `visitor_id` is assigned at `ENTRY` confirmation and persists across camera handoffs and re-entries < 300s

---

## Database Schema

SQLite with WAL mode. All timestamps are ISO 8601 UTC strings.

**Tables:** `stores`, `zones`, `cameras`, `visitors`, `visits`, `events`, `track_positions`, `pos_transactions`, `anomalies`

**Critical indexes:**
```sql
CREATE INDEX idx_events_store_timestamp ON events(store_id, timestamp);
CREATE INDEX idx_events_visitor          ON events(visitor_id);
CREATE INDEX idx_track_positions_store_ts ON track_positions(store_id, timestamp);
```

**Idempotency:** Events are inserted with `INSERT OR IGNORE` keyed on `event_id`. Submitting the same event twice produces exactly one database row.

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Subsystem health with live probes |
| `GET` | `/schema/events` | Canonical JSON Schema |
| `POST` | `/stores` | Create/update store layout |
| `POST` | `/stores/{id}/transactions` | Ingest POS transaction |
| `POST` | `/events/ingest` | Single or batch event ingestion (≤500, atomic) |
| `GET` | `/stores/{id}/metrics` | KPIs for a time window |
| `GET` | `/stores/{id}/funnel` | Visitor funnel stages |
| `GET` | `/stores/{id}/heatmap` | Density grid (10×10, 20×20, 40×40) |
| `GET` | `/stores/{id}/anomalies` | Anomaly records |
| `WS` | `/ws/stores/{id}/events` | Real-time event stream |

---

## WebSocket Protocol

**On connect:** Server sends initial state:
```json
{ "type": "initial_state", "events": [ ...last 50 events... ] }
```

**Streaming:** Each new event is pushed as:
```json
{ "type": "event", "data": { ...canonical event object... } }
```

**Close codes:**
- `4004`: Unknown `store_id`
- `1001`: Idle timeout (60s without ping)
- `1011`: Internal send error

---

## Visitor Identity Logic

```
New track detected
→ check VisitorRegistry
→ if track_id known: return existing visitor_id
→ if track crosses entry zone (inward):
    → check _exit_times for recent exits
    → if gap < 300s: reuse visitor_id, emit REENTRY
    → if gap ≥ 300s or no prior exit: assign new visitor_id, emit ENTRY
```

Camera handoff (same person, different camera): `merge_camera_handoff()` unifies two `track_id` values to one `visitor_id` if gap ≤ 10s.

---

## Anomaly Detection Thresholds

| Anomaly | Trigger | Severity |
|---|---|---|
| `QUEUE_BUILDUP` | Queue depth > 5 for > 180s | high |
| `EMPTY_STORE` | 0 visitors for > 600s during operating hours | medium |
| `UNUSUAL_DWELL` | Single zone dwell > 900s | low |
| `CAMERA_OVERLAP_CONFLICT` | Same track in two non-adjacent zones within 2s | high |

All anomalies are persisted to the `anomalies` table and broadcast via WebSocket.

---

## Correctness Properties

Eleven properties verified by Hypothesis property-based tests:

1. Event schema round-trip equality
2. Visit duration non-negativity
3. Detection threshold filtering (confidence ≥ 0.5, bbox ≥ 50px)
4. Staff exclusion invariant
5. Zone dwell threshold (ZONE_DWELL iff dwell ≥ 30s)
6. Re-entry visitor identity preservation (same ID iff gap < 300s)
7. Queue position monotonicity (position = prior_depth + 1)
8. Event ingestion idempotency (N submissions → 1 DB row)
9. Batch atomic rejection (any invalid → entire batch rejected)
10. Conversion rate correctness (= 0.0 when unique_visitors = 0)
11. Unique visitor count excludes re-entries

---

## Frontend Architecture

React 18 + TypeScript SPA served by Nginx.

**State management:**
- **Zustand**: WebSocket-driven live state (visitor count, queue depth, last 20 events, connection status)
- **TanStack React Query**: REST polling with configured refetch intervals

**Screens:** Overview, Funnel, Heatmap, Anomalies, Live Feed

**Responsive:** 1280px – 2560px, no horizontal overflow

**WebSocket reconnect backoff:** 1s, 2s, 4s, 8s, 16s (5 attempts), then manual retry button

---

## Testing Strategy

| Suite | Scope | Tools |
|---|---|---|
| Unit | EventEngine, ZoneTracker, VisitorRegistry, QueueTracker | Pytest |
| Integration | All REST endpoints + WebSocket | Pytest + Starlette TestClient |
| Property | 11 correctness properties | Hypothesis (≥100 examples each) |
| Smoke | Docker Compose health check | Pytest + requests |

**Coverage achieved:** engine/ ~85%, api/ ~81% (total 81%)
