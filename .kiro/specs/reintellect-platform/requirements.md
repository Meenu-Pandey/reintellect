# Requirements Document

## Introduction

ReIntellect is an AI-powered Store Intelligence Platform built for the Purplle Tech Challenge 2026. It transforms raw CCTV footage from retail stores into real-time analytics and business intelligence. The platform ingests video streams from entry, main floor, and billing cameras; runs a computer-vision detection and tracking pipeline; emits a structured event stream; exposes a REST + WebSocket Intelligence API; and renders a real-time dashboard for store operators.

The primary business metric the platform optimises is **Offline Store Conversion Rate**:

```
Conversion Rate = Visitors who completed a purchase / Total unique visitors
```

The platform is designed for hackathon evaluation with production-grade engineering: clean architecture, strong documentation, containerised deployment, and a comprehensive test suite.

---

## Glossary

- **ReIntellect**: The complete AI-powered Store Intelligence Platform described in this document.
- **Detection_Pipeline**: The subsystem that ingests CCTV video frames, runs YOLOv8n object detection, and applies ByteTrack multi-object tracking to produce person tracks.
- **Event_Engine**: The subsystem that consumes person tracks and store-layout context to classify and emit structured retail events.
- **Event_Stream**: The ordered sequence of structured retail events produced by the Event_Engine.
- **Intelligence_API**: The FastAPI-based HTTP and WebSocket service that exposes ingestion endpoints, metric queries, and real-time event push.
- **Dashboard**: The React + Vite single-page application that visualises store analytics in real time.
- **Store**: A physical retail location identified by a unique store ID, containing one or more camera feeds and a defined layout.
- **Zone**: A named, bounded region within a store floor plan (e.g., "Skincare Aisle", "Checkout Counter").
- **Track**: A continuous sequence of bounding-box detections assigned to a single person across video frames by ByteTrack. Each Track is assigned an internal `track_id` by ByteTrack; this is a pipeline-internal concept and is not exposed in the public event schema.
- **Visitor**: A unique person detected entering the store through the entry camera zone, excluding staff. Each Visitor is assigned a `visitor_id` at the moment their `ENTRY` event is confirmed; this is the public identifier used in all events and APIs.
- **Visitor_ID**: The stable, business-level identifier assigned to a Visitor at entry confirmation. It persists across camera handoffs and re-entries within 300 seconds. It is distinct from `track_id`, which is an internal ByteTrack concept.
- **Staff**: A person wearing a staff identifier (uniform colour or badge region) excluded from visitor counts.
- **Conversion**: A Visitor who is associated with at least one POS transaction during their store visit.
- **Dwell_Time**: The duration in seconds a Track remains within a Zone.
- **Funnel**: The ordered sequence of store zones a Visitor traverses from entry to billing.
- **Heatmap**: A spatial density map of Track positions aggregated over a time window.
- **Anomaly**: A detected deviation from baseline store behaviour (e.g., queue buildup, empty store, unusual dwell).
- **POS_Transaction**: A point-of-sale record linking a transaction timestamp and amount to a store.
- **ByteTrack**: The multi-object tracking algorithm used to assign persistent IDs to detected persons across frames.
- **YOLOv8n**: The nano variant of the YOLOv8 object detection model used for real-time person detection.
- **SQLite**: The embedded relational database used for event and metric persistence.
- **WebSocket**: The persistent bidirectional connection used to push real-time events to the Dashboard.
- **Docker_Compose**: The container orchestration tool used to run all platform services.
- **Pytest**: The Python testing framework used for unit, integration, and property-based tests.

---

## Requirements

### Requirement 1: Person Detection and Tracking

**User Story:** As a store analyst, I want the platform to detect and track every person in CCTV footage, so that I can measure unique visitor counts and movement patterns accurately.

#### Acceptance Criteria

