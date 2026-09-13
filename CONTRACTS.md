# API Contracts

All services return JSON. Field names below are exact — do not rename.

## Main API (Person 1) — port 8000

### POST /reports
Request: multipart/form-data — `image` (file), `lat` (float), `lng` (float)
```json
{ "id": 1, "issue_class": "pothole", "severity": "high",
  "ward_id": 14, "deduped": true, "report_count": 12 }
```

### GET /reports?resolved=false
```json
[{ "id": 1, "ward_id": 14, "issue_class": "pothole", "severity": "high",
   "report_count": 11, "lat": 19.0760, "lng": 72.8777,
   "created_at": "2026-09-10T08:30:00" }]
```

### POST /reports/{id}/resolve
```json
{ "id": 1, "resolved_at": "2026-09-11T14:00:00", "hours_open": 29.5 }
```

### GET /stats/response-times
```json
[{ "ward_id": 14, "avg_hours": 31.2, "open_count": 4 }]
```

## Forecast (Person 1) — port 8002

### GET /forecast?ward_id=14&hours=48
```json
[{ "ts": "2026-09-11T00:00:00", "value": 92.4 }]
```

## Vision (Person 2) — port 8001

### POST /detect
Request: multipart/form-data — `image` (file)
```json
{ "class": "pothole", "confidence": 0.87, "bbox_area": 45200,
  "image_area": 307200, "severity": "high" }
```
`class` is one of: `pothole`, `waterlogging`, `garbage`, `none`

## Agent (Person 2) — port 8003

### POST /agent/plan
```json
[{ "ward": "Ward 14", "issue": "pothole", "priority": 1,
   "action": "Dispatch PWD team before 7 AM",
   "justification": "High severity, 11 corroborating reports" }]
```

## Notes

CORS must be enabled on every FastAPI service from day 1, or the frontend
cannot call anything:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
```

Severity buckets: bbox_area/image_area below 0.05 low, 0.05–0.15 medium,
above 0.15 high. Confidence below 0.4 returns `class: "none"`.

Any change to these shapes must be agreed by the whole group first.