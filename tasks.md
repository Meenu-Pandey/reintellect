# Implementation Plan: ReIntellect AI-Powered Store Intelligence Platform

## Overview

This plan breaks the ReIntellect platform into 10 sequential phases, each decomposed into small, independently-completable coding tasks (≤ 30 minutes each). Every task references the specific requirements it satisfies. The backend is a monolithic Python process (DetectionPipeline + EventEngine + FastAPI) communicating via `asyncio.Queue`. The frontend is a React + Vite SPA. Deployment uses Docker Compose with three services: `db-init`, `backend`, `frontend`.

---

## Tasks

- [ ] 1. Phase 1: Project Scaffolding
  - [x] 1.1 Initialise backend Python package structure
    - Create the directory tree: `backend/detection/`, `backend/engine/`, `backend/api/routers/`, `backend/api/websocket/`, `backend/db/migrations/`, `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/property/`, `backend/tests/smoke/`
    - Add `__init__.py` to every package directory
    - Acceptance criteria: `python -c "import detection; import engine; import api; import db"` succeeds from `backend/`
    - _Requirements: 13.1_
    - Depends on: none

  - [ ] 1.2 Create `pyproject.toml` with pinned dependencies
    - Add dependencies: `fastapi==0.111.*`, `uvicorn[standard]==0.29.*`, `ultralytics==8.2.*`, `aiosqlite==0.20.*`, `hypothesis==6.100.*`, `pytest==8.2.*`, `pytest-asyncio==0.23.*`, `pytest-cov==5.*`, `httpx==0.27.*`, `opencv-python-headless==4.9.*`, `torch>=2.2,<3`, `shapely==2.0.*`
    - Add `[tool.pytest.ini_options]` section: `asyncio_mode = "auto"`, `testpaths = ["tests"]`
    - Acceptance criteria: `pip install -e .` completes without errors
    - _Requirements: 13.1, 14.1_
    - Depends on: 1.1

  - [ ] 1.3 Create `backend/main.py` application entrypoint skeleton
    - Define `create_app()` factory that returns a FastAPI instance with a `lifespan` context manager
    - Lifespan stub: open aiosqlite connection, create two `asyncio.Queue` instances (`track_queue`, `event_queue`), log startup, yield, log shutdown
    - Acceptance criteria: `uvicorn main:app --port 8000` starts without import errors
    - _Requirements: 12.1, 13.1_
    - Depends on: 1.2

  - [ ] 1.4 Initialise frontend Vite + React + TypeScript project
    - Run `npm create vite@latest frontend -- --template react-ts` (or scaffold manually)
    - Install dependencies: `recharts@2.*`, `zustand@4.*`, `@tanstack/react-query@5.*`, `axios@1.*`
    - Configure `vite.config.ts`: set `server.proxy` to forward `/api` and `/ws` to `http://localhost:8000`
    - Acceptance criteria: `npm run build` in `frontend/` exits 0 with no TypeScript errors
    - _Requirements: 10.1, 13.1_
    - Depends on: none

  - [ ] 1.5 Create `.env.example` and root `docker-compose.yml` skeleton
    - `.env.example`: define `VIDEO_SOURCE=demo`, `CUDA_VISIBLE_DEVICES=`, `LOG_LEVEL=INFO`, `STORE_TIMEZONE=Asia/Kolkata`
    - `docker-compose.yml`: declare three services (`db-init`, `backend`, `frontend`) and named volume `reintellect_db`; leave `command` and `build` stubs
    - Acceptance criteria: `docker compose config` validates without errors
    - _Requirements: 13.1, 13.4, 13.6, 13.7_
    - Depends on: none

- [ ] 2. Phase 2: Dataset Analysis
  - [ ] 2.1 Create detection data models (`backend/detection/models.py`)
    - Define `TrackDetection` dataclass: `track_id: int`, `bbox: tuple[float, float, float, float]`, `confidence: float`, `role: Literal["visitor", "staff"]`
    - Define `TrackFrame` dataclass: `camera_id: str`, `frame_id: int`, `timestamp: datetime`, `detections: list[TrackDetection]`
    - All fields must be typed; add `__post_init__` validation that `confidence` is in [0.0, 1.0] and bbox values are in [0.0, 1.0]
    - Acceptance criteria: instantiating both dataclasses with valid data succeeds; invalid confidence raises `ValueError`
    - _Requirements: 1.1, 1.2_
    - Depends on: 1.1

  - [ ] 2.2 Create engine event models (`backend/engine/models.py`)
    - Define `Event` dataclass with fields: `event_id: str` (UUID v4), `event_type: str` (one of 8 valid types), `store_id: str`, `visitor_id: str`, `timestamp: datetime`, `camera_id: str`, `attributes: dict`
    - Add `EVENT_TYPES` constant: `frozenset` of the 8 valid event type strings
    - Add `to_dict()` method that serialises all fields to a JSON-compatible dict (datetime → ISO 8601 string)
    - Add `from_dict()` classmethod that deserialises from a dict and validates required fields
    - Acceptance criteria: `Event.from_dict(event.to_dict())` produces an equal object for all valid event types
    - _Requirements: 15.1, 15.5_
    - Depends on: 1.1

  - [ ] 2.3 Write property test for Event schema round-trip (Property 1)
    - File: `backend/tests/property/test_event_schema_roundtrip.py`
    - Use `hypothesis.strategies` to generate valid `Event` dicts covering all 8 event types with valid UUIDs, ISO 8601 timestamps, and type-appropriate attributes
    - Assert `Event.from_dict(event.to_dict()) == original_event` for all generated events
    - Tag: `# Property 1: Event Schema Round-Trip — Validates: Requirements 14.3, 15.5`
    - Acceptance criteria: `pytest tests/property/test_event_schema_roundtrip.py` passes with ≥ 100 examples
    - _Requirements: 14.3, 15.5_
    - Depends on: 2.2

  - [ ] 2.4 Bundle a demo video clip for offline testing
    - Add a short (≥ 30s) royalty-free retail CCTV-style video as `backend/tests/fixtures/demo_clip.mp4`
    - Create `backend/detection/demo_source.py` with a `DemoVideoSource` class that loops the clip indefinitely using `cv2.VideoCapture`
    - Acceptance criteria: `DemoVideoSource` yields at least 10 frames per second; looping restarts without error
    - _Requirements: 1.6, 13.1_
    - Depends on: 1.2

