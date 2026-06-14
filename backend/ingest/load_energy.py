"""
One-off script: loads eirgrid_renewable_2026.csv into the renewable_energy table.
Run from the repo root: python -m backend.ingest.load_energy
Truncates the table before inserting — safe to re-run.
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data-pipeline/output/eirgrid_renewable_2026.csv")
DB_DSN = os.getenv("DATABASE_URL", "dbname=ecocharge")

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

df = pd.read_csv(CSV_PATH)
df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

cur.execute("TRUNCATE TABLE renewable_energy")

rows = [
    (
        row["datetime"],
        row["wind_mw"],
        row["solar_mw"],
        row["total_demand_mw"],
        row["wind_penetration"],
        row["solar_penetration"],
        row["renewable_score"],
    )
    for _, row in df.iterrows()
]

execute_values(cur, """
    INSERT INTO renewable_energy
        (datetime, wind_mw, solar_mw, total_demand_mw, wind_penetration, solar_penetration, renewable_score)
    VALUES %s
""", rows)

conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(rows)} energy records into renewable_energy.")
