import { useState } from "react";
import CityMap from "./CityMap";
import ForecastChart from "./ForecastChart";
import AgentPanel from "./AgentPanel";
import { mockReports, mockForecast } from "../mocks";

const order = { high: 0, medium: 1, low: 2 };

export default function Dashboard() {
  const [reports, setReports] = useState(mockReports);
  const [selected, setSelected] = useState(null);

  const sorted = [...reports].sort(
    (a, b) => order[a.severity] - order[b.severity] || b.report_count - a.report_count
  );

  function resolve(id) {
    setReports(reports.filter((r) => r.id !== id));
  }

  return (
    <div style={s.page}>
      <h2 style={s.title}>Municipal operations dashboard</h2>
      <div style={s.grid}>
        <div>
          <CityMap reports={reports} onSelect={setSelected} />
          <h3 style={s.sub}>
            AQI forecast — next 48 hours{selected ? ` (Ward ${selected.ward_id})` : ""}
          </h3>
          <ForecastChart data={mockForecast} />
        </div>
        <div>
          <h3 style={s.sub}>Open issues ({sorted.length})</h3>
          {sorted.map((r) => (
            <div key={r.id} style={s.ticket}>
              <div style={{ ...s.dot, background: dot[r.severity] }} />
              <div style={{ flex: 1 }}>
                <div style={s.tTitle}>{r.issue_class} — Ward {r.ward_id}</div>
                <div style={s.tMeta}>{r.severity} · {r.report_count} reports</div>
              </div>
              <button onClick={() => resolve(r.id)} style={s.resolve}>Resolve</button>
            </div>
          ))}
          <AgentPanel />
        </div>
      </div>
    </div>
  );
}

const dot = { high: "#b3543f", medium: "#c19a4b", low: "#6b8f7a" };
const s = {
  page: { padding: 24, fontFamily: "system-ui, sans-serif", color: "#23231f" },
  title: { fontSize: 20, fontWeight: 600, marginBottom: 20 },
  grid: { display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 24 },
  sub: { fontSize: 14, fontWeight: 600, color: "#5f5e5a", margin: "20px 0 10px" },
  ticket: { display: "flex", alignItems: "center", gap: 10, padding: 12,
            marginBottom: 8, borderRadius: 8, background: "#f7f6f2",
            border: "1px solid #d3d1c7" },
  dot: { width: 10, height: 10, borderRadius: "50%", flexShrink: 0 },
  tTitle: { fontSize: 14, fontWeight: 600, textTransform: "capitalize" },
  tMeta: { fontSize: 12, color: "#7a7871", marginTop: 2 },
  resolve: { padding: "6px 10px", fontSize: 12, borderRadius: 5,
             border: "1px solid #b4b2a9", background: "#fff", cursor: "pointer" },
};