- [ ] 3. Phase 3: YOLOv8 + ByteTrack Pipeline
  - [ ] 3.1 Implement ByteTrack wrapper (`backend/detection/tracker.py`)
    - Create `ByteTrackWrapper` class that wraps the ByteTrack implementation from `ultralytics`
    - Expose `update(detections: list[dict]) -> list[dict]` method that accepts raw YOLO detections and returns tracked detections with `track_id` assigned
    - Configure re-association window: lost tracks re-associated if absent < 30 frames; new `track_id` after ≥ 30 frames
    - Acceptance criteria: two detections in the same position across 5 frames receive the same `track_id`; a detection absent for 31 frames receives a new `track_id`
    - _Requirements: 1.2, 1.3_
    - Depends on: 2.1

  - [ ] 3.2 Implement staff filter (`backend/detection/staff_filter.py`)
    - Create `StaffFilter` class with `classify(bbox: tuple, frame: np.ndarray, config: dict) -> Literal["visitor", "staff"]` method
    - Implement heuristic: check if the bounding box region contains a high proportion of a configured staff colour (HSV range from config); return `"staff"` if threshold exceeded, else `"visitor"`
    - Accept staff colour config as a dict with `hsv_lower` and `hsv_upper` keys
    - Acceptance criteria: a bbox region filled with the configured staff colour returns `"staff"`; a region without it returns `"visitor"`
    - _Requirements: 1.5_
    - Depends on: 2.1

  - [ ] 3.3 Implement `DetectionPipeline` class (`backend/detection/pipeline.py`)
    - Create `DetectionPipeline` with `__init__(video_source, track_queue: asyncio.Queue, config: dict)`
    - Implement `async run()` method: read frames from video source, run YOLOv8n inference (person class only, confidence ≥ 0.5, bbox height ≥ 50px), apply ByteTrack, apply staff filter, assemble `TrackFrame`, put onto `track_queue`
    - Use `torch.cuda.is_available()` to select device; log selected device at startup
    - On camera feed loss: log interruption with timestamp, poll for reconnect every 2s, preserve active track state
    - Acceptance criteria: pipeline processes ≥ 10 frames/second on CPU with the demo clip; detections below threshold are absent from `TrackFrame.detections`
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7, 1.8, 13.5_
    - Depends on: 3.1, 3.2, 2.4

  - [ ]* 3.4 Write property test for detection threshold filtering (Property 3)
    - File: `backend/tests/property/test_event_schema_roundtrip.py` (add to existing file)
    - Use Hypothesis to generate lists of detections with random confidence scores and bbox heights
    - Assert that after pipeline filtering, all remaining detections have `confidence >= 0.5` AND `bbox_height >= 50`
    - Tag: `# Property 3: Detection Threshold Filtering — Validates: Requirements 1.1, 1.8`
    - Acceptance criteria: test passes with ≥ 100 examples
    - _Requirements: 1.1, 1.8_
    - Depends on: 3.3

  - [ ]* 3.5 Write property test for staff exclusion invariant (Property 4)
    - File: `backend/tests/property/test_event_schema_roundtrip.py` (add to existing file)
    - Use Hypothesis to generate mixed detection sets with some tagged `role=staff`
    - Assert that no staff-tagged detection appears in the output `TrackFrame.detections` list
    - Tag: `# Property 4: Staff Exclusion Invariant — Validates: Requirements 1.5`
    - Acceptance criteria: test passes with ≥ 100 examples
    - _Requirements: 1.5_
    - Depends on: 3.3

  - [ ] 3.6 Wire `DetectionPipeline` into `main.py` lifespan
    - In `main.py` lifespan: instantiate `DetectionPipeline` with `track_queue` and config from environment; start it as an `asyncio.create_task(pipeline.run())`
    - Log pipeline task start and handle `CancelledError` on shutdown
    - Acceptance criteria: `uvicorn main:app` starts and logs "DetectionPipeline started"; no unhandled exceptions on shutdown
    - _Requirements: 1.6, 12.4_
    - Depends on: 3.3, 1.3

