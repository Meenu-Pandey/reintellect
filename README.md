<<<<<<< HEAD
# ReIntellect

### AI-Powered Retail Intelligence Platform

Transforming CCTV footage into real-time business intelligence for physical retail stores.

## Problem

Retail stores generate thousands of customer interactions every day, but most of this valuable behavioral data is lost because it exists only in CCTV footage.

Store managers know:

* Revenue
* Transactions
* Inventory

But they don't know:

* How many visitors entered
* Which brands attracted attention
* Where customers spent time
* Why customers abandoned purchases
* How queues impact conversion

## Solution

ReIntellect converts CCTV footage into actionable retail analytics using Computer Vision and AI.

The platform tracks customer journeys from entry to purchase and provides real-time insights into:

* Visitor Traffic
* Conversion Rate
* Dwell Time
* Queue Performance
* Brand Engagement
* Security Events

## Visitor Journey Intelligence

ENTRY
→ Product Discovery
→ Brand Engagement
→ Checkout Queue
→ POS Interaction
→ PURCHASE
→ EXIT

## Key Features

### Customer Analytics

* Unique Visitor Tracking
* Dwell Time Analysis
* Heatmaps
* Customer Journey Mapping

### Conversion Analytics

* Offline Store Conversion Rate
* Funnel Analysis
* Checkout Performance
* Queue Abandonment Detection

### Brand Intelligence

* Brand-Level Engagement
* Zone Popularity Analysis
* Product Interest Tracking

### Operations & Security

* Queue Monitoring
* Cashier Presence Detection
* Restricted Area Monitoring
* After-Hours Activity Alerts

## Technology Stack

### AI & Computer Vision

* YOLOv8
* ByteTrack
* OpenCV

### Backend

* FastAPI
* SQLite
* WebSockets

### Frontend

* React
* TypeScript
* Vite

## Data Sources

* Multi-Camera CCTV Footage
* POS Transaction Data

## Primary KPI

Conversion Rate = Purchasers / Unique Visitors

## Built For

Purplle Retail Intelligence Challenge
=======
# ReIntellect — AI-Powered Retail Intelligence Platform

> **Built for Purplle Tech Challenge 2026**
> Transform retail CCTV footage into visitor journeys, conversion analytics, queue intelligence, heatmaps, and actionable retail insights — in real time.

---

## Overview

ReIntellect is an AI-powered store intelligence platform that processes live CCTV camera feeds through a multi-stage pipeline:

```
CCTV Cameras
    ↓
YOLOv8 Person Detection  (10+ FPS, CPU)
    ↓
ByteTrack Identity Tracking  (30-frame re-association window)
    ↓
Event Engine  (entry, exit, zone, queue classification)
    ↓
SQLite Analytics Store  (WAL mode, idempotent writes)
    ↓
FastAPI REST + WebSocket APIs  (<500ms latency)
    ↓
React Live Dashboard  (real-time, WebSocket-driven)
```

---

## Screenshots

| Landing Page | Dashboard Overview |
|---|---|
| `[Homepage — product showcase]` | `[Overview — KPIs + store map]` |

| Funnel Analytics | Heatmap |
|---|---|
| `[Customer journey funnel]` | `[Zone density heatmap]` |

| Anomaly Detection | Live Event Feed |
|---|---|
| `[Anomaly cards with recommendations]` | `[Real-time event stream]` |

---

## Features

| Feature | Description |
|---|---|
| **Visitor Tracking** | ByteTrack persistent identity across frames, 30-frame re-association |
| **Zone Intelligence** | Per-brand zone entry, dwell time, and exit events |
| **Queue Analytics** | Real-time queue depth, wait time, and abandonment detection |
| **Conversion Funnel** | End-to-end visitor journey from entry to purchase |
| **Heatmap** | Density visualisation from track position data |
| **Anomaly Detection** | Queue buildup, empty store, unusual dwell, camera overlap conflict |
| **Live Dashboard** | WebSocket-driven real-time analytics command center |
| **REST APIs** | Full CRUD + analytics endpoints for all store data |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Person Detection | YOLOv8n (Ultralytics) |
| Object Tracking | ByteTrack (via Ultralytics) |
| Backend Framework | FastAPI + Uvicorn |
| Async Storage | aiosqlite (SQLite WAL mode) |
| Real-time Transport | WebSockets (Starlette) |
| Frontend | React 18 + TypeScript + Vite |
| State Management | Zustand (WebSocket store) |
| Data Fetching | TanStack React Query |
| Charts | Recharts |
| Animations | Framer Motion |
| Icons | Lucide React |
| Routing | React Router v6 |
| Container | Docker + Docker Compose |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Docker Compose                    │
│                                                      │
│  ┌──────────┐    ┌─────────────────┐    ┌─────────┐ │
│  │ db-init  │───▶│    backend      │◀───│frontend │ │
│  │(one-shot)│    │  FastAPI :8000  │    │nginx:80 │ │
│  └──────────┘    │                 │    └─────────┘ │
│                  │ DetectionPipeline│               │
│                  │ EventEngine      │               │
│                  │ ConnectionManager│               │
│                  │ REST APIs        │               │
│                  └────────┬────────┘               │
│                           │                         │
│                  ┌────────▼────────┐                │
│                  │  SQLite (WAL)   │                │
│                  │  /data/         │                │
│                  └─────────────────┘                │
└──────────────────────────────────────────────────────┘
```

**Services:**
- **db-init** — Runs once at startup: creates schema, seeds Purplle store layout and demo data
- **backend** — FastAPI monolith: detection pipeline + event engine + REST + WebSocket
- **frontend** — React SPA served by nginx, proxies `/api` → backend, `/ws` → WebSocket

---

## Quickstart (Docker)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2.20+
- 8 GB RAM recommended (YOLOv8 + PyTorch on CPU)

### Launch in one command

```bash
# 1. Clone the repository
git clone <repo-url>
cd reIntellect

