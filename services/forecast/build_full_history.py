import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OPENAQ_API_KEY not found in .env")

HEADERS = {
    "X-API-Key": API_KEY
}

# Complete months we have already audited
START_MONTH = "2025-03-01"
END_MONTH = "2026-09-01"   # exclusive, so through Aug 2026

METADATA_FILE = "sensor_metadata_audit.csv"

RAW_DIR = Path("full_history_raw_months")
RAW_DIR.mkdir(exist_ok=True)

FINAL_RAW_FILE = "full_history_raw_sensor_hourly.csv"
STATION_FILE = "full_history_station_hourly.csv"
WARD_FILE = "full_history_ward_hourly.csv"
WARD_SUMMARY_FILE = "full_history_ward_summary.csv"


# ============================================================
# LOAD SENSOR METADATA
# ============================================================

metadata = pd.read_csv(METADATA_FILE)

metadata["first_datetime"] = pd.to_datetime(
    metadata["first_datetime"],
    utc=True,
    errors="coerce"
)

metadata["last_datetime"] = pd.to_datetime(
    metadata["last_datetime"],
    utc=True,
    errors="coerce"
)

print("Sensor records loaded:", len(metadata))
print("Stations:", metadata["location_id"].nunique())
print("Wards:", metadata["ward_name"].nunique())


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


def get_with_retry(url, params, max_attempts=5):
    """
    Call OpenAQ with retries for temporary API/network errors.
    """

    for attempt in range(1, max_attempts + 1):

        try:
            response = session.get(
                url,
                params=params,
                timeout=60
            )

            if response.status_code == 200:
                return response

            if response.status_code == 429:
                wait = attempt * 5
                print(
                    f"    Rate limited. Waiting {wait}s..."
                )
                time.sleep(wait)
                continue

            if response.status_code >= 500:
                wait = attempt * 3
                print(
                    f"    Server error "
                    f"{response.status_code}. "
                    f"Waiting {wait}s..."
                )
                time.sleep(wait)
                continue

            print(
                "    HTTP error:",
                response.status_code
            )

            return None

        except requests.RequestException as e:

            wait = attempt * 3

            print(
                f"    Request error: {e}"
            )

            print(
                f"    Retrying in {wait}s..."
            )

            time.sleep(wait)

    return None


# ============================================================
# MONTH-BY-MONTH DOWNLOAD
# ============================================================

month_starts = pd.date_range(
    start=START_MONTH,
    end=END_MONTH,
    freq="MS",
    inclusive="left",
    tz="Asia/Kolkata"
)

