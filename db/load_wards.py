import json
import psycopg
from shapely.geometry import shape

GEOJSON_PATH = "db/BMC_Wards.geojson"

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="civic",
    user="civic",
    password="civic"
)

with open(GEOJSON_PATH, "r") as f:
    data = json.load(f)

features = data["features"]

print(f"Found {len(features)} ward features")

with conn:
    with conn.cursor() as cur:

        # Start clean so rerunning this script doesn't create duplicates
        cur.execute("DELETE FROM wards;")

        for feature in features:
            props = feature["properties"]

            ward_id = int(props["gid"])
            ward_name = str(props["name"])

            geom = shape(feature["geometry"])

            cur.execute(
                """
                INSERT INTO wards (id, name, geom)
                VALUES (
                    %s,
                    %s,
                    ST_Multi(
                        ST_SetSRID(
                            ST_GeomFromText(%s),
                            4326
                        )
                    )
                );
                """,
                (ward_id, ward_name, geom.wkt)
            )

            print(f"Loaded ward {ward_id}: {ward_name}")

print("Ward loading complete.")
