import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

const colors = { high: "#b3543f", medium: "#c19a4b", low: "#6b8f7a" };

function makeIcon(severity) {
  return L.divIcon({
    className: "",
    html: `<div style="width:16px;height:16px;border-radius:50%;
           background:${colors[severity]};border:2px solid #fff;
           box-shadow:0 0 3px rgba(0,0,0,.4)"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

export default function CityMap({ reports, onSelect }) {
  return (
    <MapContainer center={[19.076, 72.877]} zoom={11}
      style={{ height: 420, borderRadius: 8 }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      {reports.map((r) => (
        <Marker key={r.id} position={[r.lat, r.lng]} icon={makeIcon(r.severity)}
          eventHandlers={{ click: () => onSelect(r) }}>
          <Popup>
            <strong>{r.issue_class}</strong><br />
            Severity: {r.severity}<br />
            {r.report_count} reports
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}