1. WHEN a video frame is received from any camera feed, THE Detection_Pipeline SHALL detect all persons in the frame using YOLOv8n with a confidence threshold of at least 0.5 and a minimum bounding box height of 50 pixels; detections below either threshold SHALL be discarded without track assignment.
2. WHEN persons are detected across consecutive frames, THE Detection_Pipeline SHALL assign persistent track IDs using ByteTrack so that each person retains the same ID throughout their continuous appearance.
3. WHEN a person's track is lost for fewer than 30 frames, THE Detection_Pipeline SHALL re-associate the returning detection with the original track ID to handle partial occlusion; IF the absence spans 30 or more frames, THE Detection_Pipeline SHALL assign a new track ID to the returning detection.
4. WHEN two or more persons enter the frame simultaneously through the entry zone, THE Detection_Pipeline SHALL assign a distinct track ID to each person within 5 frames of their appearance.
5. WHEN a person wearing a staff identifier (defined as a high-visibility vest, uniform badge, or other visually distinct marker designated in system configuration) is detected, THE Detection_Pipeline SHALL tag the track as `role=staff` and exclude it from Visitor counts.
6. THE Detection_Pipeline SHALL process frames at a minimum rate of 10 frames per second per camera feed on the minimum system specification defined in the deployment configuration.
7. IF a camera feed becomes unavailable, THEN THE Detection_Pipeline SHALL log the interruption with a timestamp and resume processing when the feed is restored, preserving all active track IDs and their last known positions without reset.
8. WHEN a detection falls below the 0.5 confidence threshold or the 50-pixel bounding box height threshold, THE Detection_Pipeline SHALL discard the detection and SHALL NOT assign or update any track ID for that detection.

---

### Requirement 2: Retail Event Classification

**User Story:** As a store analyst, I want every meaningful customer action to be captured as a structured event, so that I can reconstruct the complete customer journey.

#### Acceptance Criteria

1. WHEN a Visitor track crosses the entry camera zone boundary from outside to inside, THE Event_Engine SHALL assign a `visitor_id` to that Visitor (if not already assigned) and emit an `ENTRY` event containing `visitor_id`, `store_id`, `timestamp` (the moment of boundary crossing), and `camera_id`.
2. WHEN a Visitor track crosses the entry camera zone boundary from inside to outside and does not re-enter within 60 seconds, THE Event_Engine SHALL emit an `EXIT` event containing `visitor_id`, `store_id`, `timestamp` (the moment of outward boundary crossing), `duration_seconds`, and `camera_id`.
3. WHEN a Visitor track enters a defined Zone boundary, THE Event_Engine SHALL emit a `ZONE_ENTER` event containing `visitor_id`, `zone_id`, `store_id`, and `timestamp`.
4. WHEN a Visitor track exits a defined Zone boundary, THE Event_Engine SHALL emit a `ZONE_EXIT` event containing `visitor_id`, `zone_id`, `store_id`, `timestamp`, and `dwell_seconds`.
5. WHEN a Visitor track remains within a single Zone for 30 or more consecutive seconds, THE Event_Engine SHALL emit a `ZONE_DWELL` event containing `visitor_id`, `zone_id`, `store_id`, `timestamp`, and `dwell_seconds` (the running total dwell time at the moment of emission, which SHALL be at least 30).
6. WHEN a Visitor track enters the billing queue Zone, THE Event_Engine SHALL emit a `BILLING_QUEUE_JOIN` event containing `visitor_id`, `store_id`, `timestamp`, and `queue_position` (the 1-based count of visitors already in the billing queue zone at the moment of entry, plus one).
7. WHEN a Visitor track that has emitted a `BILLING_QUEUE_JOIN` event exits the billing queue Zone without a POS transaction linked to that `visitor_id` within 120 seconds of the `BILLING_QUEUE_JOIN` timestamp, THE Event_Engine SHALL emit a `BILLING_QUEUE_ABANDON` event containing `visitor_id`, `store_id`, `timestamp`, and `wait_seconds`.
8. WHEN a Visitor track that previously emitted an `EXIT` event re-enters the store within 300 seconds, THE Event_Engine SHALL emit a `REENTRY` event containing the original `visitor_id` (the same `visitor_id` assigned at the initial `ENTRY` event), `store_id`, `timestamp`, and `gap_seconds`.
9. THE Event_Engine SHALL emit all events within 500 milliseconds of the triggering condition being detected.
10. IF an event cannot be persisted to the database within 2 seconds of emission, THEN THE Event_Engine SHALL log the failure with the full event payload and retry up to 3 times with exponential backoff intervals of 1 second, 2 seconds, and 4 seconds.
11. WHEN a Visitor track is lost (absent for 30 or more frames) while inside a Zone, THE Event_Engine SHALL emit a `ZONE_EXIT` event for that Zone using the last known timestamp, the `visitor_id` of that Visitor, and the dwell time accumulated up to the point of track loss.