- [ ] 4. Phase 4: Event Engine
  - [ ] 4.1 Implement `VisitorRegistry` (`backend/engine/visitor_registry.py`)
    - Create `VisitorRegistry` class with in-memory dict `_track_to_visitor: dict[int, str]` and `_exit_times: dict[str, datetime]`
    - Implement `get_or_assign(track_id: int, entry_time: datetime) -> str`: returns existing `visitor_id` if track is known; assigns new UUID v4 `visitor_id` otherwise
    - Implement `record_exit(visitor_id: str, exit_time: datetime)` and `handle_reentry(track_id: int, reentry_time: datetime) -> tuple[str, float]`: returns `(visitor_id, gap_seconds)`; reuses original `visitor_id` if gap < 300s, assigns new one if gap ≥ 300s
    - Implement `merge_camera_handoff(old_track_id: int, new_track_id: int, gap_seconds: float)`: merges track segments if gap ≤ 10s
    - Acceptance criteria: re-entry at 299s returns same `visitor_id`; re-entry at 300s returns new `visitor_id`
    - _Requirements: 2.1, 2.8, 16.1, 16.2, 16.3_
    - Depends on: 2.2

  - [ ] 4.2 Implement `ZoneTracker` (`backend/engine/zone_tracker.py`)
    - Create `ZoneTracker` class with state machine per visitor: `OUTSIDE → IN_ZONE → DWELL_EMITTED`
    - Implement `update(visitor_id: str, bbox_centroid: tuple[float, float], timestamp: datetime, zones: list[dict]) -> list[Event]`: uses `shapely.geometry.Point.within(Polygon)` for zone containment; emits `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL` events
    - `ZONE_DWELL` emitted when continuous dwell ≥ 30s; `dwell_seconds` field ≥ 30
    - On track loss (called with `track_lost=True`): emit `ZONE_EXIT` with last known timestamp and accumulated dwell
    - Acceptance criteria: 29s dwell emits no `ZONE_DWELL`; 30s dwell emits exactly one `ZONE_DWELL` with `dwell_seconds >= 30`
    - _Requirements: 2.3, 2.4, 2.5, 2.11_
    - Depends on: 2.2

  - [ ]* 4.3 Write property test for zone dwell threshold (Property 5)
    - File: `backend/tests/property/test_visit_duration.py`
    - Use Hypothesis to generate dwell durations (floats ≥ 0); assert `ZONE_DWELL` is emitted iff duration ≥ 30s and `dwell_seconds >= 30`
    - Tag: `# Property 5: Zone Dwell Threshold — Validates: Requirements 2.5`
    - Acceptance criteria: test passes with ≥ 100 examples
    - _Requirements: 2.5_
    - Depends on: 4.2

  - [ ] 4.4 Implement `QueueTracker` (`backend/engine/queue_tracker.py`)
    - Create `QueueTracker` class with `_queue_members: dict[str, datetime]` (visitor_id → join_time) and `_depth: int`
    - Implement `join(visitor_id: str, timestamp: datetime) -> Event`: emits `BILLING_QUEUE_JOIN` with `queue_position = _depth + 1`; increments `_depth`
    - Implement `check_abandon(visitor_id: str, exit_time: datetime, pos_transactions: list) -> Event | None`: emits `BILLING_QUEUE_ABANDON` if no POS transaction linked to `visitor_id` within 120s of join time; decrements `_depth`
    - Implement `get_depth() -> int` returning current live queue depth
    - Acceptance criteria: first joiner gets `queue_position=1`; second joiner gets `queue_position=2`; abandon emitted when no POS within 120s
    - _Requirements: 2.6, 2.7_
    - Depends on: 2.2

  - [ ]* 4.5 Write property test for queue position monotonicity (Property 7)
    - File: `backend/tests/property/test_visit_duration.py` (add to existing file)
    - Use Hypothesis to generate sequences of queue join events; assert each `queue_position = prior_depth + 1` and `queue_position >= 1`
    - Tag: `# Property 7: Queue Position Monotonicity — Validates: Requirements 2.6`
    - Acceptance criteria: test passes with ≥ 100 examples
    - _Requirements: 2.6_
    - Depends on: 4.4

  - [ ] 4.6 Implement `AnomalyDetector` (`backend/engine/anomaly_detector.py`)
    - Create `AnomalyDetector` class with methods for each anomaly type
    - `check_queue_buildup(depth: int, duration_seconds: float, zone_id: str) -> Anomaly | None`: triggers when `depth > 5` for `> 180s`; severity `high`
    - `check_empty_store(visitor_count: int, duration_seconds: float) -> Anomaly | None`: triggers when `visitor_count == 0` for `> 600s` during operating hours; severity `medium`
    - `check_unusual_dwell(visitor_id: str, zone_id: str, dwell_seconds: float) -> Anomaly | None`: triggers when `dwell_seconds > 900`; severity `low`
    - `check_camera_overlap(track_id: int, zone_a: str, zone_b: str, gap_seconds: float, adjacency_map: dict) -> Anomaly | None`: triggers when same track in two non-adjacent zones within 2s; severity `high`
    - Acceptance criteria: each method returns `None` below threshold and an `Anomaly` object above threshold
    - _Requirements: 8.3, 8.4_
    - Depends on: 2.2

  - [ ] 4.7 Implement `EventEngine` orchestrator (`backend/engine/event_engine.py`)
    - Create `EventEngine` with `__init__(track_queue: asyncio.Queue, event_queue: asyncio.Queue, store_layout: dict)`
    - Implement `async run()`: consume `TrackFrame` from `track_queue`; for each visitor detection, call `VisitorRegistry`, `ZoneTracker`, `QueueTracker`; put emitted `Event` objects onto `event_queue`
    - Implement entry/exit boundary crossing detection using `shapely` polygon containment on bbox centroid
    - Emit `ENTRY` on inward boundary crossing; emit `EXIT` on outward crossing with no re-entry within 60s; emit `REENTRY` if re-entry within 300s
    - Log each emitted event with `event_type`, `visitor_id`, `store_id`, `latency_ms`
    - Acceptance criteria: a `TrackFrame` with a centroid crossing the entry zone boundary inward produces an `ENTRY` event on `event_queue` within 500ms
    - _Requirements: 2.1, 2.2, 2.9, 12.5_
    - Depends on: 4.1, 4.2, 4.4, 4.6

  - [ ]* 4.8 Write unit tests for `EventEngine` classification logic
    - File: `backend/tests/unit/test_event_engine.py`
    - Write one test per event type (8 tests): ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL, BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY
    - Each test constructs a minimal `TrackFrame` sequence and asserts the correct event type is emitted
    - Acceptance criteria: all 8 tests pass; no external I/O required (use in-memory queues)
    - _Requirements: 14.1_
    - Depends on: 4.7

  - [ ]* 4.9 Write unit tests for `ZoneTracker` state machine
    - File: `backend/tests/unit/test_zone_tracker.py`
    - Test: OUTSIDE→IN_ZONE transition, IN_ZONE→DWELL_EMITTED at 30s, DWELL_EMITTED→OUTSIDE on exit, track-loss ZONE_EXIT
    - Acceptance criteria: all state transitions produce correct events; track-loss emits ZONE_EXIT with accumulated dwell
    - _Requirements: 14.1_
    - Depends on: 4.2

  - [ ]* 4.10 Write unit tests for `VisitorRegistry`
    - File: `backend/tests/unit/test_visitor_registry.py`
    - Test: new visitor assignment, re-entry at 299s (same ID), re-entry at 300s (new ID), camera handoff within 10s
    - Acceptance criteria: all 4 scenarios produce correct `visitor_id` values
    - _Requirements: 14.1_
    - Depends on: 4.1

  - [ ]* 4.11 Write unit tests for `QueueTracker`
    - File: `backend/tests/unit/test_queue_tracker.py`
    - Test: queue depth increments on join, `queue_position` is correct, abandon emitted at 121s without POS, no abandon when POS present within 120s
    - Acceptance criteria: all 4 scenarios pass
    - _Requirements: 14.1_
    - Depends on: 4.4

  - [ ] 4.12 Wire `EventEngine` into `main.py` lifespan
    - In `main.py` lifespan: instantiate `EventEngine` with `track_queue`, `event_queue`, and store layout loaded from DB; start as `asyncio.create_task(engine.run())`
    - Handle `CancelledError` on shutdown; log engine task start
    - Acceptance criteria: `uvicorn main:app` logs "EventEngine started"; events flow from `track_queue` to `event_queue`
    - _Requirements: 2.9, 12.5_
    - Depends on: 4.7, 3.6

