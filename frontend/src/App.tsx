/**
 * Main application component.
 *
 * Renders StoreSelector, tab navigation, active screen,
 * live event feed, and WebSocket reconnect indicator.
 *
 * Responsive layout: 1280px–2560px, no horizontal overflow.
 */

import { useEffect, useState } from "react";
import { StoreSelector } from "./components/StoreSelector";
import { OverviewScreen } from "./components/Overview/OverviewScreen";
import { FunnelScreen } from "./components/Funnel/FunnelScreen";
import { HeatmapScreen } from "./components/Heatmap/HeatmapScreen";
import { AnomaliesScreen } from "./components/Anomalies/AnomaliesScreen";
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
    <div
      style={{
        fontFamily: "system-ui, -apple-system, sans-serif",
        padding: "1rem",
        maxWidth: "2560px",
        margin: "0 auto",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <ReconnectBanner />

      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.5rem", whiteSpace: "nowrap" }}>
          ReIntellect
        </h1>
        <StoreSelector selectedStoreId={storeId} onSelect={setStoreId} />
      </header>

      {storeId && (
        <>
          <nav
            style={{
              display: "flex",
              gap: "0.5rem",
              marginBottom: "1rem",
              flexWrap: "wrap",
            }}
          >
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
                  fontSize: "0.85rem",
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          <main
            style={{
              display: "grid",
              gridTemplateColumns: "1fr minmax(280px, 320px)",
              gap: "1rem",
              minWidth: 0,
            }}
          >
            <section style={{ minWidth: 0, overflow: "hidden" }}>
              {activeTab === "overview" && <OverviewScreen storeId={storeId} />}
              {activeTab === "funnel" && <FunnelScreen storeId={storeId} />}
              {activeTab === "heatmap" && <HeatmapScreen storeId={storeId} />}
              {activeTab === "anomalies" && <AnomaliesScreen storeId={storeId} />}
            </section>

            <aside style={{ minWidth: 0 }}>
              <LiveFeedPanel />
            </aside>
          </main>
        </>
      )}
    </div>
  );
}

export default App;
