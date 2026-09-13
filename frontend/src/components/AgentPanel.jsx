import { useState } from "react";
import { mockPlan } from "../mocks";

export default function AgentPanel() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  function generate() {
    setLoading(true);
    // Mock — replaced with POST /agent/plan on day 3
    setTimeout(() => {
      setPlan(mockPlan);
      setLoading(false);
    }, 900);
  }

  return (
    <div style={s.wrap}>
      <div style={s.head}>
        <h3 style={s.title}>Recommended actions</h3>
        <button onClick={generate} style={s.btn} disabled={loading}>
          {loading ? "Analysing..." : "Generate plan"}
        </button>
      </div>

      {!plan && !loading && (
        <p style={s.empty}>
          The agent reads open reports, forecasts and response times, then ranks
          what to act on first.
        </p>
      )}

      {plan && plan.map((a) => (
        <div key={a.priority} style={s.card}>
          <div style={s.row}>
            <span style={s.rank}>{a.priority}</span>
            <div style={{ flex: 1 }}>
              <div style={s.action}>{a.action}</div>
              <div style={s.meta}>{a.ward} · {a.issue}</div>
              <div style={s.just}>{a.justification}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

const s = {
  wrap: { marginTop: 24 },
  head: { display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 12 },
  title: { fontSize: 14, fontWeight: 600, color: "#5f5e5a", margin: 0 },
  btn: { padding: "7px 14px", borderRadius: 6, border: "none",
         background: "#3d6b5c", color: "#fff", fontSize: 13,
         fontWeight: 600, cursor: "pointer" },
  empty: { fontSize: 13, color: "#7a7871", lineHeight: 1.5 },
  card: { padding: 14, marginBottom: 10, borderRadius: 8,
          background: "#f7f6f2", border: "1px solid #d3d1c7" },
  row: { display: "flex", gap: 12, alignItems: "flex-start" },
  rank: { width: 24, height: 24, borderRadius: "50%", background: "#3d6b5c",
          color: "#fff", fontSize: 13, fontWeight: 600, display: "flex",
          alignItems: "center", justifyContent: "center", flexShrink: 0 },
  action: { fontSize: 14, fontWeight: 600 },
  meta: { fontSize: 12, color: "#7a7871", marginTop: 2, textTransform: "capitalize" },
  just: { fontSize: 12.5, color: "#444441", marginTop: 8, lineHeight: 1.5,
          paddingTop: 8, borderTop: "1px solid #e0ded6" },
};