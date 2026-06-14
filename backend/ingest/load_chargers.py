"""
One-off script: loads dublin_ev_chargers.geojson into the ev_chargers table.
Run from the repo root: python -m backend.ingest.load_chargers
Safe to re-run — uses ON CONFLICT DO NOTHING.
"""
import json
import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEOJSON_PATH = Path("data-pipeline/output/dublin_ev_chargers.geojson")
DB_DSN = os.getenv("DATABASE_URL", "dbname=ecocharge")

INSERT_SQL = """
    INSERT INTO ev_chargers (id, lat, lon, address, operator, num_chargers, source_area, open_hours, geom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    ON CONFLICT (id) DO NOTHING
"""

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

with open(GEOJSON_PATH) as f:
    data = json.load(f)

loaded = 0
for feature in data["features"]:
    p = feature["properties"]
    cur.execute(INSERT_SQL, (
        p["id"], p["lat"], p["lon"],
        p.get("address"), p.get("operator"), p.get("num_chargers"),
        p.get("source_area"), p.get("open_hours"),
        p["lon"], p["lat"],  # ST_MakePoint takes (lon, lat)
    ))
    loaded += 1

conn.commit()
cur.close()
conn.close()
print(f"Loaded {loaded} EV charger records into ev_chargers.")
