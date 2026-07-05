"""
build_traffic_sites.py
------------------------
Aggregates DLR + DCC + SDCC traffic data into the flat format
the `traffic_sites` table expects, for the dashboard's traffic
heatmap display. Now includes a traffic_source column (DCC/DLR/SDCC)
for frontend colour-coding of regions.

Output:
  output/traffic_sites_v2.csv
  - Fields: location_id, lat, lon, traffic_volume, traffic_source
  - location_id is guaranteed unique (hard check before export)

DLR/DCC dedup rule: where a site exists in both, keep DCC (more
recent). SDCC has its own site-id scheme with no overlap, added
as-is.

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
    .agg(traffic_volume=("sum_volume", "mean"),
         lat=("lat", "first"),
         lon=("lon", "first"))
    .reset_index()
)
dlr_agg = dlr_agg.dropna(subset=["lat", "lon"])
dlr_agg["location_id"] = dlr_agg["site_id"].astype(str)
dlr_agg["traffic_source"] = "DLR"
print(f"  DLR sites: {len(dlr_agg)}")

# DCC
print("Loading DCC traffic data...")
dcc = pd.read_csv("output/cleaned_traffic_dcc_2025.csv")
dcc_agg = (
    dcc.groupby("site_id")
    .agg(traffic_volume=("sum_volume", "mean"),
         lat=("lat", "first"),
         lon=("lon", "first"))
    .reset_index()
)
dcc_agg = dcc_agg.dropna(subset=["lat", "lon"])
dcc_agg["location_id"] = dcc_agg["site_id"].astype(str)
dcc_agg["traffic_source"] = "DCC"
print(f"  DCC sites: {len(dcc_agg)}")

# Dedup: DCC wins on overlap
dcc_ids = set(dcc_agg["location_id"])
dlr_only = dlr_agg[~dlr_agg["location_id"].isin(dcc_ids)]
print(f"  DLR sites dropped (overlap with DCC): {len(dlr_agg) - len(dlr_only)}")
print(f"  DLR sites kept (unique): {len(dlr_only)}")

# SDCC
print("Loading SDCC traffic data...")
sdcc = pd.read_csv("output/cleaned_traffic_sdcc_2024.csv")
sdcc_agg = sdcc.rename(columns={"flow": "traffic_volume",
                                  "site_id": "location_id"})
sdcc_agg = sdcc_agg.dropna(subset=["lat", "lon"])
sdcc_agg["traffic_source"] = "SDCC"
print(f"  SDCC sites: {len(sdcc_agg)}")

# Combine
cols = ["location_id", "lat", "lon", "traffic_volume", "traffic_source"]
combined = pd.concat([
    dcc_agg[cols],
    dlr_only[cols],
    sdcc_agg[cols],
], ignore_index=True)
combined["traffic_volume"] = combined["traffic_volume"].round(2)

print(f"\nTotal rows after dedup: {len(combined)}")
print(f"Null check: {combined.isnull().sum().sum()}")
print(f"By traffic_source: {combined['traffic_source'].value_counts().to_dict()}")

# Hard uniqueness check before export
dup_count = combined["location_id"].duplicated().sum()
if dup_count > 0:
    raise ValueError(
        f"{dup_count} duplicate location_id(s) — fix dedup logic "
        "before importing (traffic_sites has a unique constraint)."
    )
print("Uniqueness check passed.")

output_path = "output/traffic_sites_v2.csv"
combined.to_csv(output_path, index=False)
print(f"\nSaved: {output_path}")
print("\nSample:")
print(combined.head(5).to_string(index=False))