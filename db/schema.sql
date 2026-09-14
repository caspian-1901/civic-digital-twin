CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS wards (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wards_geom
ON wards
USING GIST (geom);


CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,

    ward_id INTEGER NOT NULL
        REFERENCES wards(id),

    issue_class TEXT NOT NULL
        CHECK (issue_class IN ('pothole', 'waterlogging', 'garbage', 'none')),

    severity TEXT NOT NULL
        CHECK (severity IN ('low', 'medium', 'high')),

    report_count INTEGER NOT NULL DEFAULT 1
        CHECK (report_count >= 1),

    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,

    location GEOMETRY(POINT, 4326) NOT NULL,

    image_path TEXT,

    resolved BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    resolved_at TIMESTAMPTZ,

    CONSTRAINT resolved_timestamp_consistency
        CHECK (
            (resolved = FALSE AND resolved_at IS NULL)
            OR
            (resolved = TRUE AND resolved_at IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_reports_ward_id
ON reports (ward_id);

CREATE INDEX IF NOT EXISTS idx_reports_resolved
ON reports (resolved);

CREATE INDEX IF NOT EXISTS idx_reports_created_at
ON reports (created_at);

CREATE INDEX IF NOT EXISTS idx_reports_location
ON reports
USING GIST (location);


CREATE TABLE IF NOT EXISTS report_resolutions (
    id BIGSERIAL PRIMARY KEY,

    report_id BIGINT NOT NULL UNIQUE
        REFERENCES reports(id)
        ON DELETE CASCADE,

    resolved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    hours_open DOUBLE PRECISION NOT NULL
        CHECK (hours_open >= 0)
);


CREATE INDEX IF NOT EXISTS idx_report_resolutions_report_id
ON report_resolutions (report_id);
