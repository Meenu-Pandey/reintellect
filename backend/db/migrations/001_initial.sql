-- Migration 001: Initial schema
-- ReIntellect Store Intelligence Platform

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Stores
CREATE TABLE IF NOT EXISTS stores (
    store_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cameras
CREATE TABLE IF NOT EXISTS cameras (
    camera_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    name TEXT,
    position TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (camera_id, store_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Zones
CREATE TABLE IF NOT EXISTS zones (
    zone_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    camera_id TEXT,
    zone_type TEXT NOT NULL CHECK (zone_type IN ('entry', 'exit', 'floor', 'billing_queue', 'restricted')),
    name TEXT,
    polygon_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (zone_id, store_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Visitors
CREATE TABLE IF NOT EXISTS visitors (
    visitor_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    converted INTEGER NOT NULL DEFAULT 0 CHECK (converted IN (0, 1)),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Visits
CREATE TABLE IF NOT EXISTS visits (
    visit_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    duration_seconds REAL,
    converted INTEGER NOT NULL DEFAULT 0 CHECK (converted IN (0, 1)),
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id) ON DELETE CASCADE,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL CHECK (event_type IN ('ENTRY', 'EXIT', 'ZONE_ENTER', 'ZONE_EXIT', 'ZONE_DWELL', 'BILLING_QUEUE_JOIN', 'BILLING_QUEUE_ABANDON', 'REENTRY')),
    store_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    attributes_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE,
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id) ON DELETE CASCADE
);

-- Track positions
CREATE TABLE IF NOT EXISTS track_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    x REAL NOT NULL CHECK (x >= 0.0 AND x <= 1.0),
    y REAL NOT NULL CHECK (y >= 0.0 AND y <= 1.0),
    timestamp TEXT NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- POS Transactions
CREATE TABLE IF NOT EXISTS pos_transactions (
    transaction_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    visitor_id TEXT,
    timestamp TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    detected_at TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_events_store_timestamp ON events(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_visitor ON events(visitor_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_visitors_store ON visitors(store_id);
CREATE INDEX IF NOT EXISTS idx_visits_store ON visits(store_id);
CREATE INDEX IF NOT EXISTS idx_visits_visitor ON visits(visitor_id);
CREATE INDEX IF NOT EXISTS idx_track_positions_store_ts ON track_positions(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_store_detected ON anomalies(store_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_pos_transactions_store ON pos_transactions(store_id, timestamp);