for month_start_ist in month_starts:

    month_end_ist = (
        month_start_ist
        + pd.offsets.MonthBegin(1)
    )

    month_name = month_start_ist.strftime("%Y-%m")

    output_file = RAW_DIR / (
        f"{month_name}_sensor_hourly.csv"
    )

    print("\n======================================")
    print("MONTH:", month_name)
    print("======================================")

    # If month was already successfully downloaded,
    # do not download it again.
    if output_file.exists():

        existing = pd.read_csv(output_file)

        print(
            "Already downloaded:",
            len(existing),
            "rows"
        )

        continue

    # Convert local Mumbai month boundaries to UTC.
    #
    # Example:
    # 2025-03-01 00:00 IST
    # becomes
    # 2025-02-28 18:30 UTC
    month_start_utc = (
        month_start_ist.tz_convert("UTC")
    )

    month_end_utc = (
        month_end_ist.tz_convert("UTC")
    )

    active = metadata[
        (
            metadata["first_datetime"]
            < month_end_utc
        )
        &
        (
            metadata["last_datetime"]
            >= month_start_utc
        )
    ].copy()

    print(
        "Active sensors:",
        len(active)
    )

    print(
        "Stations:",
        active["location_id"].nunique()
    )

    print(
        "Wards:",
        active["ward_name"].nunique()
    )

    month_rows = []

    for _, sensor in active.iterrows():

        sensor_id = int(
            sensor["sensor_id"]
        )

        print(
            "  Downloading:",
            sensor["ward_name"],
            "|",
            sensor["station_name"],
            "|",
            sensor_id
        )

        url = (
            "https://api.openaq.org/v3/"
            f"sensors/{sensor_id}/hours"
        )

        page = 1

        while True:

            params = {
                "datetime_from":
                    month_start_utc.isoformat(),

                "datetime_to":
                    month_end_utc.isoformat(),

                "limit": 1000,

                "page": page
            }

            response = get_with_retry(
                url,
                params
            )

            if response is None:
                print(
                    "    Skipping remaining "
                    "pages for this sensor."
                )
                break

            payload = response.json()

            results = payload.get(
                "results",
                []
            )

            if not results:
                break

            for record in results:

                period = (
                    record.get("period")
                    or {}
                )

                datetime_from = (
                    period
                    .get("datetimeFrom", {})
                    .get("utc")
                )

                value = record.get("value")

                if (
                    datetime_from is None
                    or value is None
                ):
                    continue

                month_rows.append({
                    "datetime_utc":
                        datetime_from,

                    "location_id":
                        sensor["location_id"],

                    "station_name":
                        sensor["station_name"],

                    "latitude":
                        sensor["latitude"],

                    "longitude":
                        sensor["longitude"],

                    "ward_gid":
                        sensor["ward_gid"],

                    "ward_name":
                        sensor["ward_name"],

                    "sensor_id":
                        sensor_id,

                    "pm25":
                        value
                })

            if len(results) < 1000:
                break

            page += 1

            time.sleep(0.15)

        time.sleep(0.15)

    month_df = pd.DataFrame(
        month_rows
    )

    month_df.to_csv(
        output_file,
        index=False
    )

    print(
        "Saved:",
        output_file
    )

    print(
        "Rows:",
        len(month_df)
    )


# ============================================================
# COMBINE ALL MONTHLY RAW FILES
# ============================================================

print("\n======================================")
print("COMBINING MONTHLY FILES")
print("======================================")

monthly_files = sorted(
    RAW_DIR.glob(
        "*_sensor_hourly.csv"
    )
)

if not monthly_files:
    raise ValueError(
        "No monthly files were created."
    )

frames = []

for file in monthly_files:

    df = pd.read_csv(file)

    if not df.empty:
        frames.append(df)

raw = pd.concat(
    frames,
    ignore_index=True
)

print(
    "Raw rows before cleaning:",
    len(raw)
)


# ============================================================
# CLEAN RAW OBSERVATIONS
# ============================================================

raw["datetime_utc"] = pd.to_datetime(
    raw["datetime_utc"],
    utc=True,
    errors="coerce"
)

raw["pm25"] = pd.to_numeric(
    raw["pm25"],
    errors="coerce"
)

raw = raw.dropna(
    subset=[
        "datetime_utc",
        "pm25"
    ]
)

# PM2.5 concentration cannot be negative
raw = raw[
    raw["pm25"] >= 0
].copy()

# Remove exact duplicated API observations
raw = raw.drop_duplicates(
    subset=[
        "sensor_id",
        "datetime_utc"
    ]
)

# Convert to Mumbai local time.
#
# OpenAQ observations such as 18:30 UTC
# become exactly 00:00 IST.
raw["datetime"] = (
    raw["datetime_utc"]
    .dt.tz_convert(
        "Asia/Kolkata"
    )
)

# Normalize only after converting to local time.
raw["datetime"] = (
    raw["datetime"]
    .dt.floor("h")
)

raw = raw.sort_values(
    [
        "datetime",
        "ward_gid",
        "location_id",
        "sensor_id"
    ]
)

raw.to_csv(
    FINAL_RAW_FILE,
    index=False
)

print(
    "Clean raw observations:",
    len(raw)
)


# ============================================================
# SENSOR -> PHYSICAL STATION
# ============================================================

station_hourly = (
    raw.groupby(
        [
            "ward_gid",
            "ward_name",
            "location_id",
            "station_name",
            "datetime"
        ],
        as_index=False
    )
    .agg(
        pm25=(
            "pm25",
            "median"
        ),
        sensors_reporting=(
            "sensor_id",
            "nunique"
        )
    )
)