# 2. Copy environment file
cp .env.example .env

# 3. Launch all services
docker compose up --build

# 4. Open the dashboard
open http://localhost:3000
```

The startup sequence is:
1. `db-init` creates the database and seeds demo data (~5s)
2. `backend` starts and waits for `db-init` to complete (~30s for first build)
3. `frontend` starts after `backend` is healthy

### Verify everything is running

```bash
# Backend health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.1.0",...}

# Frontend
open http://localhost:3000
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialise database and seed demo data
python -m db.init_schema
python -m db.seed_demo_data

# Start the backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api and /ws to localhost:8000)
npm run dev

# Open: http://localhost:5173
```

### Run Tests

```bash
cd backend

# All tests
python -m pytest tests -v

# With coverage
python -m pytest tests --cov=engine --cov=api --cov-report=term-missing
```

---

## Demo Data

The platform ships with a demo data seeder that populates the database with a realistic day of Purplle Brigade Road store activity:

```bash
# Seed demo data (requires db to be initialised first)
python -m db.seed_demo_data
```

**Seeded data:**
| Data | Count |
|---|---|
| Visitors | ~206 per day |
| Events | ~1,300 (all 8 types) |
| Track positions | ~3,300 (for heatmap) |
| POS transactions | ~60 |
| Anomalies | 5 (all 4 types) |

**Demo store:** Purplle Brigade Road with 5 zones: Entry, Lakme, Maybelline, Skincare, Checkout Queue.

---

## API Reference

All endpoints are prefixed by the backend base URL (`http://localhost:8000` in development).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Subsystem health status |
| `GET` | `/schema/events` | Canonical event JSON Schema |
| `POST` | `/stores` | Create/update store layout |
| `POST` | `/stores/{id}/transactions` | Ingest POS transaction |
| `POST` | `/events/ingest` | Ingest single event or batch (up to 500) |
| `GET` | `/stores/{id}/metrics` | KPI metrics for a time window |
| `GET` | `/stores/{id}/funnel` | Visitor funnel stages |
| `GET` | `/stores/{id}/heatmap` | Position density grid |
| `GET` | `/stores/{id}/anomalies` | Anomaly records |
| `WS` | `/ws/stores/{id}/events` | Live event WebSocket stream |

Full OpenAPI docs: `http://localhost:8000/docs`

---

## Project Structure

```
reIntellect/
├── backend/
│   ├── api/
│   │   ├── routers/          # REST endpoints (health, stores, events, metrics...)
│   │   └── websocket/        # ConnectionManager + WebSocket router
│   ├── db/
│   │   ├── database.py       # Async SQLite wrapper
│   │   ├── migrations/       # SQL schema files
│   │   ├── init_schema.py    # db-init entry point
│   │   └── seed_demo_data.py # Demo data seeder
│   ├── detection/
│   │   ├── pipeline.py       # YOLOv8 + ByteTrack + StaffFilter
│   │   ├── tracker.py        # ByteTrack wrapper
│   │   └── staff_filter.py   # HSV colour classification
│   ├── engine/
│   │   ├── event_engine.py   # Orchestrator + anomaly integration
│   │   ├── visitor_registry.py
│   │   ├── zone_tracker.py
│   │   ├── queue_tracker.py
│   │   └── anomaly_detector.py
│   ├── tests/
│   │   ├── unit/             # 13 unit tests
│   │   ├── integration/      # 2 WebSocket integration tests
│   │   └── property/         # 5 Hypothesis property tests
│   ├── main.py               # FastAPI entrypoint + lifespan
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/            # HomePage + DashboardPage
│   │   ├── components/       # Landing + Dashboard components
│   │   ├── api/              # Axios client + React Query hooks
│   │   ├── store/            # Zustand WebSocket store
│   │   └── types/            # TypeScript event interfaces
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── resources/
│   ├── CAM 1.mp4 … CAM 5.mp4   # Purplle store footage
│   └── layouts/                 # Store layout files
├── data/
│   └── pos/                     # POS transaction data
├── docs/
│   ├── footage_analysis.md
│   ├── zone_design.md
│   └── business_metrics.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VIDEO_SOURCE` | `demo` | Video file path or `demo` for bundled footage |
| `CUDA_VISIBLE_DEVICES` | _(empty)_ | GPU index, leave empty for CPU |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `STORE_TIMEZONE` | `Asia/Kolkata` | Store timezone for metric windows |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowed origin |
| `DB_PATH` | `/data/reintellect.db` | SQLite database path (set by Docker) |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |
| `VITE_WS_BASE_URL` | _(empty)_ | Frontend WebSocket base URL |

---

## Verification Checklist

After `docker compose up --build`:

- [ ] `curl http://localhost:8000/health` returns `{"status":"healthy",...}`
- [ ] `http://localhost:3000` loads the ReIntellect landing page
- [ ] `http://localhost:3000/dashboard` shows the analytics dashboard
- [ ] KPI cards show ~143 visitors, ~35% conversion
- [ ] Funnel shows 5 stages with drop-off percentages
- [ ] Heatmap shows coloured density cells
- [ ] Anomalies shows 5 cards (QUEUE_BUILDUP, CAMERA_OVERLAP, etc.)
- [ ] Live Feed panel shows "Waiting for events..." (no live pipeline in demo)

---

## License

Built for the Purplle Tech Challenge 2026. All rights reserved.
>>>>>>> phase-3-detection
