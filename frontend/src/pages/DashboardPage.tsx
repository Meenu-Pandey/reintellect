import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Zap, Clock, ArrowLeft, Activity } from "lucide-react";
import { theme } from "../styles/theme";
import { OverviewScreen } from "../components/Overview/OverviewScreen";
import { FunnelScreen } from "../components/Funnel/FunnelScreen";
import { HeatmapScreen } from "../components/Heatmap/HeatmapScreen";
import { AnomaliesScreen } from "../components/Anomalies/AnomaliesScreen";
import { LiveFeedPanel } from "../components/LiveFeed/LiveFeedPanel";
import { useWebSocketStore } from "../store/websocket";

type Tab = "overview" | "funnel" | "heatmap" | "anomalies";

export function DashboardPage() {
  const [storeId] = useState("purplle-brigade-road");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [clock, setClock] = useState(getTime());
  const connect = useWebSocketStore((s) => s.connect);
  const connectionStatus = useWebSocketStore((s) => s.connectionStatus);
  const navigate = useNavigate();

  useEffect(() => { connect(storeId); }, [storeId, connect]);
  useEffect(() => { const i = setInterval(() => setClock(getTime()), 1000); return () => clearInterval(i); }, []);

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "funnel", label: "Funnel" },
    { id: "heatmap", label: "Heatmap" },
    { id: "anomalies", label: "Anomalies" },
  ];

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: theme.bg.primary, fontFamily: theme.font, color: theme.text.primary, overflow: "hidden" }}>
      {/* Header */}
      <header style={{ display: "flex", alignItems: "center", padding: "0.6rem 1.25rem", borderBottom: `1px solid ${theme.border}`, gap: "0.75rem", flexShrink: 0 }}>
        <button onClick={() => navigate("/")} style={{ display: "flex", alignItems: "center", gap: "0.3rem", background: "none", border: "none", color: theme.text.muted, cursor: "pointer", fontSize: "0.82rem" }}>
          <ArrowLeft size={14} /> Home
        </button>
        <div style={{ width: 1, height: 16, background: theme.border }} />
        <Zap size={16} color={theme.accent.purple} />
        <span style={{ fontWeight: 700, fontSize: "1rem" }}>ReIntellect</span>
        <span style={{ fontSize: "0.75rem", color: theme.text.muted, padding: "0.15rem 0.45rem", background: theme.bg.elevated, borderRadius: 4 }}>Purplle Brigade Road</span>
        <div style={{ flex: 1 }} />
        {/* Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: connectionStatus === "connected" ? theme.accent.green : theme.accent.amber, animation: "pulse 2s infinite" }} />
          <span style={{ fontSize: "0.75rem", color: theme.text.muted }}>{connectionStatus === "connected" ? "Live" : "Reconnecting"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", color: theme.text.muted }}>
          <Clock size={13} />
          <span style={{ fontSize: "0.8rem", fontFamily: "monospace" }}>{clock}</span>
        </div>
      </header>

      {/* Tabs */}
      <nav style={{ display: "flex", gap: "0.25rem", padding: "0.5rem 1.25rem", borderBottom: `1px solid ${theme.border}`, flexShrink: 0 }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "0.4rem 0.85rem",
              border: "none",
              borderRadius: theme.radiusXs,
              background: activeTab === tab.id ? theme.bg.elevated : "transparent",
              color: activeTab === tab.id ? theme.text.primary : theme.text.muted,
              fontSize: "0.85rem",
              fontWeight: activeTab === tab.id ? 600 : 400,
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.75rem", color: theme.text.muted }}>
          <Activity size={12} /> Processing
        </div>
      </nav>

      {/* Content */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr minmax(240px, 300px)", gap: "0.75rem", padding: "0.75rem clamp(0.75rem, 2vw, 1.25rem)", minHeight: 0, overflow: "hidden" }}>
        <main style={{ overflow: "auto", minHeight: 0, paddingRight: "0.25rem" }}>
          {activeTab === "overview" && <OverviewScreen storeId={storeId} />}
          {activeTab === "funnel" && <FunnelScreen storeId={storeId} />}
          {activeTab === "heatmap" && <HeatmapScreen storeId={storeId} />}
          {activeTab === "anomalies" && <AnomaliesScreen storeId={storeId} />}
        </main>
        <aside style={{ overflow: "auto", minHeight: 0 }}>
          <LiveFeedPanel />
        </aside>
      </div>
    </div>
  );
}

function getTime() {
  return new Date().toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }) + " IST";
}
