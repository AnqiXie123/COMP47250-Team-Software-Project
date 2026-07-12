"""
One-off script: loads scenario recommendation CSVs into scenario_recommendations table.
Run from the repo root: python -m backend.ingest.load_scenario_recommendations
Safe to re-run — truncates before inserting.

CSV files:
  data-pipeline/output/recommendations_ev05.csv  (ev_penetration=0.05)
  data-pipeline/output/recommendations_ev08.csv  (ev_penetration=0.08)
  data-pipeline/output/recommendations_ev12.csv  (ev_penetration=0.12)
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_DSN = os.getenv("DATABASE_URL", "dbname=ecocharge")

SCENARIO_FILES = [
    ("data-pipeline/output/recommendations_ev05.csv", 0.05),
    ("data-pipeline/output/recommendations_ev08.csv", 0.08),
    ("data-pipeline/output/recommendations_ev12.csv", 0.12),
]

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

cur.execute("TRUNCATE TABLE scenario_recommendations")

total = 0
for csv_path, ev_val in SCENARIO_FILES:
    df = pd.read_csv(Path(csv_path))
    execute_values(cur, """
        INSERT INTO scenario_recommendations
            (rank, lat, lon, cluster, gap_score, ev_penetration, k_value, candidate_percentile)
        VALUES %s
    """, [
        (
            int(row["rank"]),
            float(row["lat"]),
            float(row["lon"]),
            int(row["cluster"]),
            float(row["gap_score"]),
            ev_val,
            int(row["k_value"]),
            int(row["candidate_percentile"]),
        )
        for _, row in df.iterrows()
    ])
    print(f"  Loaded {len(df)} rows for ev_penetration={ev_val}")
    total += len(df)

conn.commit()
cur.close()
conn.close()
print(f"Done. Total {total} scenario rows loaded.")