- [ ] 5. Phase 5: SQLite Persistence
  - [ ] 5.1 Write SQLite DDL schema (`backend/db/schema.sql` and `backend/db/migrations/001_initial.sql`)
    - Define all tables: `stores`, `zones`, `cameras`, `visitors`, `visits`, `events`, `track_positions`, `pos_transactions`, `anomalies`
    - Include all `CHECK` constraints, foreign keys with `ON DELETE CASCADE`, and all indexes from the design
    - Enable WAL mode: `PRAGMA journal_mode=WAL;`
    - Acceptance criteria: `sqlite3 test.db < schema.sql` executes without errors; all tables and indexes are created
    - _Requirements: 5.1, 5.2, 7.2, 8.2_
    - Depends on: 1.1

  - [ ] 5.2 Implement aiosqlite connection manager (`backend/db/database.py`)
    - Create `Database` class with `async connect(db_path: str)`, `async close()`, and `async execute(sql, params)` / `async fetchall(sql, params)` / `async fetchone(sql, params)` methods
    - Implement `async upsert_event(event: Event)`: `INSERT OR IGNORE INTO events` (idempotent by `event_id`); also upsert `visitors` and `visits` records
    - Implement `async upsert_store(layout: dict)`: insert or replace `stores`, `zones`, `cameras` records
    - Enable WAL mode on connection open
    - Acceptance criteria: two calls to `upsert_event` with the same `event_id` result in exactly one row in `events`
    - _Requirements: 4.2, 4.3, 3.4_
    - Depends on: 5.1

  - [ ] 5.3 Implement `db-init` schema migration script (`backend/db/init_schema.py`)
    - Create `async main()` that opens the DB at `DB_PATH`, runs `001_initial.sql`, seeds a demo store layout (one entry zone, two floor zones, one billing_queue zone), then exits 0
    - Acceptance criteria: running `python -m db.init_schema` creates `reintellect.db` with all tables and the demo store row
    - _Requirements: 13.1, 13.4_
    - Depends on: 5.2

  - [ ] 5.4 Implement `event_consumer` task and wire into `main.py`
    - Create `async event_consumer(event_queue: asyncio.Queue, db: Database, ws_manager)` function
    - Loop: `event = await event_queue.get()` → `await db.upsert_event(event)` → `await ws_manager.broadcast(event)`
    - On DB failure: retry 3× with exponential backoff (1s, 2s, 4s); log full payload on final failure
    - Start as `asyncio.create_task` in `main.py` lifespan
    - Acceptance criteria: an event placed on `event_queue` appears in the `events` table within 2s; duplicate `event_id` does not create a second row
    - _Requirements: 2.10, 4.2, 4.3_
    - Depends on: 5.2, 1.3

- [ ] 6. Phase 6: FastAPI APIs
  - [ ] 6.1 Create FastAPI app factory and middleware (`backend/api/app.py`)
    - Create `create_app(db: Database, event_queue: asyncio.Queue, ws_manager) -> FastAPI`
    - Register `CORSMiddleware` (allow frontend origin from env), `RequestIDMiddleware` (UUID v4 per request stored in `contextvars.ContextVar`), `StructuredLoggingMiddleware` (JSON log per request with `timestamp`, `method`, `path`, `status_code`, `duration_ms`, `request_id`)
    - Include all routers (stub imports for now)
    - Acceptance criteria: `GET /docs` returns 200; request logs contain `request_id` field
    - _Requirements: 12.3, 12.6_
    - Depends on: 5.2, 1.3

  - [ ] 6.2 Implement `GET /health` endpoint (`backend/api/routers/health.py`)
    - Return JSON: `status`, `version`, `uptime_seconds`, `database` health, `detection_pipeline` health, `event_engine` health
    - Perform live probe at request time: DB probe = `SELECT 1`; pipeline/engine probe = check asyncio task is running
    - Return HTTP 503 if any subsystem probe fails; set that subsystem's field to `"unhealthy"`
    - Acceptance criteria: returns 200 with all subsystems healthy when running; returns 503 with `status: "degraded"` when DB is unavailable
    - _Requirements: 12.1, 12.2, 12.7_
    - Depends on: 6.1

  - [ ] 6.3 Implement `GET /schema/events` endpoint (`backend/api/routers/schema.py`)
    - Return the canonical event JSON schema document as defined in the design
    - Set `Content-Type: application/schema+json`
    - Acceptance criteria: `GET /schema/events` returns 200 with valid JSON Schema containing all 8 event types
    - _Requirements: 15.4_
    - Depends on: 6.1

  - [ ] 6.4 Implement `POST /stores` layout endpoint (`backend/api/routers/stores.py`)
    - Accept JSON body with `store_id`, `name`, `timezone`, `zones` list, `cameras` list
    - Validate: all polygons closed, non-self-intersecting, ≥ 3 vertices, coordinates in [0.0, 1.0]; `zone_type` in allowed set; no camera references unknown `zone_id`
    - On validation failure: return HTTP 422 identifying each failing element
    - On success: upsert via `db.upsert_store()`; return HTTP 200 with persisted layout
    - Acceptance criteria: valid layout returns 200; polygon with 2 vertices returns 422; overlapping zones return 422
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
    - Depends on: 6.1, 5.2

  - [ ] 6.5 Implement `POST /stores/{id}/transactions` endpoint (`backend/api/routers/stores.py`)
    - Accept JSON body with `transaction_id`, `timestamp`, `amount`, optional `visitor_id`
    - Validate: `timestamp` not > 24h in past or in future; return HTTP 422 otherwise
    - If no `visitor_id`: query `billing_queue` zone events within 120s window; correlate to closest visitor; mark `converted=true`; if tie, mark `unmatched`
    - If `visitor_id` provided: mark that visitor `converted=true`
    - Ensure single visitor not counted as more than one conversion per visit
    - Acceptance criteria: transaction with valid `visitor_id` sets `converted=true`; timestamp 25h in past returns 422
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
    - Depends on: 6.4, 5.2

  - [ ] 6.6 Implement `POST /events/ingest` endpoint (`backend/api/routers/events.py`)
    - Accept single event or array of up to 500 events
    - Single event: validate against canonical schema; if valid and new → persist + return 201; if duplicate `event_id` → return 200 with original; if invalid → return 422
    - Batch: validate all events first; if any fail → return 422 with per-index errors, reject entire batch atomically; if all valid → upsert all, return 201 (all new) or 200 (some existed)
    - Acceptance criteria: single valid new event returns 201; duplicate returns 200; batch with one invalid event returns 422 and nothing is written
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
    - Depends on: 6.1, 5.2

  - [ ] 6.7 Implement `GET /stores/{id}/metrics` endpoint (`backend/api/routers/metrics.py`)
    - Accept optional `start` and `end` ISO 8601 query params; default to current calendar day in store timezone
    - Query SQLite for: `unique_visitors`, `conversion_rate`, `avg_dwell_per_zone`, `queue_depth`, `abandonment_rate`, `avg_visit_duration_seconds`, `peak_hour`
    - `conversion_rate = 0.0` when `unique_visitors = 0`; `abandonment_rate = 0.0` when no `BILLING_QUEUE_JOIN` events
    - Return HTTP 404 if store not found; respond within 500ms for windows up to 30 days
    - Acceptance criteria: zero-visitor store returns `conversion_rate: 0.0`; correct `unique_visitors` count for known fixture data
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
    - Depends on: 6.1, 5.2

  - [ ] 6.8 Implement `GET /stores/{id}/funnel` endpoint (`backend/api/routers/funnel.py`)
    - Accept optional `start`/`end` params (max 90-day window)
    - Return ordered funnel stages: `zone_id`, `zone_name`, `visitor_count`, `entry_rate`, `avg_dwell_seconds`; ordered by median visit sequence position, then alphabetically by `zone_name`
    - Include `conversion_funnel` sub-object with converted visitor counts per stage
    - Return 200 with empty list and `data_available: false` when no events exist
    - Return 404 if store not found
    - Acceptance criteria: stages ordered correctly; `entry_rate` is a decimal in [0.0, 1.0] rounded to 4 decimal places
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
    - Depends on: 6.1, 5.2

  - [ ] 6.9 Implement `GET /stores/{id}/heatmap` endpoint (`backend/api/routers/heatmap.py`)
    - Accept optional `start`/`end` params (max 90-day window), `resolution` (`low`=10×10, `medium`=20×20, `high`=40×40, default `medium`), optional `zone_id` filter
    - Query `track_positions` table; bin positions into grid cells; normalise density to [0.0, 1.0] relative to max cell count
    - Return `grid` array with `x`, `y`, `width`, `height`, `density` per cell
    - Return all cells with `density: 0.0` when no positions recorded
    - Return 404 if store or zone not found
    - Acceptance criteria: `low` resolution returns exactly 100 cells; `medium` returns 400; `high` returns 1600; empty window returns all zeros
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
    - Depends on: 6.1, 5.2

  - [ ] 6.10 Implement `GET /stores/{id}/anomalies` endpoint (`backend/api/routers/anomalies.py`)
    - Accept optional `start`/`end` params (max 24h window, default last 24h)
    - Return up to 500 anomaly records ordered by `detected_at` descending
    - Return 404 if store not found; return 400 if date params malformed or `start > end`
    - Acceptance criteria: returns empty list (200) when no anomalies; returns 400 for `start > end`; returns 404 for unknown store
    - _Requirements: 8.1, 8.2, 8.5, 8.6, 8.7_
    - Depends on: 6.1, 5.2

  - [ ] 6.11 Create `backend/api/dependencies.py` for shared FastAPI dependencies
    - Define `get_db() -> Database` dependency (returns the singleton DB instance from app state)
    - Define `get_event_queue() -> asyncio.Queue` dependency
    - Define `get_ws_manager() -> ConnectionManager` dependency
    - Acceptance criteria: all routers can import and use these dependencies without circular imports
    - _Requirements: 4.1, 5.1_
    - Depends on: 6.1

