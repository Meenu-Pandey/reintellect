/**
 * Funnel screen.
 *
 * Renders a Recharts BarChart with zone names on X-axis and visitor_count on Y-axis.
 * Shows drop-off rate between stages as percentage labels.
 * Uses useFunnel hook with 30s auto-refresh.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from "recharts";
import { useFunnel } from "../../api/hooks/useFunnel";

interface Props {
  storeId: string;
}

export function FunnelScreen({ storeId }: Props) {
  const { data, isLoading, error } = useFunnel(storeId);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <div style={{ color: "#dc2626" }}>Failed to load funnel data.</div>;
  }

  if (!data || !data.data_available || data.stages.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#888" }}>
        No funnel data available yet.
      </div>
    );
  }

  const stages = data.stages;
  const chartData = stages.map((stage, i) => {
    const prev = i > 0 ? stages[i - 1].visitor_count : data.total_visitors;
    const dropOff = prev > 0 ? ((prev - stage.visitor_count) / prev) * 100 : 0;
    return {
      name: stage.zone_name,
      visitors: stage.visitor_count,
      dropOff: Math.round(dropOff),
      entryRate: (stage.entry_rate * 100).toFixed(1),
    };
  });

  const colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#22c55e", "#ec4899"];

  return (
    <div>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Visitor Funnel</h2>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-30}
            textAnchor="end"
            height={80}
            fontSize={12}
          />
          <YAxis label={{ value: "Visitors", angle: -90, position: "insideLeft" }} />
          <Tooltip
            content={({ payload, active }) => {
              if (!active || !payload || !payload.length) return null;
              const d = payload[0].payload as { name: string; visitors: number; dropOff: number; entryRate: string };
              return (
                <div style={{ background: "#fff", border: "1px solid #ccc", padding: "0.5rem", borderRadius: "4px", fontSize: "0.8rem" }}>
                  <div style={{ fontWeight: 600 }}>{d.name}</div>
                  <div>{d.visitors} visitors</div>
                  <div>Drop-off: {d.dropOff}%</div>
                  <div>Entry rate: {d.entryRate}%</div>
                </div>
              );
            }}
          />
          <Bar dataKey="visitors" radius={[4, 4, 0, 0]}>
            {chartData.map((_entry, index) => (
              <Cell key={index} fill={colors[index % colors.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div style={{ marginTop: "1rem", fontSize: "0.8rem", color: "#666" }}>
        {chartData.map((d, i) => (
          <span key={i} style={{ marginRight: "1.5rem" }}>
            {d.name}: {d.visitors} visitors
            {i > 0 && <span style={{ color: "#dc2626" }}> (↓{d.dropOff}%)</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div style={{ padding: "2rem" }}>
      <div
        style={{
          height: "350px",
          background: "#f3f4f6",
          borderRadius: "8px",
          animation: "pulse 1.5s infinite",
        }}
      />
    </div>
  );
}
