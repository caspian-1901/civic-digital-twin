import pandas as pd

INPUT = "full_history_final_clean.csv"
OUTPUT = "ward_hourly_observed.csv"

df = pd.read_csv(INPUT)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True,
    errors="coerce"
)

df["pm25"] = pd.to_numeric(
    df["pm25"],
    errors="coerce"
)

# Remove rows unusable for aggregation
df = df.dropna(
    subset=["datetime_utc", "ward_name", "pm25"]
).copy()

# --------------------------------------------------
# Create one PM2.5 value for each ward-hour
# Median chosen after within-ward sensor agreement
# analysis.
# --------------------------------------------------

ward_hourly = (
    df.groupby(["ward_name", "datetime_utc"])
      .agg(
          pm25=("pm25", "median"),
          sensors_used=("sensor_id", "nunique")
      )
      .reset_index()
)

ward_hourly = ward_hourly.sort_values(
    ["ward_name", "datetime_utc"]
).reset_index(drop=True)

print("=" * 70)
print("WARD-HOURLY AGGREGATION")
print("=" * 70)

print("Input sensor observations:", len(df))
print("Output ward-hour observations:", len(ward_hourly))
print("Wards represented:", ward_hourly["ward_name"].nunique())

print("\nWARD COVERAGE")
print(
    ward_hourly.groupby("ward_name")
    .agg(
        observations=("pm25", "count"),
        first=("datetime_utc", "min"),
        last=("datetime_utc", "max"),
        median_pm25=("pm25", "median"),
        max_pm25=("pm25", "max")
    )
    .sort_index()
    .to_string()
)

print("\nSENSORS USED PER WARD-HOUR")
print(
    ward_hourly["sensors_used"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nPM2.5 SUMMARY")
print(
    ward_hourly["pm25"].describe(
        percentiles=[.50, .75, .90, .95, .99, .995, .999]
    )
)

# Safety checks
duplicates = ward_hourly.duplicated(
    subset=["ward_name", "datetime_utc"]
).sum()

print("\nVALIDATION")
print("Duplicate ward-hours:", duplicates)
print("Missing PM2.5:", ward_hourly["pm25"].isna().sum())
print("Negative PM2.5:", (ward_hourly["pm25"] < 0).sum())

ward_hourly.to_csv(OUTPUT, index=False)

print("\nSaved:", OUTPUT)
