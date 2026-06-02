/**
 * Zustand store for WebSocket-driven live state.
 *
 * Manages:
 * - visitorCount: current visitor count
 * - queueDepth: current billing queue depth
 * - liveEvents: last 20 events (most recent first)
 * - connectionStatus: "connected" | "reconnecting" | "failed"
 *
 * Reconnect backoff: 1s, 2s, 4s, 8s, 16s (5 attempts).
 * After 5 failures, connectionStatus = "failed".
 */

import { create } from "zustand";
import type { Event } from "../types/events";

export type ConnectionStatus = "connected" | "reconnecting" | "failed";

interface WebSocketState {
  visitorCount: number;
  queueDepth: number;
  liveEvents: Event[];
  connectionStatus: ConnectionStatus;
  connect: (storeId: string) => void;
  disconnect: () => void;
}

const MAX_LIVE_EVENTS = 20;
const MAX_RECONNECT_ATTEMPTS = 5;
const BACKOFF_BASE_MS = 1000;

let ws: WebSocket | null = null;
let reconnectAttempts = 0;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let currentStoreId: string | null = null;

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  visitorCount: 0,
  queueDepth: 0,
  liveEvents: [],
  connectionStatus: "reconnecting",

  connect: (storeId: string) => {
    // Clean up existing connection
    if (ws) {
      ws.close();
      ws = null;
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    currentStoreId = storeId;
    reconnectAttempts = 0;
    _connect(storeId, set, get);
  },

  disconnect: () => {
    if (ws) {
      ws.close();
      ws = null;
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    currentStoreId = null;
    reconnectAttempts = 0;
  },
}));

function _connect(
  storeId: string,
  set: (partial: Partial<WebSocketState>) => void,
  get: () => WebSocketState
) {
  const wsBaseUrl =
    import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}`;
  const url = `${wsBaseUrl}/ws/stores/${storeId}/events`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    set({ connectionStatus: "connected" });
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);

      if (msg.type === "event") {
        const evt: Event = msg.data;
        const state = get();

        // Update live events (cap at 20)
        const updatedEvents = [evt, ...state.liveEvents].slice(
          0,
          MAX_LIVE_EVENTS
        );

        // Update counters based on event type
        let visitorCount = state.visitorCount;
        let queueDepth = state.queueDepth;

        if (evt.event_type === "ENTRY") {
          visitorCount += 1;
        } else if (evt.event_type === "EXIT") {
          visitorCount = Math.max(0, visitorCount - 1);
        } else if (evt.event_type === "BILLING_QUEUE_JOIN") {
          queueDepth += 1;
        } else if (evt.event_type === "BILLING_QUEUE_ABANDON") {
          queueDepth = Math.max(0, queueDepth - 1);
        }

        set({
          liveEvents: updatedEvents,
          visitorCount,
          queueDepth,
        });
      } else if (msg.type === "initial_state") {
        // Initial state payload with last 50 events
        const events: Event[] = msg.events || [];
        const recentEvents = events.slice(0, MAX_LIVE_EVENTS);

        // Count current visitors/queue from initial state
        let visitorCount = 0;
        let queueDepth = 0;
        for (const evt of events) {
          if (evt.event_type === "ENTRY") visitorCount += 1;
          if (evt.event_type === "EXIT") visitorCount -= 1;
          if (evt.event_type === "BILLING_QUEUE_JOIN") queueDepth += 1;
          if (evt.event_type === "BILLING_QUEUE_ABANDON") queueDepth -= 1;
        }

        set({
          liveEvents: recentEvents,
          visitorCount: Math.max(0, visitorCount),
          queueDepth: Math.max(0, queueDepth),
        });
      }
    } catch {
      // Ignore malformed messages
    }
  };

  ws.onclose = () => {
    ws = null;

    if (!currentStoreId) return; // Intentional disconnect

    // Reconnect with backoff
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      set({ connectionStatus: "reconnecting" });
      const backoff = BACKOFF_BASE_MS * Math.pow(2, reconnectAttempts);
      reconnectAttempts += 1;
      reconnectTimeout = setTimeout(() => {
        if (currentStoreId) {
          _connect(currentStoreId, set, get);
        }
      }, backoff);
    } else {
      set({ connectionStatus: "failed" });
    }
  };

  ws.onerror = () => {
    // onclose will fire after onerror — handled there
  };
}