---

### Requirement 3: Store Layout Integration

**User Story:** As a store manager, I want to define my store's floor plan and camera zones, so that the platform can map detections to meaningful retail locations.

#### Acceptance Criteria

1. THE Intelligence_API SHALL accept a store layout definition as a JSON document containing `store_id`, `name`, a list of `zones` (each with `zone_id`, `name`, `polygon` coordinates, and `zone_type`), and a list of `cameras` (each with `camera_id`, `position`, and `coverage_polygon`).
2. WHEN a store layout is submitted, THE Intelligence_API SHALL validate that all zone polygons and camera coverage polygons are closed, non-self-intersecting, contain at least 3 vertices, and are expressed in normalised coordinates between 0.0 and 1.0.
3. IF a submitted store layout fails any validation check (overlapping zone polygons, invalid geometry, or a camera referencing an unknown `zone_id`), THEN THE Intelligence_API SHALL return HTTP 422 with a descriptive error identifying the specific failing element(s).
4. WHEN a valid store layout is submitted, THE Intelligence_API SHALL persist it, return HTTP 200 with the persisted layout including all assigned IDs, and make it available to the Event_Engine within 1 second.
5. THE Intelligence_API SHALL support the following `zone_type` values: `entry`, `exit`, `floor`, `billing_queue`, `staff_area`.
6. WHEN a store layout is submitted with a `store_id` that already exists, THE Intelligence_API SHALL replace the existing layout with the new one (upsert behaviour) and return HTTP 200.

---

### Requirement 4: Event Ingestion API

**User Story:** As an integration developer, I want a reliable HTTP endpoint to ingest events from the detection pipeline, so that events are durably stored and immediately available for analytics.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `POST /events/ingest` endpoint that accepts a JSON body conforming to the canonical event schema defined in Requirement 15.
2. WHEN a valid event payload is received at `POST /events/ingest` and no event with the same `event_id` already exists in the database, THE Intelligence_API SHALL persist the event to SQLite and return HTTP 201 with the persisted event.
3. WHEN a valid event payload is received at `POST /events/ingest` and an event with the same `event_id` already exists in the database, THE Intelligence_API SHALL return HTTP 200 with the originally persisted event without creating a duplicate (idempotent behaviour by `event_id`).
4. IF the event payload is missing required fields or contains invalid values, THEN THE Intelligence_API SHALL return HTTP 422 with a JSON body listing each missing or invalid field.
5. IF the `store_id` in the event payload does not correspond to a registered store, THEN THE Intelligence_API SHALL return HTTP 404 with a descriptive error message.
6. THE Intelligence_API SHALL process each single-event `POST /events/ingest` request and return a response within 200 milliseconds when there is no concurrent load on the endpoint.
7. THE Intelligence_API SHALL support batch ingestion of up to 500 events in a single `POST /events/ingest` request; WHEN all events in the batch are valid and new, THE Intelligence_API SHALL return HTTP 201 with an array of persisted events; WHEN one or more events in the batch already exist by `event_id`, those events SHALL be treated as idempotent and included in the response without duplication.
8. WHEN a batch request contains one or more events that fail schema validation, THE Intelligence_API SHALL reject the entire batch atomically, return HTTP 422, and identify each failing event by its zero-based index in the request array along with the specific validation error.

