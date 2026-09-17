from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware

from services.api.db import (
    get_reports,
    get_ward_for_location,
    create_report,
    find_duplicate_report,
    increment_report_count,
)

app = FastAPI(
    title="Civic Digital Twin Main API",
    version="1.0.0",
)

# Required by CONTRACTS.md
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reports")
def list_reports(
    resolved: bool = Query(default=False)
):
    return get_reports(resolved)

@app.post("/reports")
async def submit_report(
    image: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
):
    # 1. Send image to the Vision service
    image_bytes = await image.read()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8001/detect",
                files={
                    "image": (
                        image.filename,
                        image_bytes,
                        image.content_type,
                    )
                },
            )
            response.raise_for_status()
            detection = response.json()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Vision service unavailable: {exc}",
        )

    issue_class = detection.get("class")
    severity = detection.get("severity")

    if issue_class not in {"pothole", "waterlogging", "garbage"}:
        raise HTTPException(
            status_code=400,
            detail="No supported civic issue detected",
        )

    if severity not in {"low", "medium", "high"}:
        raise HTTPException(
            status_code=502,
            detail="Invalid severity returned by Vision service",
        )

    # 2. Determine the BMC ward from the coordinates
    ward = get_ward_for_location(lat, lng)

    if ward is None:
        raise HTTPException(
            status_code=400,
            detail="Location is outside the supported ward boundaries",
        )

    # 3. Look for an existing nearby unresolved report
    duplicate = find_duplicate_report(
        issue_class=issue_class,
        lat=lat,
        lng=lng,
    )

    if duplicate:
        report = increment_report_count(duplicate["id"])

        return {
            "id": report["id"],
            "issue_class": report["issue_class"],
            "severity": report["severity"],
            "ward_id": report["ward_id"],
            "deduped": True,
            "report_count": report["report_count"],
        }

    # 4. Otherwise create a new report
    report = create_report(
        ward_id=ward["id"],
        issue_class=issue_class,
        severity=severity,
        lat=lat,
        lng=lng,
        image_path=None,
    )

    return {
        "id": report["id"],
        "issue_class": report["issue_class"],
        "severity": report["severity"],
        "ward_id": report["ward_id"],
        "deduped": False,
        "report_count": report["report_count"],
    }
