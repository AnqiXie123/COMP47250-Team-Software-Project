"""
07_clean_traffic_sdcc.py
--------------------------
Cleans and consolidates SDCC (South Dublin County Council) traffic
flow data, producing a single time-series CSV ready for spatial
join in the feature dataset construction step.

This extends pipeline coverage beyond DLR (03) and DCC (06) into
South Dublin.

Sources processed:
  1. SDCC Traffic Flow Data — GeoJSON, no embedded coordinates
     (geometry is null for all records; confirmed during Phase 1
     investigation — see data-sources.md)
     raw/Traffic_Flow_Data_*_SDCC.geojson
  2. SDCC Site Names — provides X/Y coordinates per site
     raw/sdcc_site_names.csv

Note on the site location file:
  The site location file's `scn` field (e.g. "N01111") and the flow
  data's `site` field (e.g. "N01111A") are NOT the same string — the
  flow data's site has one extra trailing letter indicating the
  detection direction/lane at that junction (e.g. "A", "C", "D" are
  different approaches to junction N01111). Multiple `site` values
  share one physical location and therefore one `scn` coordinate.
  This script strips the trailing letter from `site` before joining
  on `scn`. This was confirmed against real data: stripping the
  last character of every observed site value in the flow data
  produces exactly the set of scn values in the site-names file
  (e.g. N01111A, N01111C, N01111D, ... -> N01111).

  Site location file download (CSV):
    https://data-sdublincoco.opendata.arcgis.com/api/download/v1/
    items/ae717b6b1c1642928bc8f1dbe993332c/csv?layers=0
  Landing page:
    https://data.smartdublin.ie/dataset/traffic-data-site-names-sdcc1
  Columns: OBJECTID, scn, region, system, locn, X, Y
  (X = longitude, Y = latitude)

Output:
  output/cleaned_traffic_sdcc_2024.csv
  - One row per site (full site code, e.g. N01111A) per 15-min interval
  - Fields: site_id, datetime, flow, lat, lon
  - Rows with unmatched site_id are NOT dropped — kept with lat/lon
    = null, same tolerant approach as 03 and 06

Usage:
  python 07_clean_traffic_sdcc.py
"""

import json
import pandas as pd
import os
import glob

os.makedirs("output", exist_ok=True)

# 1. Load all SDCC flow GeoJSON file(s)
print("Loading SDCC traffic flow data...")
sdcc_files = sorted(glob.glob("raw/Traffic_Flow_Data_*_SDCC.geojson"))

if not sdcc_files:
    print("ERROR: No SDCC flow files found in raw/")
    print("Expected files named: raw/Traffic_Flow_Data_*_SDCC.geojson")
    exit(1)

print(f"Found {len(sdcc_files)} file(s):")
for f in sdcc_files:
    print(f"  {f}")

records = []
for filepath in sdcc_files:
    with open(filepath) as f:
        data = json.load(f)
    print(f"  Loaded {filepath}: {len(data['features']):,} features")
    for feat in data["features"]:
        p = feat["properties"]
        records.append(p)

df = pd.DataFrame(records)
print(f"\nTotal rows after concat: {len(df):,}")
print(f"Columns: {list(df.columns)}")

# 2. Basic cleaning
# A small number of rows in the source file have site == "site"
# (a stray header row that ended up embedded as a data row) — drop
# these before they pollute the join.
before = len(df)
df = df[df["site"].notna() & (df["site"] != "site")]
print(f"Dropped {before - len(df)} rows with invalid/header site value")

# Build a proper datetime from date + start_time.
# date is "YYYY-MM-DD", start_time is "HH:MM:SS"
print("\nParsing datetime column...")
df["datetime"] = pd.to_datetime(
    df["date"].astype(str) + " " + df["start_time"].astype(str),
    errors="coerce"
)
invalid_dt = df["datetime"].isna().sum()
if invalid_dt > 0:
    print(f"Warning: {invalid_dt} rows with invalid datetime — dropping")
df = df.dropna(subset=["datetime"])

print(f"Rows after datetime parsing: {len(df):,}")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"Unique sites (full code, e.g. N01111A): {df['site'].nunique()}")

# 3. Aggregate to site level (mean flow per site)
# Unlike 03/06 (hourly SCATS volume), this source is 15-minute flow
# data — we aggregate across the whole time range to a single mean
# per site, matching the granularity 05_build_feature_dataset.py
# expects (one mean traffic figure per site).
print("\nAggregating to site level...")
site_traffic = (
    df.groupby("site")
    .agg(flow=("flow", "mean"))
    .reset_index()
)
site_traffic.columns = ["site_id", "flow"]
site_traffic["flow"] = site_traffic["flow"].round(2)
print(f"Sites after aggregation: {len(site_traffic)}")

# 4. Join site location coordinates
# IMPORTANT: join key requires stripping the trailing direction
# letter from site_id (see module docstring).
location_file = "raw/sdcc_site_names.csv"

if os.path.exists(location_file):
    print(f"\nLoading site locations from {location_file}...")
    locations = pd.read_csv(location_file)
    print(f"Location file columns: {list(locations.columns)}")

    locations = locations[["scn", "X", "Y", "locn"]].rename(columns={
        "scn": "scn_key",
        "X": "lon",
        "Y": "lat"
    })
    locations["scn_key"] = locations["scn_key"].astype(str)

    # Strip the trailing direction letter to build the join key.
    # e.g. "N01111A" -> "N01111"
    site_traffic["scn_key"] = site_traffic["site_id"].str[:-1]

    dup_sites = locations["scn_key"].duplicated().sum()
    if dup_sites > 0:
        print(f"Warning: {dup_sites} duplicate scn values in "
              f"location file — keeping first occurrence only")
        locations = locations.drop_duplicates(subset="scn_key", keep="first")

    site_traffic = site_traffic.merge(locations, on="scn_key", how="left")
    site_traffic = site_traffic.drop(columns=["scn_key"])

    matched = site_traffic["lat"].notna().sum()
    total = len(site_traffic)
    print(f"Coordinates matched: {matched} / {total} sites "
          f"({matched/total*100:.1f}%)")

    unmatched = sorted(site_traffic.loc[site_traffic["lat"].isna(), "site_id"])
    if unmatched:
        print(f"Unmatched site_ids ({len(unmatched)}): {unmatched[:15]}"
              f"{' ...' if len(unmatched) > 15 else ''}")
else:
    print(f"\nWarning: site location file not found: {location_file}")
    print("Download from:")
    print("  https://data.smartdublin.ie/dataset/traffic-data-site-names-sdcc1")
    site_traffic["lat"] = None
    site_traffic["lon"] = None

# 5. Basic data quality checks
print("\n=== Data Quality ===")
print(f"Rows with flow = 0: {(site_traffic['flow'] == 0).sum()} "
      f"(kept — zero traffic is valid at night)")
print(f"Rows with null coordinates: {site_traffic['lat'].isna().sum()}")

# 6. Export
site_traffic = site_traffic.sort_values("site_id").reset_index(drop=True)
output_path = "output/cleaned_traffic_sdcc_2024.csv"
site_traffic.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(site_traffic)}")
print(f"Columns: {list(site_traffic.columns)}")
print("\nSample:")
print(site_traffic.head(5).to_string(index=False))
print("\nNext step: update 05_build_feature_dataset.py to merge this")
print("with the DLR+DCC traffic data, applying the same dedup logic")
print("if any site_ids turn out to overlap geographically.")