---

### Requirement 5: Store Metrics API

**User Story:** As a store analyst, I want to query aggregated store metrics over any time window, so that I can measure performance and conversion rate.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `GET /stores/{id}/metrics` endpoint that accepts optional `start` and `end` query parameters in ISO 8601 UTC format to define the time window for aggregation.
2. WHEN `GET /stores/{id}/metrics` is called, THE Intelligence_API SHALL return a JSON response containing:
   - `unique_visitors`: the count of distinct `visitor_id` values with an `ENTRY` event in the time window
   - `conversion_rate`: a decimal between 0.0 and 1.0, calculated as `converted_visitors / unique_visitors`, returning 0.0 when `unique_visitors` is zero
   - `avg_dwell_per_zone`: an object mapping each `zone_id` to the average dwell time in seconds for visitors who entered that zone in the time window
   - `queue_depth`: the current count of visitors with an active `BILLING_QUEUE_JOIN` event and no subsequent `BILLING_QUEUE_ABANDON`, `EXIT`, or POS transaction at the time of the request
   - `abandonment_rate`: a decimal between 0.0 and 1.0, calculated as `BILLING_QUEUE_ABANDON events / BILLING_QUEUE_JOIN events`, returning 0.0 when there are no `BILLING_QUEUE_JOIN` events in the time window
   - `avg_visit_duration_seconds`: the average duration in seconds between `ENTRY` and `EXIT` events for completed visits in the time window
   - `peak_hour`: the calendar hour (integer 0–23) with the highest visitor entry count in the time window
3. WHEN `GET /stores/{id}/metrics` is called without `start` and `end` parameters, THE Intelligence_API SHALL default the time window to the current calendar day (00:00:00 to 23:59:59) in the store's configured timezone.
4. IF the specified store ID does not exist, THEN THE Intelligence_API SHALL return HTTP 404 with a descriptive error message.
5. THE Intelligence_API SHALL return a response to `GET /stores/{id}/metrics` within 500 milliseconds for time windows up to 30 days.

---

### Requirement 6: Customer Journey Funnel API

**User Story:** As a store analyst, I want to see how visitors progress through store zones toward purchase, so that I can identify drop-off points in the customer journey.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `GET /stores/{id}/funnel` endpoint that accepts optional `start` and `end` query parameters in ISO 8601 UTC format (maximum window of 90 days) to define the time window for funnel aggregation.
2. WHEN `GET /stores/{id}/funnel` is called, THE Intelligence_API SHALL return an ordered list of funnel stages, each containing `zone_id`, `zone_name`, `visitor_count`, `entry_rate` (the percentage of total unique visitors who entered this zone, expressed as a decimal between 0.0 and 1.0 rounded to four decimal places), and `avg_dwell_seconds`.
3. THE Intelligence_API SHALL order funnel stages by median visit sequence position across all Visitor tracks; WHERE two zones share the same median position, they SHALL be ordered alphabetically by `zone_name`.
4. WHEN `GET /stores/{id}/funnel` is called, THE Intelligence_API SHALL include a `conversion_funnel` sub-object showing the count of visitors at each stage who ultimately converted (i.e., whose visit record has `converted=true`).
5. IF no events exist for the specified store and time window, THEN THE Intelligence_API SHALL return HTTP 200 with an empty funnel list and a `data_available: false` flag.
6. IF the specified store ID does not exist, THEN THE Intelligence_API SHALL return HTTP 404 with a descriptive error message.

---

### Requirement 7: Spatial Heatmap API

