import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://civic:civic@localhost:5432/civic"
)

def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )

def get_ward_for_location(lat: float, lng: float):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name
                FROM wards
                WHERE ST_Covers(
                    geom,
                    ST_SetSRID(ST_Point(%s, %s), 4326)
                )
                LIMIT 1
                """,
                (lng, lat),
            )
            return cur.fetchone()

def get_reports(resolved: bool = False):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    ward_id,
                    issue_class,
                    severity,
                    report_count,
                    ST_Y(location) AS lat,
                    ST_X(location) AS lng,
                    created_at
                FROM reports
                WHERE resolved = %s
                ORDER BY created_at DESC
                """,
                (resolved,),
            )
            return cur.fetchall()

def create_report(
    ward_id: int,
    issue_class: str,
    severity: str,
    lat: float,
    lng: float,
    image_path: str | None = None,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reports (
                    ward_id,
                    issue_class,
                    severity,
                    report_count,
                    lat,
                    lng,
                    location,
                    image_path
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    1,
                    %s,
                    %s,
                    ST_SetSRID(ST_Point(%s, %s), 4326),
                    %s
                )
                RETURNING
                    id,
                    issue_class,
                    severity,
                    ward_id,
                    report_count
                """,
                (
                    ward_id,
                    issue_class,
                    severity,
                    lat,
                    lng,
                    lng,
                    lat,
                    image_path,
                ),
            )

            report = cur.fetchone()
            conn.commit()
            return report

def find_duplicate_report(
    issue_class: str,
    lat: float,
    lng: float,
    radius_meters: float = 50.0,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    ward_id,
                    issue_class,
                    severity,
                    report_count
                FROM reports
                WHERE resolved = FALSE
                  AND issue_class = %s
                  AND ST_DWithin(
                      location::geography,
                      ST_SetSRID(ST_Point(%s, %s), 4326)::geography,
                      %s
                  )
                ORDER BY
                    ST_Distance(
                        location::geography,
                        ST_SetSRID(ST_Point(%s, %s), 4326)::geography
                    )
                LIMIT 1
                """,
                (
                    issue_class,
                    lng,
                    lat,
                    radius_meters,
                    lng,
                    lat,
                ),
            )
            return cur.fetchone()


def increment_report_count(report_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE reports
                SET report_count = report_count + 1
                WHERE id = %s
                RETURNING
                    id,
                    ward_id,
                    issue_class,
                    severity,
                    report_count
                """,
                (report_id,),
            )

            report = cur.fetchone()
            conn.commit()
            return report
