/**
 * Main application component.
 *
 * Renders StoreSelector, tab navigation, active screen,
 * live event feed, and WebSocket reconnect indicator.
 */

import { useEffect, useState } from "react";
import { StoreSelector } from "./components/StoreSelector";
import { OverviewScreen } from "./components/Overview/OverviewScreen";
import { LiveFeedPanel } from "./components/LiveFeed/LiveFeedPanel";
import { ReconnectBanner } from "./components/ReconnectBanner";
import { useWebSocketStore } from "./store/websocket";

type Tab = "overview" | "funnel" | "heatmap" | "anomalies";

function App() {
  const [storeId, setStoreId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const connect = useWebSocketStore((s) => s.connect);

  useEffect(() => {
    if (storeId) {
      connect(storeId);
    }
  }, [storeId, connect]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "funnel", label: "Funnel" },
    { id: "heatmap", label: "Heatmap" },
    { id: "anomalies", label: "Anomalies" },
  ];

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "1rem" }}>
      <ReconnectBanner />

      <header style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem" }}>ReIntellect</h1>
        <StoreSelector selectedStoreId={storeId} onSelect={setStoreId} />
      </header>

      {storeId && (
        <>
          <nav style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: "0.5rem 1rem",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  background: activeTab === tab.id ? "#333" : "#fff",
                  color: activeTab === tab.id ? "#fff" : "#333",
                  cursor: "pointer",
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          <main style={{ display: "flex", gap: "1rem" }}>
            <section style={{ flex: 1 }}>
              {activeTab === "overview" && <OverviewScreen storeId={storeId} />}
              {activeTab === "funnel" && <PlaceholderScreen name="Funnel" />}
              {activeTab === "heatmap" && <PlaceholderScreen name="Heatmap" />}
              {activeTab === "anomalies" && <PlaceholderScreen name="Anomalies" />}
            </section>

            <aside style={{ width: "320px" }}>
              <LiveFeedPanel />
            </aside>
          </main>
        </>
      )}
    </div>
  );
}

/** Placeholder for screens not yet implemented (7.6, 7.7, 7.8). */
function PlaceholderScreen({ name }: { name: string }) {
  return (
    <div style={{ padding: "2rem", textAlign: "center", color: "#888" }}>
      {name} screen — not yet implemented
    </div>
  );
}

export default App;