station_hourly.to_csv(
    STATION_FILE,
    index=False
)

print(
    "Station-hour rows:",
    len(station_hourly)
)


# ============================================================
# PHYSICAL STATIONS -> WARD
# ============================================================

ward_observed = (
    station_hourly.groupby(
        [
            "ward_gid",
            "ward_name",
            "datetime"
        ],
        as_index=False
    )
    .agg(
        pm25=(
            "pm25",
            "median"
        ),
        stations_reporting=(
            "location_id",
            "nunique"
        )
    )
)


# ============================================================
# BUILD COMPLETE WARD x HOUR GRID
# ============================================================

full_start = pd.Timestamp(
    START_MONTH,
    tz="Asia/Kolkata"
)

full_end = pd.Timestamp(
    END_MONTH,
    tz="Asia/Kolkata"
)

hours = pd.date_range(
    start=full_start,
    end=full_end,
    freq="h",
    inclusive="left"
)

wards = (
    metadata[
        [
            "ward_gid",
            "ward_name"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        "ward_gid"
    )
)

grid = (
    wards.assign(key=1)
    .merge(
        pd.DataFrame({
            "datetime": hours,
            "key": 1
        }),
        on="key"
    )
    .drop(
        columns="key"
    )
)

ward_hourly = grid.merge(
    ward_observed,
    on=[
        "ward_gid",
        "ward_name",
        "datetime"
    ],
    how="left"
)

ward_hourly = ward_hourly.sort_values(
    [
        "ward_gid",
        "datetime"
    ]
)

ward_hourly.to_csv(
    WARD_FILE,
    index=False
)


# ============================================================
# WARD QUALITY SUMMARY
# ============================================================

summary_rows = []

for (
    ward_gid,
    ward_name
), group in ward_hourly.groupby(
    [
        "ward_gid",
        "ward_name"
    ]
):

    group = group.sort_values(
        "datetime"
    )

    present = (
        group["pm25"]
        .notna()
    )

    completeness = (
        present.mean()
        * 100
    )

    # Completely observed 24-hour windows
    valid_24 = (
        present
        .astype(int)
        .rolling(24)
        .sum()
        .eq(24)
        .sum()
    )

    # Completely observed 72-hour windows
    valid_72 = (
        present
        .astype(int)
        .rolling(72)
        .sum()
        .eq(72)
        .sum()
    )

    # Longest consecutive missing run
    longest_gap = 0
    current_gap = 0

    for value in present:

        if value:
            current_gap = 0
        else:
            current_gap += 1
            longest_gap = max(
                longest_gap,
                current_gap
            )

    summary_rows.append({
        "ward_gid":
            ward_gid,

        "ward_name":
            ward_name,

        "expected_hours":
            len(group),

        "observed_hours":
            int(present.sum()),

        "completeness_pct":
            round(
                completeness,
                2
            ),

        "valid_24h_windows":
            int(valid_24),

        "valid_72h_windows":
            int(valid_72),

        "longest_missing_gap_hours":
            int(longest_gap)
    })


ward_summary = pd.DataFrame(
    summary_rows
)

ward_summary = ward_summary.sort_values(
    "completeness_pct",
    ascending=False
)

ward_summary.to_csv(
    WARD_SUMMARY_FILE,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n======================================")
print("FULL HISTORY BUILD COMPLETE")
print("======================================")

print(
    "Period:",
    full_start,
    "to",
    full_end
)

print(
    "Wards:",
    len(ward_summary)
)

print(
    "Median ward completeness:",
    round(
        ward_summary[
            "completeness_pct"
        ].median(),
        2
    ),
    "%"
)

print(
    "\nWard summary:\n"
)

print(
    ward_summary.to_string(
        index=False
    )
)

print("\nSaved:")
print(FINAL_RAW_FILE)
print(STATION_FILE)
print(WARD_FILE)
print(WARD_SUMMARY_FILE)