- [ ] 6.12 Checkpoint — Ensure all tests pass
  - Run `pytest tests/unit/ tests/integration/ tests/property/ -v --cov=engine --cov=api --cov-report=term-missing`
  - Ensure ≥ 80% line coverage across `engine/` and `api/` modules
  - Fix any failing tests before proceeding to Phase 7
  - _Requirements: 14.2_

- [ ] 7. Phase 7: Dashboard
  - [ ] 7.1 Create TypeScript event types (`frontend/src/types/events.ts`)
    - Define TypeScript interfaces mirroring the canonical event schema: `Event`, `EventType` (union of 8 strings), `StoreMetrics`, `FunnelStage`, `HeatmapCell`, `Anomaly`
    - Acceptance criteria: `npm run build` passes with no TypeScript errors referencing these types
    - _Requirements: 10.1, 15.1_
    - Depends on: 1.4

  - [ ] 7.2 Create axios API client and React Query hooks (`frontend/src/api/`)
    - Create `frontend/src/api/client.ts`: axios instance with `baseURL` from `VITE_API_BASE_URL` env var
    - Create `frontend/src/api/hooks/useMetrics.ts`: `useQuery` hook for `GET /stores/{id}/metrics`
    - Create `frontend/src/api/hooks/useFunnel.ts`: `useQuery` hook with 30s `refetchInterval`
    - Create `frontend/src/api/hooks/useHeatmap.ts`: `useQuery` hook, accepts `timeWindow` param
    - Create `frontend/src/api/hooks/useAnomalies.ts`: `useQuery` hook with 60s `refetchInterval`
    - Acceptance criteria: each hook returns `{ data, isLoading, error }` with correct TypeScript types
    - _Requirements: 10.2, 10.3, 10.4_
    - Depends on: 7.1

  - [ ] 7.3 Implement Zustand store for WebSocket-driven live state (`frontend/src/store/websocket.ts`)
    - Define Zustand store with: `visitorCount: number`, `queueDepth: number`, `liveEvents: Event[]` (last 20), `connectionStatus: "connected" | "reconnecting" | "failed"`
    - Implement `connect(storeId: string)`: open WebSocket to `VITE_WS_BASE_URL/ws/stores/{id}/events`; on message, update store state
    - Implement reconnect backoff: 1s, 2s, 4s, 8s, 16s (5 attempts); set `connectionStatus = "failed"` after 5 failures
    - On disconnect: set `connectionStatus = "reconnecting"` within 1s
    - Acceptance criteria: `connectionStatus` transitions to `"reconnecting"` within 1s of connection drop; `liveEvents` never exceeds 20 items
    - _Requirements: 9.6, 10.1, 10.5, 10.6_
    - Depends on: 7.1

  - [ ] 7.4 Implement `StoreSelector` component and `App.tsx` routing
    - Create `frontend/src/App.tsx`: render `StoreSelector` dropdown; on selection, trigger all data fetches and WebSocket connection
    - Create `frontend/src/components/StoreSelector.tsx`: fetch store list from `GET /stores` (add this lightweight endpoint to backend); render `<select>` element
    - Implement tab navigation: Overview, Funnel, Heatmap, Anomalies (render correct screen per tab)
    - Acceptance criteria: selecting a store populates all screens within 2s; tab switching renders correct component
    - _Requirements: 10.8_
    - Depends on: 7.2, 7.3

  - [ ] 7.5 Implement Overview Screen (`frontend/src/components/Overview/`)
    - Create `OverviewScreen.tsx`: display 4 KPI cards — visitor count, conversion rate, avg dwell, queue depth
    - KPI values sourced from Zustand store (WebSocket-driven); update within 500ms of WS event receipt
    - Acceptance criteria: KPI cards render without errors; values update when Zustand store changes
    - _Requirements: 10.1_
    - Depends on: 7.3, 7.4

  - [ ] 7.6 Implement Funnel Screen (`frontend/src/components/Funnel/`)
    - Create `FunnelScreen.tsx`: render a Recharts `BarChart` with zone names on X-axis and `visitor_count` on Y-axis
    - Show drop-off rate between stages as percentage labels
    - Use `useFunnel` hook; display loading skeleton while fetching
    - Acceptance criteria: chart renders with correct zone order; refreshes every 30s
    - _Requirements: 10.2_
    - Depends on: 7.2, 7.4

  - [ ] 7.7 Implement Heatmap Screen (`frontend/src/components/Heatmap/`)
    - Create `HeatmapScreen.tsx`: render a `<canvas>` overlay on a store layout image
    - Draw each grid cell as a filled rectangle with opacity proportional to `density`; use a red-yellow-green colour scale
    - Add time-window selector buttons: "Last 1h", "Last 4h", "Today"; trigger `useHeatmap` refetch on change
    - Acceptance criteria: canvas cells align with normalised coordinates; density 0.0 renders as transparent; density 1.0 renders as fully opaque red
    - _Requirements: 10.3_
    - Depends on: 7.2, 7.4

  - [ ] 7.8 Implement Anomalies Screen (`frontend/src/components/Anomalies/`)
    - Create `AnomaliesScreen.tsx`: render a list of anomaly cards with severity badges
    - Badge colours: `high` → red (`bg-red-500`), `medium` → amber (`bg-amber-500`), `low` → grey (`bg-gray-400`)
    - Use `useAnomalies` hook; auto-refresh every 60s
    - Acceptance criteria: severity badges render correct colours; list is ordered by `detected_at` descending
    - _Requirements: 10.4_
    - Depends on: 7.2, 7.4

  - [ ] 7.9 Implement Live Event Feed panel (`frontend/src/components/LiveFeed/`)
    - Create `LiveFeedPanel.tsx`: render last 20 events from Zustand `liveEvents` in reverse chronological order
    - Each row: event type badge, visitor ID (truncated), timestamp (relative, e.g. "2s ago")
    - Updates within 500ms of WS event receipt (driven by Zustand store)
    - Acceptance criteria: new events appear at top; list never exceeds 20 items; timestamps update every second
    - _Requirements: 10.5_
    - Depends on: 7.3, 7.4

  - [ ] 7.10 Implement WebSocket reconnect indicator
    - In `App.tsx` or a shared layout component: read `connectionStatus` from Zustand store
    - When `connectionStatus === "reconnecting"`: show a visible banner "Reconnecting…" within 1s
    - When `connectionStatus === "failed"`: show banner with "Manual Retry" button that calls `connect(storeId)`
    - Acceptance criteria: banner appears within 1s of connection drop; "Manual Retry" button triggers reconnect attempt
    - _Requirements: 10.6_
    - Depends on: 7.3, 7.4

  - [ ] 7.11 Implement responsive layout (1280px–2560px)
    - Apply Tailwind CSS (or CSS Grid/Flexbox) layout to `App.tsx` and all screen components
    - Ensure no horizontal scrollbars at 1280px, 1920px, and 2560px viewport widths
    - Acceptance criteria: `npm run build` passes; no horizontal overflow at any supported viewport width
    - _Requirements: 10.7_
    - Depends on: 7.5, 7.6, 7.7, 7.8, 7.9

