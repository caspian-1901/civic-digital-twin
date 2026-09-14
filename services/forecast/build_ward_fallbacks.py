from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

WARD_FILE = REPO_ROOT / "db" / "BMC_Wards.geojson"
OBSERVATIONS_FILE = BASE_DIR / "ward_hourly_observed.csv"
OUTPUT_FILE = BASE_DIR / "ward_fallbacks.csv"


WARD_ID_TO_NAME = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E",
    6: "F/S",
    7: "G/S",
    8: "F/N",
    9: "G/N",
    10: "N",
    11: "R/C",
    12: "S",
    13: "T",
    14: "K/W",
    15: "R/N",
    16: "M/E",
    17: "M/W",
    18: "H/E",
    19: "K/E",
    20: "P/S",
    21: "P/N",
    22: "R/S",
    23: "H/W",
    24: "L",
}

WARD_NAME_TO_ID = {name: gid for gid, name in WARD_ID_TO_NAME.items()}


# -----------------------------
# 1. Load ward boundaries
# -----------------------------
wards = gpd.read_file(WARD_FILE)

wards = wards.rename(
    columns={
        "gid": "ward_id",
        "name": "ward_name",
    }
)

wards["ward_id"] = wards["ward_id"].astype(int)

# Use a projected CRS suitable for Mumbai so distance is measured in metres.
wards_projected = wards.to_crs(epsg=32643)

wards_projected["centroid"] = wards_projected.geometry.centroid


# -----------------------------
# 2. Determine which wards have observed PM2.5
# -----------------------------
observations = pd.read_csv(OBSERVATIONS_FILE)

covered_names = set(
    observations["ward_name"]
    .dropna()
    .astype(str)
    .unique()
)

covered_ids = {
    WARD_NAME_TO_ID[name]
    for name in covered_names
    if name in WARD_NAME_TO_ID
}

print("Covered wards:", len(covered_ids))
print("Covered IDs:", sorted(covered_ids))


# -----------------------------
# 3. Find nearest covered ward
# -----------------------------
rows = []

for _, ward in wards_projected.iterrows():
    ward_id = int(ward["ward_id"])
    ward_name = ward["ward_name"]

    if ward_id in covered_ids:
        rows.append(
            {
                "ward_id": ward_id,
                "ward_name": ward_name,
                "has_direct_data": True,
                "proxy_ward_id": ward_id,
                "proxy_ward_name": ward_name,
                "distance_m": 0.0,
            }
        )
        continue

    origin = ward["centroid"]

    candidates = wards_projected[
        wards_projected["ward_id"].isin(covered_ids)
    ].copy()

    candidates["distance_m"] = candidates["centroid"].distance(origin)

    nearest = candidates.sort_values("distance_m").iloc[0]

    rows.append(
        {
            "ward_id": ward_id,
            "ward_name": ward_name,
            "has_direct_data": False,
            "proxy_ward_id": int(nearest["ward_id"]),
            "proxy_ward_name": nearest["ward_name"],
            "distance_m": round(float(nearest["distance_m"]), 1),
        }
    )


result = pd.DataFrame(rows).sort_values("ward_id")

result.to_csv(OUTPUT_FILE, index=False)

print("\nWARD FALLBACK MAP")
print("=" * 80)
print(result.to_string(index=False))

print("\nUncovered wards only:")
print(
    result[result["has_direct_data"] == False][
        [
            "ward_id",
            "ward_name",
            "proxy_ward_id",
            "proxy_ward_name",
            "distance_m",
        ]
    ].to_string(index=False)
)

print(f"\nSaved: {OUTPUT_FILE}")
