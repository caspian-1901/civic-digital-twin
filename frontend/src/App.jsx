import { useState } from "react";
import CitizenForm from "./components/CitizenForm";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [view, setView] = useState("citizen");
  return (
    <div>
      <nav style={{ display: "flex", gap: 8, padding: 12,
                    borderBottom: "1px solid #d3d1c7", background: "#f7f6f2" }}>
        <button onClick={() => setView("citizen")}>Citizen</button>
        <button onClick={() => setView("officer")}>Officer</button>
      </nav>
      {view === "citizen" ? <CitizenForm /> : <Dashboard />}
    </div>
  );
}