- [ ] 8. Phase 8: WebSocket Integration
  - [ ] 8.1 Implement `ConnectionManager` (`backend/api/websocket/manager.py`)
    - Create `ConnectionManager` class with `connections: dict[str, set[WebSocket]]`
    - Implement `async connect(store_id: str, ws: WebSocket, db: Database)`: validate `store_id` exists in DB (reject with close code 4004 if not); add `ws` to `connections[store_id]`; send last 50 events as `{"type": "initial_state", "events": [...]}` payload
    - Implement `disconnect(store_id: str, ws: WebSocket)`: remove `ws` from set; no effect on other connections
    - Implement `async broadcast(event: Event)`: send `{"type": "event", "data": event.to_dict()}` to all connections for `event.store_id`; on send error, close that connection with code 1011 and log; do not affect other connections
    - Acceptance criteria: broadcast to 50 connections completes within 500ms; failed connection is closed with 1011 without affecting others
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.6, 9.7_
    - Depends on: 5.2, 2.2

  - [ ] 8.2 Implement WebSocket router (`backend/api/websocket/router.py`)
    - Create FastAPI `APIRouter` with endpoint `WS /ws/stores/{store_id}/events`
    - On connect: call `ws_manager.connect(store_id, ws, db)`
    - Run receive loop: `await ws.receive_text()` (to detect client disconnect); on `WebSocketDisconnect`, call `ws_manager.disconnect(store_id, ws)`
    - Implement 60s idle timeout: if no ping frame received within 60s, close with code 1001
    - Acceptance criteria: unknown `store_id` closes with code 4004; idle connection closes with code 1001 after 60s
    - _Requirements: 9.1, 9.5_
    - Depends on: 8.1

  - [ ] 8.3 Wire `ConnectionManager` into `event_consumer` and `main.py`
    - Instantiate `ConnectionManager` as a singleton in `main.py`; pass to `event_consumer` task and to `create_app()`
    - Register WebSocket router in `app.py`
    - Acceptance criteria: an event placed on `event_queue` is broadcast to all connected WebSocket clients for that store
    - _Requirements: 9.2_
    - Depends on: 8.2, 5.4, 6.1

  - [ ]* 8.4 Write integration tests for WebSocket endpoint
    - File: `backend/tests/integration/test_health_api.py` (add WS tests) or new file
    - Test: valid store connection receives initial state payload; unknown store rejected with 4004; broadcast reaches all connected clients; failed client closed with 1011
    - Use `httpx` async WebSocket client or `starlette.testclient.TestClient`
    - Acceptance criteria: all 4 scenarios pass
    - _Requirements: 9.1, 9.3, 9.7_
    - Depends on: 8.3

