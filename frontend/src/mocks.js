export const mockReports = [
  { id: 1, ward_id: 14, issue_class: "pothole", severity: "high",
    report_count: 11, lat: 19.0760, lng: 72.8777, created_at: "2026-09-10T08:30:00" },
  { id: 2, ward_id: 9, issue_class: "waterlogging", severity: "high",
    report_count: 7, lat: 19.0330, lng: 72.8560, created_at: "2026-09-10T09:15:00" },
  { id: 3, ward_id: 22, issue_class: "garbage", severity: "medium",
    report_count: 3, lat: 19.1136, lng: 72.8697, created_at: "2026-09-10T10:00:00" },
  { id: 4, ward_id: 14, issue_class: "pothole", severity: "low",
    report_count: 1, lat: 19.0820, lng: 72.8810, created_at: "2026-09-10T11:20:00" },
  { id: 5, ward_id: 5, issue_class: "waterlogging", severity: "medium",
    report_count: 4, lat: 19.0176, lng: 72.8562, created_at: "2026-09-10T12:00:00" },
];

export const mockForecast = Array.from({ length: 48 }, (_, i) => ({
  ts: `2026-09-11T${String(i % 24).padStart(2, "0")}:00:00`,
  value: 80 + Math.round(40 * Math.sin(i / 4) + Math.random() * 15),
}));

export const mockPlan = [
  { ward: "Ward 14", issue: "pothole", priority: 1,
    action: "Dispatch PWD team before 7 AM",
    justification: "High severity, 11 corroborating reports, congestion forecast elevated tomorrow morning" },
  { ward: "Ward 9", issue: "waterlogging", priority: 2,
    action: "Deploy pump unit today",
    justification: "High severity with 7 reports, rainfall trend worsening" },
];