**User Story:** As a store manager, I want a spatial heatmap of customer movement, so that I can optimise product placement and store layout.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `GET /stores/{id}/heatmap` endpoint that accepts optional `start` and `end` query parameters in ISO 8601 UTC format (maximum window of 90 days) to define the time window for density aggregation.
2. WHEN `GET /stores/{id}/heatmap` is called, THE Intelligence_API SHALL return a JSON response containing a `grid` array of cells, each with `x`, `y`, `width`, `height` (all in normalised 0.0–1.0 coordinates), and `density` (a float between 0.0 and 1.0 relative to the maximum cell count in the window).
3. THE Intelligence_API SHALL support a `resolution` query parameter accepting values `low` (10×10 grid), `medium` (20×20 grid), and `high` (40×40 grid), defaulting to `medium`.
4. WHEN `GET /stores/{id}/heatmap` is called with a `zone_id` query parameter, THE Intelligence_API SHALL restrict the heatmap to track positions within that zone's polygon.
5. THE Intelligence_API SHALL return a response to `GET /stores/{id}/heatmap` within 1 second for `low` and `medium` resolution requests and within 3 seconds for `high` resolution requests, for time windows up to 7 days.
6. IF the specified store ID does not exist or the specified `zone_id` does not belong to that store, THEN THE Intelligence_API SHALL return HTTP 404 with a descriptive error message.
7. WHEN `GET /stores/{id}/heatmap` is called for a time window in which no track positions were recorded, THE Intelligence_API SHALL return HTTP 200 with a `grid` array where all cells have `density: 0.0`.

---

### Requirement 8: Anomaly Detection API

**User Story:** As a store operator, I want to be alerted to unusual store conditions, so that I can take corrective action in real time.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `GET /stores/{id}/anomalies` endpoint that accepts optional `start` and `end` query parameters in ISO 8601 UTC format (maximum window of 24 hours, defaulting to the last 24 hours) to define the time window for anomaly retrieval.
2. WHEN `GET /stores/{id}/anomalies` is called, THE Intelligence_API SHALL return a list of up to 500 anomaly records ordered by `detected_at` descending, each containing `anomaly_id`, `anomaly_type`, `detected_at`, `severity` (`low`, `medium`, or `high`), `description`, and `affected_zone_id` (nullable).
3. THE Intelligence_API SHALL detect and classify the following anomaly types with the specified severities: `QUEUE_BUILDUP` (`high`) when billing queue depth exceeds 5 persons for more than 3 minutes; `EMPTY_STORE` (`medium`) when zero visitors are detected for more than 10 minutes during operating hours; `UNUSUAL_DWELL` (`low`) when a visitor dwells in a single zone for more than 15 minutes; and `CAMERA_OVERLAP_CONFLICT` (`high`) when the same track ID is simultaneously active in two non-adjacent camera zones.
4. WHEN a `QUEUE_BUILDUP` anomaly is detected, THE Intelligence_API SHALL set severity to `high` and include the current queue depth in the description.
5. IF no anomalies are detected for the specified store and time window, THEN THE Intelligence_API SHALL return HTTP 200 with an empty list.
6. IF the specified store ID does not exist, THEN THE Intelligence_API SHALL return HTTP 404 with a descriptive error message.
7. IF the `start` or `end` query parameter is malformed or `start` is after `end`, THEN THE Intelligence_API SHALL return HTTP 400 with a descriptive error message.

---

### Requirement 9: Real-Time Event Push via WebSocket

**User Story:** As a dashboard user, I want to receive store events in real time without polling, so that the dashboard reflects current store conditions instantly.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a WebSocket endpoint at `ws://{host}/ws/stores/{id}/events`; WHEN a client attempts to connect with an unknown store `{id}`, THE Intelligence_API SHALL reject the connection with WebSocket close code 4004 and a descriptive reason string.
2. WHEN a new event is persisted for a store, THE Intelligence_API SHALL push the event as a JSON message to all active WebSocket connections for that store within 200 milliseconds of persistence under normal load, and within 500 milliseconds under maximum concurrent load (50 connections per store).
3. WHEN a WebSocket client connects to a valid store endpoint, THE Intelligence_API SHALL send the last 50 events for the store as an initial state payload before streaming new events.
4. WHEN a WebSocket connection is closed by the client, THE Intelligence_API SHALL release all resources associated with that connection without affecting other active connections.
5. IF a WebSocket client does not send a WebSocket protocol-level ping frame within 60 seconds, THEN THE Intelligence_API SHALL close the connection with WebSocket close code 1001.
6. THE Intelligence_API SHALL support at least 50 concurrent WebSocket connections per store.
7. IF the Intelligence_API encounters an internal error while pushing an event to a WebSocket connection, THEN THE Intelligence_API SHALL close that connection with WebSocket close code 1011 and log the error, without affecting other active connections.

