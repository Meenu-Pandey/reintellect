# ReIntellect

**Transform retail CCTV footage into real-time business intelligence.**

> Built for the Purplle Tech Challenge 2026

---

## Overview

ReIntellect is an AI-powered store intelligence platform that converts ordinary security cameras into a live analytics engine. It tracks visitor journeys, measures brand engagement, detects queue abandonment, and surfaces anomalies — all within 500 milliseconds of the camera capturing the event.

The platform was designed specifically for Purplle's Brigade Road store, where five CCTV cameras cover the entrance, cosmetics zone, skincare zone, checkout queue, and backroom. Every frame is processed through a multi-stage AI pipeline and delivered to a real-time dashboard.

---

## Problem Statement

Retail stores operate blind. Security cameras record footage that is reviewed only after incidents — never in real time, never for business insight. Store managers cannot answer basic questions:

- How many unique visitors entered today?
- Which brand zones attract the most dwell time?
- How long is the queue right now, and are customers abandoning it?
- Is there an anomaly I should act on immediately?

Existing retail analytics solutions either require expensive hardware upgrades or rely on manual observation. Neither scales.

---

## Solution

ReIntellect turns any existing CCTV infrastructure into a real-time intelligence layer — no hardware changes required.

```
CCTV Cameras  →  YOLOv8 Detection  →  ByteTrack Identity Tracking
      →  Event Engine  →  Anomaly Detection  →  Live Dashboard
```

The result: a live command center that shows visitor journeys, heatmaps, conversion funnels, queue depth, and anomaly alerts — updated in under 500ms.

---

## Key Features

| Feature | Description |
|---|---|
| **Visitor Tracking** | ByteTrack persistent identity with 30-frame re-association window |
| **Zone Intelligence** | Per-brand dwell time, entry/exit events across all store zones |
| **Conversion Funnel** | End-to-end visitor journey from entrance to purchase |
| **Queue Intelligence** | Real-time queue depth, wait time, and abandonment detection |
| **Heatmap** | Density visualisation from tracked position data |
| **Anomaly Detection** | Queue buildup, unusual dwell, camera overlap conflict, empty store |
| **Live Dashboard** | WebSocket-driven real-time analytics updated <500ms |
| **Store Digital Twin** | Actual Brigade Road floor plan with zone overlays and visitor paths |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose                          │
│                                                                 │
│  ┌──────────┐     ┌──────────────────────────┐    ┌─────────┐  │
│  │ db-init  │────▶│        backend            │◀───│frontend │  │
│  │(one-shot)│     │                           │    │ :3000   │  │
│  └──────────┘     │  ┌─────────────────────┐ │    └─────────┘  │
│                   │  │  DetectionPipeline   │ │                 │
│                   │  │  YOLOv8n + ByteTrack │ │                 │
│                   │  └──────────┬──────────┘ │                 │
│                   │             │ TrackFrames │                 │
│                   │  ┌──────────▼──────────┐ │                 │
│                   │  │    EventEngine       │ │                 │
│                   │  │  VisitorRegistry     │ │                 │
│                   │  │  ZoneTracker         │ │                 │
│                   │  │  QueueTracker        │ │                 │
│                   │  │  AnomalyDetector     │ │                 │
│                   │  └──────────┬──────────┘ │                 │
│                   │             │ Events      │                 │
│                   │  ┌──────────▼──────────┐ │                 │
│                   │  │  FastAPI REST + WS   │ │                 │
│                   │  │  SQLite WAL          │ │                 │
│                   │  └─────────────────────┘ │                 │
│                   └──────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

**Services:**

- **db-init** — Runs once at startup: creates schema and seeds demo data
- **backend** — FastAPI monolith: detection pipeline + event engine + REST + WebSocket
- **frontend** — React SPA served by nginx, proxies `/api` and `/ws` to backend

---

## Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Person Detection | YOLOv8n (Ultralytics) | 10+ FPS real-time inference on CPU |
| Object Tracking | ByteTrack | Persistent visitor identity across frames |
| Backend Framework | FastAPI + Uvicorn | Async event engine, REST APIs, WebSockets |
| Database | SQLite (WAL mode) | Idempotent event persistence |
| Real-time | WebSockets (Starlette) | Live event streaming <100ms |
| Frontend | React 18 + TypeScript | Real-time dashboard |
| State | Zustand + React Query | WebSocket store + REST data fetching |
| Charts | Recharts | Funnel and traffic visualisations |
| Animation | Framer Motion | Smooth transitions and live indicators |
| Containerisation | Docker + Compose | One-command deployment |

