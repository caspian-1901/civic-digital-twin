# AI Digital Twin for Smart Cities

Closed-loop urban digital twin combining citizen civic-issue reporting,
air-quality forecasting, and an agentic decision layer.

## Team and branches
| Person | Area | Branch |
|---|---|---|
| 1 | Backend, database, forecasting | `feat/backend` |
| 2 | Vision, deduplication, agent | `feat/models` |
| 3 | Frontend | `feat/frontend` |
| 4 | Report, QA | `docs/report` |

## Python version
Use 3.11. Not 3.13 — torch and ultralytics have wheel availability issues.

## Ports
| Service | Port |
|---|---|
| API + DB | 8000 |
| Vision | 8001 |
| Forecast | 8002 |
| Agent | 8003 |
| Frontend | 5173 |

## Setup