- [ ] 9. Phase 9: Anomaly Detection
  - [ ] 9.1 Integrate `AnomalyDetector` into `EventEngine` run loop
    - In `EventEngine.run()`: after processing each `TrackFrame`, call all four `AnomalyDetector` check methods with current state
    - On anomaly detected: write to `anomalies` table via `db.insert_anomaly(anomaly)`; push anomaly as an event onto `event_queue` for WebSocket broadcast
    - Acceptance criteria: a queue depth > 5 sustained for 181s triggers a `QUEUE_BUILDUP` anomaly row in the DB
    - _Requirements: 8.3, 8.4_
    - Depends on: 4.7, 4.6, 5.2

  - [ ] 9.2 Implement `QUEUE_BUILDUP` anomaly persistence and API response
    - Ensure `AnomalyDetector.check_queue_buildup` includes current queue depth in the `description` field
    - Ensure `GET /stores/{id}/anomalies` returns `QUEUE_BUILDUP` records with `severity: "high"` and depth in description
    - Acceptance criteria: `GET /stores/{id}/anomalies` returns a `QUEUE_BUILDUP` record with `severity: "high"` and description containing the queue depth value
    - _Requirements: 8.3, 8.4_
    - Depends on: 9.1, 6.10

  - [ ] 9.3 Implement `CAMERA_OVERLAP_CONFLICT` detection and resolution
    - In `EventEngine.run()`: maintain a `_recent_positions: dict[int, list[tuple[str, datetime]]]` (track_id → [(zone_id, timestamp)])
    - Detect when same `track_id` appears in two non-adjacent zones within 2s; emit `CAMERA_OVERLAP_CONFLICT` anomaly
    - Use higher-confidence detection as authoritative position; if equal confidence, use earlier timestamp
    - Acceptance criteria: simultaneous detection in two non-adjacent zones within 2s produces a `CAMERA_OVERLAP_CONFLICT` anomaly; authoritative position is the higher-confidence one
    - _Requirements: 8.3, 16.5_
    - Depends on: 9.1

  - [ ]* 9.4 Write integration tests for anomaly detection edge cases
    - File: `backend/tests/integration/test_anomalies_api.py`
    - Test all 4 anomaly types: `QUEUE_BUILDUP`, `EMPTY_STORE`, `UNUSUAL_DWELL`, `CAMERA_OVERLAP_CONFLICT`
    - Test time window filtering, empty result (200 with empty list), unknown store (404), malformed dates (400)
    - Acceptance criteria: all 6 test scenarios pass
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.6, 8.7, 14.5_
    - Depends on: 9.2, 9.3

  - [ ]* 9.5 Write integration tests for edge cases (group entry, staff, re-entry, occlusion, queue buildup, empty store)
    - File: `backend/tests/integration/test_ingest_api.py` (add edge case tests)
    - Group entry: 2 simultaneous entrants → `unique_visitors = 2`
    - Staff movement: staff tracks absent from all events and metrics
    - Re-entry within 300s: `REENTRY` emitted; `unique_visitors` not incremented
    - Partial occlusion (track lost < 30 frames): same `visitor_id` before and after
    - Queue buildup (depth > 5 for > 3 min): `QUEUE_BUILDUP` in anomalies
    - Empty store (0 visitors > 10 min): `EMPTY_STORE` in anomalies
    - Acceptance criteria: each of the 6 edge case tests asserts on a specific named observable outcome
    - _Requirements: 14.5_
    - Depends on: 9.4, 4.12