---

### Requirement 10: Real-Time Dashboard

**User Story:** As a store manager, I want a live dashboard showing key store metrics and events, so that I can monitor store performance at a glance.

#### Acceptance Criteria

1. THE Dashboard SHALL display a live **Overview Screen** showing: current visitor count, today's conversion rate, average dwell time, and queue depth — all updating within 500 milliseconds of a new WebSocket event being received.
2. THE Dashboard SHALL display a **Funnel Screen** showing the customer journey funnel chart with zone-level visitor counts and drop-off rates, refreshing every 30 seconds via the `GET /stores/{id}/funnel` endpoint.
3. THE Dashboard SHALL display a **Heatmap Screen** showing the spatial heatmap of the store floor overlaid on the store layout image at the correct scale and position, with a time-window selector offering at least the options: last 1 hour, last 4 hours, and today.
4. THE Dashboard SHALL display an **Anomalies Screen** showing a list of active and recent anomalies with severity badges coloured red for `high`, amber for `medium`, and grey for `low`, auto-refreshing every 60 seconds.
5. THE Dashboard SHALL display a **Live Event Feed** panel showing the last 20 events in reverse chronological order, updating within 500 milliseconds of a new WebSocket event being received.
6. WHEN the WebSocket connection is lost, THE Dashboard SHALL display a visible reconnection indicator within 1 second and attempt to reconnect with exponential backoff (1s, 2s, 4s, 8s, 16s) up to 5 attempts before showing a manual retry button.
7. THE Dashboard SHALL render all screens without horizontal scrollbars or overlapping elements on viewport widths from 1280px to 2560px.
8. WHEN a store is selected from the store selector, THE Dashboard SHALL display populated data on all screens within 2 seconds, measured from the moment the selection is confirmed to the moment all API responses are rendered.

---

### Requirement 11: POS Transaction Correlation

**User Story:** As a store analyst, I want POS transactions linked to visitor tracks, so that conversion rate is calculated accurately.

#### Acceptance Criteria

1. THE Intelligence_API SHALL accept POS transaction records via `POST /stores/{id}/transactions` containing `transaction_id`, `timestamp`, `amount`, and optional `visitor_id`.
2. WHEN a POS transaction is received without a `visitor_id`, THE Intelligence_API SHALL attempt to correlate it with the Visitor whose `visitor_id` was in the billing queue zone closest in time to the transaction timestamp within a 120-second window; IF multiple visitors are equidistant in time, THE Intelligence_API SHALL mark the transaction as `unmatched`.
3. WHEN a POS transaction is successfully correlated with a Visitor, THE Intelligence_API SHALL mark that Visitor's record as `converted=true` and include it in conversion rate calculations.
4. IF a POS transaction cannot be correlated with any Visitor, THEN THE Intelligence_API SHALL persist the transaction as `unmatched` and include it in an `unmatched_transactions` count in the metrics response.
5. THE Intelligence_API SHALL ensure that a single Visitor is not counted as more than one conversion within a single store visit, defined as the period from the Visitor's `ENTRY` event timestamp to their `EXIT` event timestamp or session expiry.
6. IF a POS transaction `timestamp` is more than 24 hours in the past or is in the future relative to the server's current time, THEN THE Intelligence_API SHALL reject the transaction with HTTP 422 and a descriptive error message.

---

### Requirement 12: Health and Observability

**User Story:** As a DevOps engineer, I want a health endpoint and structured logs, so that I can monitor platform health and diagnose issues quickly.