---

## Demo Screenshots

> *Screenshots from the Purplle Brigade Road demo deployment*

| Screen | Description |
|---|---|
| `[Landing Page]` | Premium product showcase with live camera feed preview |
| `[Overview Dashboard]` | KPI cards, store floor map, hourly traffic chart |
| `[Funnel Analytics]` | Visitor conversion stages with drop-off rates |
| `[Heatmap]` | Real store layout with density overlay |
| `[Anomaly Detection]` | SOC-style anomaly cards with recommended actions |

---

## Quick Start (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2.20+
- 8 GB RAM (YOLOv8 on CPU)

### Launch

```bash
git clone <repo-url>
cd reIntellect

cp .env.example .env

docker compose up --build
```

Open **http://localhost:3000** once all services are healthy (~30–60s on first build).

### Verify

```bash
# Backend health
curl http://localhost:8000/health

# Expected
# {"status":"healthy","version":"0.1.0","database":"healthy",...}
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate

pip install -e .

python -m db.init_schema       # Create schema
python -m db.seed_demo_data    # Populate with Brigade Road demo data

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

### Tests

```bash
cd backend
pytest tests -v                                          # 84 tests
pytest tests --cov=engine --cov=api --cov-report=term  # Coverage report
```

---

## API Overview

Full interactive docs at `http://localhost:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Subsystem health (DB, pipeline, engine) |
| `GET` | `/schema/events` | Canonical event JSON Schema |
| `POST` | `/stores` | Create/update store layout with zone polygons |
| `POST` | `/stores/{id}/transactions` | Ingest POS transaction, mark conversion |
| `POST` | `/events/ingest` | Single event or batch up to 500 (atomic) |
| `GET` | `/stores/{id}/metrics` | KPIs: visitors, conversion, dwell, queue |
| `GET` | `/stores/{id}/funnel` | Visitor funnel stages with entry rates |
| `GET` | `/stores/{id}/heatmap` | Grid density (10×10 to 40×40 resolution) |
| `GET` | `/stores/{id}/anomalies` | Anomaly records with metadata |
| `WS` | `/ws/stores/{id}/events` | Live event stream (initial state + updates) |

---

## Demo Data

The seeder populates one full operating day of Purplle Brigade Road activity:

```bash
python -m db.seed_demo_data
```

| Data | Count |
|---|---|
| Visitors | ~206 |
| Events (all 8 types) | ~1,300 |
| Track positions | ~3,300 |
| POS transactions | ~60 |
| Anomalies | 5 (all 4 types) |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VIDEO_SOURCE` | `demo` | Path to video file or `demo` for bundled footage |
| `DB_PATH` | `/data/reintellect.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `STORE_TIMEZONE` | `Asia/Kolkata` | Store timezone for metric windows |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowed origin |
| `CUDA_VISIBLE_DEVICES` | *(empty)* | GPU index — leave empty for CPU |

---

## Future Improvements

- **Multi-camera cross-tracking** — Unify visitor identity across all 5 camera feeds using spatial proximity and appearance features
- **GPU inference** — CUDA support for 30+ FPS detection (currently 10+ FPS on CPU)
- **POS integration** — Direct EPOS feed integration for automatic conversion attribution
- **Staff uniform training** — Fine-tune YOLOv8 on Purplle staff uniforms for better visitor/staff separation
- **Zone polygon calibration** — Admin UI for drawing zone polygons directly on the camera feed
- **Multi-store support** — Scale to multiple Purplle locations with shared analytics
- **Mobile dashboard** — Responsive manager-facing mobile view
- **Alert notifications** — Push/SMS alerts for high-severity anomalies

---

## Project Structure

```
reIntellect/
├── backend/
│   ├── api/           # FastAPI routers and WebSocket manager
│   ├── db/            # SQLite schema, migrations, seeder
│   ├── detection/     # YOLOv8 pipeline, ByteTrack, staff filter
│   ├── engine/        # Event engine, visitor registry, anomaly detector
│   ├── tests/         # 84 tests: unit, integration, property-based
│   └── main.py        # Application entrypoint
├── frontend/
│   ├── public/        # Store layout image, camera thumbnails, video assets
│   └── src/
│       ├── components/ # Dashboard + landing page components
│       ├── pages/      # HomePage and DashboardPage
│       └── store/      # Zustand WebSocket store
├── resources/         # Original CCTV footage (CAM 1–5, zone videos)
├── docs/              # Footage analysis, zone design, business metrics
├── docker-compose.yml
└── .env.example
```

---

*Built for Purplle Tech Challenge 2026*
