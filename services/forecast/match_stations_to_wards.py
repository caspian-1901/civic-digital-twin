import os
import requests
import geopandas as gpd
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAQ_API_KEY")

if not api_key:
    raise ValueError("OPENAQ_API_KEY not found")

# ---------------------------------
# 1. Load BMC ward boundaries
# ---------------------------------

ward_file = (
    "Municipal_Spatial_Data/"
    "Mumbai/"
    "BMC_Wards.geojson"
)

wards = gpd.read_file(ward_file)

# GeoJSON coordinates are longitude/latitude
wards = wards.set_crs(epsg=4326, allow_override=True)

print("BMC wards loaded:", len(wards))


# ---------------------------------
# 2. Get Mumbai-area OpenAQ stations
# ---------------------------------

url = "https://api.openaq.org/v3/locations"

headers = {
    "X-API-Key": api_key
}

params = {
    "coordinates": "19.0760,72.8777",
    "radius": 25000,
    "limit": 100
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

response.raise_for_status()

locations = response.json().get("results", [])


# ---------------------------------
# 3. Keep only PM2.5 stations
# ---------------------------------

station_rows = []

for location in locations:

    sensors = location.get("sensors", [])

    pm25_sensors = [
        sensor
        for sensor in sensors
        if sensor.get("parameter", {}).get("name") == "pm25"
    ]

    if not pm25_sensors:
        continue

    coords = location.get("coordinates", {})

    latitude = coords.get("latitude")
    longitude = coords.get("longitude")

    if latitude is None or longitude is None:
        continue

    station_rows.append({
        "location_id": location.get("id"),
        "station_name": location.get("name"),
        "latitude": latitude,
        "longitude": longitude,
        "sensor_ids": ",".join(
            str(sensor.get("id"))
            for sensor in pm25_sensors
        )
    })


# ---------------------------------
# 4. Convert stations into geographic points
# ---------------------------------

stations = gpd.GeoDataFrame(
    station_rows,
    geometry=gpd.points_from_xy(
        [row["longitude"] for row in station_rows],
        [row["latitude"] for row in station_rows]
    ),
    crs="EPSG:4326"
)

print("PM2.5 stations found:", len(stations))


# ---------------------------------
# 5. Spatial join: station -> BMC ward
# ---------------------------------

matched = gpd.sjoin(
    stations,
    wards[["gid", "name", "geometry"]],
    how="left",
    predicate="within"
)

matched = matched.rename(
    columns={
        "gid": "ward_gid",
        "name": "ward_name"
    }
)


# ---------------------------------
# 6. Print results
# ---------------------------------

print("\n=== STATION TO WARD MATCHES ===")

for _, row in matched.iterrows():

    ward = (
        row["ward_name"]
        if row["ward_name"] is not None
        else "OUTSIDE BMC"
    )

    print(
        f"{row['station_name']} "
        f"-> Ward {ward}"
    )


# ---------------------------------
# 7. Coverage summary
# ---------------------------------

inside = matched.dropna(subset=["ward_name"])

coverage = (
    inside.groupby(["ward_gid", "ward_name"])
    .size()
    .reset_index(name="station_count")
)

all_wards = wards[["gid", "name"]].copy()

coverage_all = all_wards.merge(
    coverage,
    left_on=["gid", "name"],
    right_on=["ward_gid", "ward_name"],
    how="left"
)

coverage_all["station_count"] = (
    coverage_all["station_count"]
    .fillna(0)
    .astype(int)
)

print("\n=== WARD COVERAGE ===")

for _, row in coverage_all.iterrows():
    print(
        f"Ward {row['name']}: "
        f"{row['station_count']} PM2.5 station(s)"
    )

print("\n=== SUMMARY ===")

print(
    "Stations inside BMC:",
    len(inside)
)

print(
    "Stations outside BMC:",
    matched["ward_name"].isna().sum()
)

print(
    "Wards with at least one station:",
    (coverage_all["station_count"] > 0).sum(),
    "/",
    len(coverage_all)
)

print(
    "Wards without a station:",
    (coverage_all["station_count"] == 0).sum()
)

# Save results to CSV
matched.drop(columns="geometry").to_csv(
    "station_ward_mapping.csv",
    index=False
)

coverage_all.to_csv(
    "ward_station_coverage.csv",
    index=False
)

print("\nSaved station_ward_mapping.csv")
print("Saved ward_station_coverage.csv")
