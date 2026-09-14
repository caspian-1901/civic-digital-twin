import pandas as pd

INPUT = "full_history_clean_sensor_hourly.csv"
OUTPUT = "full_history_final_clean.csv"

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

original_rows = len(df)

# Remove the independently validated extreme sensor artifacts.
# We stop here rather than progressively trimming legitimate high pollution.
bad_extreme = df["pm25"] >= 900

removed = df[bad_extreme].copy()
clean = df[~bad_extreme].copy()

clean = clean.sort_values(
    ["datetime_utc", "sensor_id"]
).reset_index(drop=True)

clean.to_csv(OUTPUT, index=False)
removed.to_csv("final_removed_extremes.csv", index=False)

print("=" * 70)
print("FINAL SENSOR-LEVEL CLEANING")
print("=" * 70)

print("Input rows:", original_rows)
print("Extreme artifacts removed:", len(removed))
print("Final clean rows:", len(clean))
print(
    "Percent removed in final step:",
    round(len(removed) / original_rows * 100, 4),
    "%"
)

print("\nFINAL PM2.5 SUMMARY")
print(clean["pm25"].describe(percentiles=[
    .01, .05, .25, .50, .75, .90, .95, .99, .995, .999
]))

print("\nMaximum:", clean["pm25"].max())

print("\nSaved:")
print(OUTPUT)
print("final_removed_extremes.csv")