#### Acceptance Criteria

1. THE Intelligence_API SHALL expose a `GET /health` endpoint that returns a response within 2 seconds containing a JSON body with `status` (`"healthy"` or `"degraded"`), `version`, `uptime_seconds`, and the health status of each subsystem (`database`, `detection_pipeline`, `event_engine`), each with a value of `"healthy"` or `"unhealthy"`.
2. IF any subsystem's active health probe fails at the time of the request, THEN THE Intelligence_API SHALL return HTTP 503 with `status: "degraded"` and the affected subsystem's field set to `"unhealthy"`; all healthy subsystems SHALL retain `"healthy"`.
3. THE Intelligence_API SHALL emit structured JSON log lines for every HTTP request containing: `timestamp`, `method`, `path`, `status_code`, `duration_ms`, and `request_id`.
4. THE Detection_Pipeline SHALL emit structured JSON log lines for every processed frame containing: `timestamp`, `camera_id`, `frame_id`, `persons_detected`, `tracks_active`, and `processing_ms`.
5. THE Event_Engine SHALL emit structured JSON log lines for every emitted event containing: `timestamp`, `event_type`, `visitor_id`, `store_id`, and `latency_ms`.
6. THE Intelligence_API SHALL assign a UUID v4 `request_id` to every inbound HTTP request, unique within the process lifetime, and propagate it through all log lines generated during that request's processing.
7. WHEN `GET /health` is called, THE Intelligence_API SHALL perform a live probe of each subsystem at request time and SHALL NOT return cached health state from a previous probe.

---

### Requirement 13: Containerised Deployment

**User Story:** As a reviewer, I want to run the entire platform with a single command, so that I can evaluate it without complex environment setup.

#### Acceptance Criteria

1. THE ReIntellect platform SHALL be deployable using `docker compose up` from the repository root without any manual pre-configuration beyond copying a `.env.example` file to `.env`.
2. THE Docker_Compose configuration SHALL define the following services: `detection-pipeline`, `event-engine`, `intelligence-api`, `dashboard`, and `db-init`.
3. WHEN `docker compose up` is executed, THE ReIntellect platform SHALL have all services passing their Docker health checks and the Dashboard returning HTTP 200 at `http://localhost:3000` within 60 seconds on a machine with a 4-core CPU and 8 GB RAM.
4. THE Docker_Compose configuration SHALL define named volumes for SQLite database persistence so that data survives container restarts.
5. WHERE a CUDA-capable GPU device is visible to the container runtime, THE Detection_Pipeline SHALL use CUDA for inference; WHERE no such device is available, THE Detection_Pipeline SHALL fall back to CPU processing automatically without requiring configuration changes.
6. THE Docker_Compose configuration SHALL expose only the ports required for external access: `8000` for the Intelligence_API and `3000` for the Dashboard.
7. IF the `.env` file is absent when `docker compose up` is executed, THEN the platform SHALL fail with a descriptive error message before starting any service.

---

### Requirement 14: Testing Strategy

**User Story:** As a reviewer, I want a comprehensive test suite, so that I can verify the platform's correctness and robustness.

#### Acceptance Criteria

1. THE ReIntellect platform SHALL include a Pytest test suite with: unit tests covering the Event_Engine's classification logic for all 8 event types; integration tests covering all 6 Intelligence_API endpoints (POST /events/ingest, GET /stores/{id}/metrics, GET /stores/{id}/funnel, GET /stores/{id}/heatmap, GET /stores/{id}/anomalies, GET /health); and property-based tests covering event schema round-trip validation and POS correlation logic.
2. WHEN the test suite is executed with `pytest`, THE ReIntellect platform SHALL produce a test report showing at least 80% line coverage across the `event_engine` and `intelligence_api` modules.
3. THE test suite SHALL include property-based tests verifying that FOR ALL event payloads accepted without a validation error, serialising the payload to JSON and deserialising it back produces an object where all fields are equal by value and type to the original.
4. THE test suite SHALL include property-based tests verifying that FOR ALL sequences of ENTRY and EXIT events for a given `visitor_id`, the computed visit duration is always non-negative.
5. THE test suite SHALL include integration tests for each of the six required edge cases — group entry, staff movement, re-entry, partial occlusion, queue buildup, and empty store periods — where each test asserts on a specific, named observable outcome (a metric field value or API response field) that confirms the edge case is handled correctly.
6. THE test suite SHALL include a smoke test that starts the full Docker_Compose stack and asserts that `GET /health` returns HTTP 200 within 30 seconds; IF the 30-second deadline elapses without HTTP 200, the smoke test SHALL fail with a descriptive timeout message.

