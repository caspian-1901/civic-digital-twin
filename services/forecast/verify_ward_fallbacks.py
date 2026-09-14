from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

WARD_FILE = REPO_ROOT / "db" / "BMC_Wards.geojson"
FALLBACK_FILE = BASE_DIR / "ward_fallbacks.csv"


wards = gpd.read_file(WARD_FILE).rename(
    columns={
        "gid": "ward_id",
        "name": "ward_name",
    }
)

wards["ward_id"] = wards["ward_id"].astype(int)

fallbacks = pd.read_csv(FALLBACK_FILE)

uncovered = fallbacks[fallbacks["has_direct_data"] == False]

print("WARD FALLBACK GEOGRAPHIC VALIDATION")
print("=" * 80)

for _, row in uncovered.iterrows():
    source = wards[wards["ward_id"] == int(row["ward_id"])].iloc[0]
    proxy = wards[wards["ward_id"] == int(row["proxy_ward_id"])].iloc[0]

    source_geom = source.geometry
    proxy_geom = proxy.geometry

    touches = source_geom.touches(proxy_geom)
    intersects = source_geom.intersects(proxy_geom)

    print(
        f"{row['ward_name']:>4} -> "
        f"{row['proxy_ward_name']:<4} | "
        f"distance={row['distance_m']:>7.1f} m | "
        f"touches={touches} | "
        f"intersects={intersects}"
    )
