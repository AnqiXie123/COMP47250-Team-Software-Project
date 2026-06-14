"""
One-off script: loads traffic_sites.csv into the traffic_sites table.
Run from the repo root: python -m backend.ingest.load_traffic
Safe to re-run — truncates before inserting.
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data-pipeline/output/traffic_sites.csv")
DB_DSN = os.getenv("DATABASE_URL", "dbname=ecocharge")

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

df = pd.read_csv(CSV_PATH)

cur.execute("TRUNCATE TABLE traffic_sites")

execute_values(cur, """
    INSERT INTO traffic_sites (location_id, lat, lon, traffic_volume)
    VALUES %s
""", [
    (str(row["location_id"]), float(row["lat"]), float(row["lon"]), float(row["traffic_volume"]))
    for _, row in df.iterrows()
])

conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(df)} traffic sites into database.")
