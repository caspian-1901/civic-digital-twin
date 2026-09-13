import { useState } from "react";

export default function CitizenForm() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [coords, setCoords] = useState(null);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState(null);

  function handleFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  function getLocation() {
    setStatus("Getting location...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({
          lat: pos.coords.latitude.toFixed(5),
          lng: pos.coords.longitude.toFixed(5),
        });
        setStatus("");
      },
      () => setStatus("Location access denied")
    );
  }

  function handleSubmit() {
    if (!file || !coords) {
      setStatus("Add a photo and your location first");
      return;
    }
    setStatus("Submitting...");
    // Mock response — replaced with a real API call on day 3
    setTimeout(() => {
      setResult({
        issue_class: "pothole",
        severity: "high",
        ward_id: 14,
        deduped: true,
        report_count: 12,
      });
      setStatus("");
    }, 600);
  }

  return (
    <div style={styles.page}>
      <h2 style={styles.title}>Report a civic issue</h2>

      <label style={styles.label}>Photo</label>
      <input type="file" accept="image/*" onChange={handleFile} />

      {preview && <img src={preview} alt="preview" style={styles.preview} />}

      <label style={styles.label}>Location</label>
      <button onClick={getLocation} style={styles.secondary}>
        Use my current location
      </button>
      {coords && (
        <p style={styles.coords}>
          {coords.lat}, {coords.lng}
        </p>
      )}

      <button onClick={handleSubmit} style={styles.primary}>
        Submit report
      </button>

      {status && <p style={styles.status}>{status}</p>}

      {result && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Report received</h3>
          <p><strong>Detected:</strong> {result.issue_class}</p>
          <p><strong>Severity:</strong> {result.severity}</p>
          <p><strong>Ward:</strong> {result.ward_id}</p>
          {result.deduped && (
            <p style={styles.merged}>
              Merged with an existing report — now {result.report_count} people
              have reported this.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: { maxWidth: 480, margin: "0 auto", padding: 24,
          fontFamily: "system-ui, sans-serif", color: "#23231f" },
  title: { fontSize: 20, fontWeight: 600, marginBottom: 20 },
  label: { display: "block", marginTop: 18, marginBottom: 6,
           fontSize: 13, fontWeight: 600, color: "#5f5e5a" },
  preview: { width: "100%", borderRadius: 8, marginTop: 12,
             border: "1px solid #d3d1c7" },
  coords: { fontSize: 13, color: "#5f5e5a", marginTop: 8 },
  secondary: { padding: "8px 14px", borderRadius: 6,
               border: "1px solid #b4b2a9", background: "#f7f6f2",
               cursor: "pointer", fontSize: 14 },
  primary: { display: "block", width: "100%", marginTop: 24,
             padding: "12px", borderRadius: 6, border: "none",
             background: "#3d6b5c", color: "#fff", fontSize: 15,
             fontWeight: 600, cursor: "pointer" },
  status: { marginTop: 12, fontSize: 13, color: "#7a7871" },
  card: { marginTop: 24, padding: 16, borderRadius: 8,
          background: "#f7f6f2", border: "1px solid #d3d1c7" },
  cardTitle: { fontSize: 15, fontWeight: 600, marginTop: 0, marginBottom: 10 },
  merged: { marginTop: 10, padding: 10, borderRadius: 6,
            background: "#e8efe9", fontSize: 13, color: "#2f5347" },
};