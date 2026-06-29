"""
build_traffic_sites.py
------------------------
One-off script: aggregates DLR + DCC + SDCC traffic data into the
flat format the `traffic_sites` table expects (location_id, lat,
lon, traffic_volume) — one row per site, for the dashboard's
traffic heatmap display.

This is DISTINCT from unified_features_v2.csv:
  - unified_features_v2.csv is for K-Means TRAINING. It deduplicates
    DLR/DCC overlap (keeping DCC) and currently excludes SDCC
    entirely (per Anqi's decision, due to the SCOOT/SCATS unit
    mismatch — SDCC's flow values run ~5x lower than DCC's
    sum_volume, and mixing them would distort standardisation).
  - traffic_sites (this script's output) is for DISPLAY ONLY on the
    map's traffic heatmap layer.

IMPORTANT — location_id must be deduplicated here too, NOT just for
K-Means. The traffic_sites table has a UNIQUE/PRIMARY KEY constraint
on location_id (confirmed via check_tables.py against the live
database — inserting a duplicate raises psycopg2.errors.
UniqueViolation). An earlier version of this script assumed
duplicate location_ids would be harmless for a display-only table,
on the theory that the DB wouldn't enforce uniqueness for a simple
display table — that assumption was wrong and caused a failed
import. The DLR/DCC overlap (222 sites, same site_id, same physical
location, see check_dlr_dcc_overlap.py) must be deduplicated before
insertion.

Dedup rule: identical to 05_build_feature_dataset.py — where a
location_id exists in both DLR and DCC, keep the DCC value (more
recent). This keeps the heatmap consistent with what the K-Means
training data uses, rather than introducing a second, different
dedup rule for the same overlap.

SDCC has its own site-id scheme (e.g. "N01111A") with no overlap
against DLR/DCC, so it is added without dedup, same as in 05.

Input files:
  output/cleaned_traffic_dlr_2023.csv   (from 03_clean_traffic_data.py)
  output/cleaned_traffic_dcc_2025.csv   (from 06_clean_traffic_dcc.py)
  output/cleaned_traffic_sdcc_2024.csv  (from 07_clean_traffic_sdcc.py)

Output:
  output/traffic_sites_v2.csv
  - Fields: location_id, lat, lon, traffic_volume
  - location_id is guaranteed unique (verified before export)
  - Matches the existing `traffic_sites` table schema exactly
    (confirmed via check_tables.py against the live database)

Usage:
  python build_traffic_sites.py
"""

import pandas as pd
import os

os.makedirs("output", exist_ok=True)

# DLR
print("Loading DLR traffic data...")
dlr = pd.read_csv("output/cleaned_traffic_dlr_2023.csv")
dlr_agg = (
    dlr.groupby("site_id")
    .agg(traffic_volume=("sum_volume", "mean"), lat=("lat", "first"), lon=("lon", "first"))
    .reset_index()
)
dlr_agg = dlr_agg.dropna(subset=["lat", "lon"])
dlr_agg["location_id"] = dlr_agg["site_id"].astype(str)
print(f"  DLR sites: {len(dlr_agg)}")

# DCC
print("Loading DCC traffic data...")
dcc = pd.read_csv("output/cleaned_traffic_dcc_2025.csv")
dcc_agg = (
    dcc.groupby("site_id")
    .agg(traffic_volume=("sum_volume", "mean"), lat=("lat", "first"), lon=("lon", "first"))
    .reset_index()
)
dcc_agg = dcc_agg.dropna(subset=["lat", "lon"])
dcc_agg["location_id"] = dcc_agg["site_id"].astype(str)
print(f"  DCC sites: {len(dcc_agg)}")

# Dedup DLR against DCC — same rule as 05: DCC wins on overlap
dcc_ids = set(dcc_agg["location_id"])
dlr_only = dlr_agg[~dlr_agg["location_id"].isin(dcc_ids)]
print(f"  DLR sites also in DCC (dropped, DCC kept instead): "
      f"{len(dlr_agg) - len(dlr_only)}")
print(f"  DLR sites NOT in DCC (kept): {len(dlr_only)}")

# SDCC
print("Loading SDCC traffic data...")
sdcc = pd.read_csv("output/cleaned_traffic_sdcc_2024.csv")
sdcc_agg = sdcc.rename(columns={"flow": "traffic_volume", "site_id": "location_id"})
sdcc_agg = sdcc_agg.dropna(subset=["lat", "lon"])
print(f"  SDCC sites: {len(sdcc_agg)}")

# Combine, now with DLR/DCC overlap removed
combined = pd.concat([
    dcc_agg[["location_id", "lat", "lon", "traffic_volume"]],
    dlr_only[["location_id", "lat", "lon", "traffic_volume"]],
    sdcc_agg[["location_id", "lat", "lon", "traffic_volume"]],
], ignore_index=True)
combined["traffic_volume"] = combined["traffic_volume"].round(2)

print(f"\nTotal rows after dedup: {len(combined)}")
print(f"Null check: {combined.isnull().sum().sum()}")

# Hard check before export — this is exactly the check that would
# have caught the earlier UniqueViolation before it reached the
# database.
dup_count = combined["location_id"].duplicated().sum()
if dup_count > 0:
    raise ValueError(
        f"{dup_count} duplicate location_id(s) remain — traffic_sites "
        "has a unique constraint on location_id, this WILL fail on "
        "import. Fix the dedup logic before proceeding."
    )
print("Uniqueness check passed — safe to import into traffic_sites.")

output_path = "output/traffic_sites_v2.csv"
combined.to_csv(output_path, index=False)
print(f"\nSaved: {output_path}")
print("\nSample:")
print(combined.head(5).to_string(index=False))
print("\nNext step: truncate + reload the traffic_sites table with this file")
print("(see load_traffic_sites_v2.py)")
