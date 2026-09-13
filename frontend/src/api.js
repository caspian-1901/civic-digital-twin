const API = "http://localhost:8000";
const FORECAST = "http://localhost:8002";
const AGENT = "http://localhost:8003";

export const getReports = () =>
  fetch(`${API}/reports?resolved=false`).then(r => r.json());

export const resolveReport = (id) =>
  fetch(`${API}/reports/${id}/resolve`, { method: "POST" }).then(r => r.json());

export const getForecast = (wardId, hours = 48) =>
  fetch(`${FORECAST}/forecast?ward_id=${wardId}&hours=${hours}`).then(r => r.json());

export const getPlan = () =>
  fetch(`${AGENT}/agent/plan`, { method: "POST" }).then(r => r.json());

export const submitReport = (file, lat, lng) => {
  const fd = new FormData();
  fd.append("image", file);
  fd.append("lat", lat);
  fd.append("lng", lng);
  return fetch(`${API}/reports`, { method: "POST", body: fd }).then(r => r.json());
};