- [ ] 10. Phase 10: Docker + Testing + Documentation
  - [ ] 10.1 Write `backend/Dockerfile`
    - Use `python:3.11-slim` base image
    - Copy `pyproject.toml` and install dependencies with `pip install -e .`
    - Copy source; set `WORKDIR /app`
    - Default `CMD`: `uvicorn main:app --host 0.0.0.0 --port 8000`
    - Add `HEALTHCHECK`: `CMD curl -f http://localhost:8000/health || exit 1`
    - Acceptance criteria: `docker build -t reintellect-backend ./backend` succeeds; `docker run` starts uvicorn
    - _Requirements: 13.1, 13.3_
    - Depends on: 6.2

  - [ ] 10.2 Write `frontend/Dockerfile` and `frontend/nginx.conf`
    - Multi-stage: stage 1 `node:20-alpine` runs `npm run build`; stage 2 `nginx:alpine` copies `dist/` to `/usr/share/nginx/html`
    - `nginx.conf`: serve static files; proxy `/api` and `/ws` to `http://backend:8000`; `try_files $uri /index.html` for SPA routing
    - Add `HEALTHCHECK`: `CMD curl -f http://localhost:80 || exit 1`
    - Acceptance criteria: `docker build -t reintellect-frontend ./frontend` succeeds; `docker run -p 3000:80` serves the React app
    - _Requirements: 13.1, 13.3_
    - Depends on: 7.11

  - [ ] 10.3 Complete `docker-compose.yml` with all service definitions
    - `db-init`: build `./backend`; command `python -m db.init_schema`; volume `reintellect_db:/data`; healthcheck `test -f /data/reintellect.db`
    - `backend`: build `./backend`; ports `8000:8000`; volume `reintellect_db:/data`; env from `.env`; `depends_on: db-init (service_completed_successfully)`; healthcheck `curl -f http://localhost:8000/health`; GPU reservation (optional, advisory)
    - `frontend`: build `./frontend`; ports `3000:80`; env `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`; `depends_on: backend (service_healthy)`; healthcheck `curl -f http://localhost:80`
    - Acceptance criteria: `docker compose up` starts all 3 services; `GET http://localhost:8000/health` returns 200; `GET http://localhost:3000` returns 200
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_
    - Depends on: 10.1, 10.2, 5.3

  - [ ] 10.4 Write complete integration test suite for all API endpoints
    - Files: `test_ingest_api.py`, `test_metrics_api.py`, `test_funnel_api.py`, `test_heatmap_api.py`, `test_anomalies_api.py`, `test_health_api.py`
    - Each file covers: happy path, error cases (404, 422, 400), edge cases per requirements
    - Use `httpx.AsyncClient` with `app=app` (in-process, no Docker required)
    - Acceptance criteria: all integration tests pass; `pytest --cov=api --cov-report=term-missing` shows ≥ 80% coverage for `api/`
    - _Requirements: 14.1, 14.2_
    - Depends on: 6.6, 6.7, 6.8, 6.9, 6.10, 6.2

  - [ ] 10.5 Write remaining property-based tests (Properties 2, 6, 8, 9, 10, 11)
    - File: `backend/tests/property/test_visit_duration.py`
    - Property 2: visit duration non-negativity — generate `(entry_ts, exit_ts)` pairs where `exit_ts >= entry_ts`; assert `duration_seconds >= 0`
    - Property 6: re-entry visitor identity — generate exit+reentry pairs with varying gaps; assert same `visitor_id` iff gap < 300s
    - Property 8: ingestion idempotency — submit same event N times; assert exactly 1 DB row and correct HTTP codes
    - Property 9: batch atomic rejection — batch with one invalid event; assert 422 and 0 rows written
    - Property 10: conversion rate correctness — generate `(unique, converted)` pairs; assert formula and 0.0 when unique=0
    - Property 11: unique visitor count excludes re-entries — generate ENTRY+REENTRY sequences; assert `unique_visitors` = distinct visitor_id count
    - Tag each test with its property number and requirements clause
    - Acceptance criteria: all 6 property tests pass with ≥ 100 examples each
    - _Requirements: 14.3, 14.4_
    - Depends on: 6.6, 6.7, 4.1, 2.2

  - [ ] 10.6 Configure `conftest.py` with shared fixtures and Hypothesis profile
    - File: `backend/tests/conftest.py`
    - Fixtures: `in_memory_db` (aiosqlite in-memory with schema applied), `test_client` (httpx AsyncClient with test app), `sample_store_layout` (dict with 4 zones), `mock_pipeline` (asyncio.Queue stub)
    - Register Hypothesis CI profile: `max_examples=100`, `suppress_health_check=[HealthCheck.too_slow]`
    - Acceptance criteria: all test files can import fixtures without errors; `pytest --collect-only` shows all tests collected
    - _Requirements: 14.1, 14.3_
    - Depends on: 5.2, 6.1

  - [ ] 10.7 Write smoke test for Docker Compose stack (`backend/tests/smoke/test_docker_stack.py`)
    - Poll `GET http://localhost:8000/health` every 2s for up to 30s
    - Assert HTTP 200 is received within the deadline
    - On timeout: fail with `"Health check timed out after 30 seconds. Last response: {last_response}"`
    - Acceptance criteria: test passes when Docker stack is running; fails with descriptive message when stack is down
    - _Requirements: 14.6_
    - Depends on: 10.3

  - [ ] 10.8 Verify test coverage meets 80% threshold
    - Run `pytest --cov=engine --cov=api --cov-report=term-missing` and confirm ≥ 80% line coverage
    - Add missing unit or integration tests for any uncovered lines in `engine/` or `api/`
    - Acceptance criteria: coverage report shows ≥ 80% for both `engine/` and `api/` modules
    - _Requirements: 14.2_
    - Depends on: 10.4, 10.5

  - [ ] 10.9 Write `README.md` with quickstart instructions
    - Document: prerequisites (Docker, Docker Compose, optional NVIDIA GPU), quickstart (`cp .env.example .env && docker compose up`), environment variables table, API endpoint reference (method, path, description), test execution (`pytest`), architecture diagram reference
    - Acceptance criteria: a reviewer can run the platform from scratch using only the README instructions
    - _Requirements: 13.1_
    - Depends on: 10.3

- [ ] 10.10 Final Checkpoint — Ensure all tests pass
  - Run `pytest -v --cov=engine --cov=api --cov-report=term-missing`
  - Run `docker compose up` and verify all health checks pass within 60s
  - Ensure `GET http://localhost:3000` returns 200 and the dashboard renders
  - Fix any remaining failures before marking the implementation complete
  - _Requirements: 13.3, 14.2_


---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they are property-based or unit tests that validate correctness properties
- Each task references specific requirements for full traceability
- Checkpoints (tasks 5 and 6) ensure incremental validation at phase boundaries
- The 11 correctness properties from the design document are covered by property tests in tasks 2.3, 3.4, 3.5, 4.3, 4.5, and 10.5
- All backend tasks assume Python 3.11; all frontend tasks assume Node 20
- The `visitor_id` / `track_id` distinction is enforced throughout: `track_id` never appears in any public API response or event payload
- `event_id` is always client-supplied (UUID v4); the server never generates it
- Batch ingestion (up to 500 events) is atomic: all-or-nothing on validation failure

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.4", "1.5"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "2.1", "5.1"] },
    { "id": 3, "tasks": ["1.4", "2.2", "2.4", "5.2"] },
    { "id": 4, "tasks": ["2.3", "3.1", "3.2", "5.3"] },
    { "id": 5, "tasks": ["3.3", "4.1", "5.4"] },
    { "id": 6, "tasks": ["3.4", "3.5", "3.6", "4.2", "4.4", "4.6"] },
    { "id": 7, "tasks": ["4.3", "4.5", "4.7"] },
    { "id": 8, "tasks": ["4.8", "4.9", "4.10", "4.11", "4.12"] },
    { "id": 9, "tasks": ["6.1", "6.11"] },
    { "id": 10, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 11, "tasks": ["6.5", "6.6", "6.7", "6.8", "6.9", "6.10"] },
    { "id": 12, "tasks": ["6.12", "7.1", "8.1"] },
    { "id": 13, "tasks": ["7.2", "7.3", "8.2"] },
    { "id": 14, "tasks": ["7.4", "8.3"] },
    { "id": 15, "tasks": ["7.5", "7.6", "7.7", "7.8", "7.9", "8.4", "9.1"] },
    { "id": 16, "tasks": ["7.10", "9.2", "9.3"] },
    { "id": 17, "tasks": ["7.11", "9.4", "9.5"] },
    { "id": 18, "tasks": ["10.1", "10.2", "10.6"] },
    { "id": 19, "tasks": ["10.3", "10.4", "10.5"] },
    { "id": 20, "tasks": ["10.7", "10.8"] },
    { "id": 21, "tasks": ["10.9", "10.10"] }
  ]
}
```