---

### Requirement 15: Event Schema Integrity

**User Story:** As an integration developer, I want all events to conform to a strict schema, so that downstream consumers can rely on a stable contract.

#### Acceptance Criteria

1. THE Event_Engine SHALL produce events conforming to a canonical JSON schema that includes: `event_id` (UUID v4, supplied by the client/pipeline — not generated by the server), `event_type` (one of: `ENTRY`, `EXIT`, `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, `BILLING_QUEUE_ABANDON`, `REENTRY`), `store_id` (string), `visitor_id` (string — the stable business-level identifier assigned at entry confirmation, distinct from the internal ByteTrack `track_id`), `timestamp` (ISO 8601 UTC), `camera_id` (string), and an `attributes` object for event-type-specific fields.
2. WHEN an event is submitted to `POST /events/ingest`, THE Intelligence_API SHALL validate it against the canonical event schema before writing to SQLite.
3. IF an event fails schema validation, THEN THE Intelligence_API SHALL reject it with HTTP 422, log the validation error with the full payload, and SHALL NOT write the event to SQLite.
4. THE Intelligence_API SHALL expose a `GET /schema/events` endpoint that returns the canonical event JSON schema document with `Content-Type: application/schema+json`, enabling client-side validation.
5. FOR ALL valid event objects (those accepted without a validation error), serialising the object to JSON and deserialising it back SHALL produce an object where every field is equal to the original by value and type (round-trip property).

---

### Requirement 16: Camera Overlap and Re-entry Handling

**User Story:** As a store analyst, I want the platform to correctly handle persons moving between overlapping camera zones and returning to the store, so that visitor counts are not inflated.

#### Acceptance Criteria

1. WHEN a Track exits one camera's coverage polygon and enters an adjacent camera's coverage polygon (where "adjacent" means the two polygons share an edge or overlapping area) within 10 seconds, THE Detection_Pipeline SHALL merge the two track segments under the original track ID; IF the original track record is already closed, THE Detection_Pipeline SHALL log a merge conflict and create a new track ID.
2. WHEN a Track that has emitted an `EXIT` event re-enters the designated entry coverage polygon within 300 seconds, THE Event_Engine SHALL emit a `REENTRY` event carrying the same `visitor_id` as the original `ENTRY` event, extend the existing visit record's duration, and retain the original visit ID rather than creating a new Visitor record.
3. WHEN a Track that has emitted an `EXIT` event re-enters the designated entry coverage polygon after 300 seconds, THE Event_Engine SHALL assign a new `visitor_id`, emit a new `ENTRY` event, and create a new Visitor record with a new visit ID.
4. THE Intelligence_API SHALL count `unique_visitors` as the number of distinct Visitor record IDs, excluding Visitor records that were continued by a `REENTRY` event within 300 seconds, so that re-entries within 300 seconds do not inflate the visitor count.
5. WHEN camera overlap is detected for a Visitor (simultaneous active detections in two non-adjacent zones within a 2-second observation window), THE Event_Engine SHALL emit a `CAMERA_OVERLAP_CONFLICT` anomaly event and use the detection with the higher confidence score as the authoritative position; IF both detections have equal confidence scores, THE Event_Engine SHALL use the detection with the earlier timestamp as the authoritative position.
