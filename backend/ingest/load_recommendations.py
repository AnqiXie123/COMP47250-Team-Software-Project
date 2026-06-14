"""
One-off script: loads recommendations.csv into the recommendations table.
Run from the repo root: python -m backend.ingest.load_recommendations
Safe to re-run — truncates before inserting.
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data-pipeline/output/recommendations.csv")
DB_DSN = os.getenv("DATABASE_URL", "dbname=ecocharge")

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

df = pd.read_csv(CSV_PATH)

cur.execute("TRUNCATE TABLE recommendations")

execute_values(cur, """
    INSERT INTO recommendations
        (rank, lat, lon, cluster_id, gap_score, traffic_volume, charger_count_nearby, renewable_score, geom)
    VALUES %s
""", [
    (
        int(row["rank"]),
        float(row["lat"]),
        float(row["lon"]),
        int(row["cluster_id"]),
        float(row["gap_score"]),
        float(row["traffic_volume"]),
        float(row["charger_count_nearby"]),
        float(row["renewable_score"]),
        f"SRID=4326;POINT({float(row['lon'])} {float(row['lat'])})",
    )
    for _, row in df.iterrows()
], template="(%s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))")

conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(df)} recommendations into database.")
