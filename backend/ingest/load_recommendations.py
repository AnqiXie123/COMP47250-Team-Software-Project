"""
One-off script: loads recommendations.csv into the recommendations table.
Run from the repo root: python -m backend.ingest.load_recommendations
Safe to re-run — truncates before inserting.

CSV fields: rank, lat, lon, cluster, gap_score, traffic_volume,
            charger_count_nearby, road_density, distance_to_nearest_substation_m,
            traffic_source, reason, k_value, candidate_percentile, minimum_spacing_m
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
        (rank, lat, lon, cluster, gap_score, traffic_volume,
         charger_count_nearby, road_density, distance_to_nearest_substation_m,
         traffic_source, reason, k_value, candidate_percentile, minimum_spacing_m, geom)
    VALUES %s
""", [
    (
        int(row["rank"]),
        float(row["lat"]),
        float(row["lon"]),
        int(row["cluster"]),
        float(row["gap_score"]),
        float(row["traffic_volume"]),
        float(row["charger_count_nearby"]),
        int(row["road_density"]),
        float(row["distance_to_nearest_substation_m"]),
        str(row["traffic_source"]),
        str(row["reason"]),
        int(row["k_value"]),
        int(row["candidate_percentile"]),
        int(row["minimum_spacing_m"]),
        f"SRID=4326;POINT({float(row['lon'])} {float(row['lat'])})",
    )
    for _, row in df.iterrows()
], template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))")

conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(df)} recommendations into database.")
