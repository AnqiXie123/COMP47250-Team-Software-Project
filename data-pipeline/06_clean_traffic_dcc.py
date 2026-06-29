"""
06_clean_traffic_dcc.py
------------------------
Cleans and consolidates SCATS traffic volume data for the Dublin
City Council (DCC) area, producing a single time-series CSV ready
for spatial join in the feature dataset construction step.

This extends pipeline coverage beyond the DLR-only dataset produced
by 03_clean_traffic_data.py. DCC 2025 data is only available for a
subset of months (gaps are a known limitation — see data-sources.md).

Sources processed:
  1. SCATS DCC 2025 — monthly CSV files (Jan, Mar, Apr, May, Jul, Aug;
     other months were not published by Dublin City Council)
     raw/SCATS<Month><Year>.csv  e.g. raw/SCATSMarch2025.csv
  2. SCATS Site Location — maps site IDs to lat/lon coordinates
     raw/dcc_site_locations.csv

Note on the site location file:
  Unlike DLR, the DCC site location file is NOT bundled in the
  monthly volume ZIP downloads. It is published as a separate
  dataset on Smart Dublin:
    https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dcc
  Direct download (CSV, "Google Maps" resource):
    https://data.smartdublin.ie/dataset/5fd277d3-4ece-45b7-982a-b6116c45470b/
    resource/f64c93a1-2bce-42d0-8a8b-b41c95546d8a/download/
    dcc-traffic-scats-signals-google-maps-1.csv
  This was not found during the initial Phase 1 feasibility
  investigation (data-sources.md listed it as missing); it has
  since been located and is used here.
  Columns: WKT, Site_ID, Location, Lat, Long
  Site_ID is numeric and matches the Site column in the volume
  CSVs directly (e.g. Site_ID 58 = "Dorset St / Frederick St /
  Blessington St", confirmed against SCATSMarch2025.csv).

Output:
  output/cleaned_traffic_dcc_2025.csv
  - One row per site per hour
  - Fields: site_id, datetime, region, sum_volume, avg_volume,
            lat, lon
  - Rows with unmatched site_id are NOT dropped — they are kept
    with lat/lon = null so no volume data is silently discarded.
    (Mirrors the tolerant approach in 03, which already handles a
    missing location file; here the file exists but coverage is
    incomplete, so some sites still won't match.)

Usage:
  python 06_clean_traffic_dcc.py
"""

import pandas as pd
import os
import glob

os.makedirs("output", exist_ok=True)

# 1. Load all available DCC monthly files
# glob: finds all files matching the pattern SCATS*.csv in raw/
# DCC 2025 only has Jan, Mar, Apr, May, Jul, Aug published — this is
# a documented gap in the source data, not a bug in this script.
print("Loading DCC SCATS monthly files...")
# NOTE: glob matching is case-INSENSITIVE on Windows, so a pattern
# like "SCATS*.csv" would also match "scats_dlr_*.csv" (the DLR
# files from 03_clean_traffic_data.py) on a Windows machine, even
# though it would correctly exclude them on Linux/Mac. To avoid
# silently pulling in DLR data here, explicitly exclude any file
# containing "dlr" in its name, on top of matching the DCC pattern.
dcc_files = sorted([
    f for f in glob.glob("raw/SCATS*.csv")
    if "dlr" not in os.path.basename(f).lower()
    and "site_location" not in os.path.basename(f).lower()
])

if not dcc_files:
    print("ERROR: No DCC SCATS files found in raw/")
    print("Expected files named: raw/SCATSMarch2025.csv etc.")
    exit(1)

print(f"Found {len(dcc_files)} files:")
for f in dcc_files:
    print(f"  {f}")

# Read all monthly files and concatenate into one DataFrame.
# Each file has identical columns so pd.concat works directly.
# Files are large (~5.4M rows/month), so report progress per file.
dfs = []
for filepath in dcc_files:
    df_month = pd.read_csv(filepath)
    dfs.append(df_month)
    print(f"  Loaded {filepath}: {len(df_month):,} rows")

df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal rows after concat: {len(df):,}")
print(f"Columns: {list(df.columns)}")

# 2. Parse and clean the datetime column
# End_Time is stored as an integer in format YYYYMMDDHHmmss
# e.g. 20250313010000 = 2025-03-13 01:00:00
print("\nParsing datetime column...")
df["datetime"] = pd.to_datetime(
    df["End_Time"].astype(str),
    format="%Y%m%d%H%M%S",
    errors="coerce"
)

# Drop rows where datetime parsing failed (header/notes rows etc.)
invalid_dt = df["datetime"].isna().sum()
if invalid_dt > 0:
    print(f"Warning: {invalid_dt} rows with invalid datetime — dropping")
df = df.dropna(subset=["datetime"])

# Report which months are actually present, to make the known
# data gap visible in the output rather than silently absorbed.
months_present = sorted(df["datetime"].dt.to_period("M").unique().astype(str))
print(f"Months present in data: {months_present}")

# 3. Aggregate to site level (sum across all detectors per site/hour)
# Same logic as 03_clean_traffic_data.py: multiple detectors per site
# (one per lane/approach), we want total volume per site per hour.
print("Aggregating detectors to site level...")
df_site = (
    df.groupby(["Site", "datetime", "Region"])
    .agg(
        sum_volume=("Sum_Volume", "sum"),
        avg_volume=("Avg_Volume", "mean")
    )
    .reset_index()
)
df_site.columns = ["site_id", "datetime", "region",
                   "sum_volume", "avg_volume"]
df_site["avg_volume"] = df_site["avg_volume"].round(2)

print(f"Rows after aggregation: {len(df_site):,}")
print(f"Unique sites: {df_site['site_id'].nunique()}")
print(f"Date range: {df_site['datetime'].min()} "
      f"to {df_site['datetime'].max()}")

# 4. Join site location coordinates
# The DCC site location file is published separately from the
# monthly volume data (see module docstring). Columns are
# WKT, Site_ID, Location, Lat, Long — Site_ID is numeric and
# joins directly against site_id with no string reformatting.
location_file = "raw/dcc_site_locations.csv"

if os.path.exists(location_file):
    print(f"\nLoading site locations from {location_file}...")
    locations = pd.read_csv(location_file)
    print(f"Location file columns: {list(locations.columns)}")
    print(f"Location file sites: {len(locations)}")

    locations = locations[["Site_ID", "Lat", "Long"]].rename(columns={
        "Site_ID": "site_id",
        "Lat":     "lat",
        "Long":    "lon"
    })

    # Ensure site_id types match for the join — volume data Site
    # column and Site_ID here are both numeric, but cast to the
    # same dtype defensively (mirrors the string-cast approach in
    # 03, applied consistently across the pipeline).
    df_site["site_id"] = df_site["site_id"].astype(str)
    locations["site_id"] = locations["site_id"].astype(str)

    # Check for duplicate Site_IDs in the location file before
    # joining — a many-to-one join would silently inflate row counts.
    dup_sites = locations["site_id"].duplicated().sum()
    if dup_sites > 0:
        print(f"Warning: {dup_sites} duplicate Site_ID values in "
              f"location file — keeping first occurrence only")
        locations = locations.drop_duplicates(subset="site_id", keep="first")

    df_site = df_site.merge(locations, on="site_id", how="left")

    matched = df_site["lat"].notna().sum()
    total = len(df_site)
    print(f"Coordinates matched: {matched:,} / {total:,} rows "
          f"({matched/total*100:.1f}%)")

    unmatched_sites = sorted(
        df_site.loc[df_site["lat"].isna(), "site_id"].unique(),
        key=lambda x: (len(x), x)
    )
    if unmatched_sites:
        print(f"Unmatched site_ids ({len(unmatched_sites)} unique): "
              f"{unmatched_sites[:15]}"
              f"{' ...' if len(unmatched_sites) > 15 else ''}")
        print("These rows are KEPT with lat/lon = null, not dropped —")
        print("consistent with how 05_build_feature_dataset.py expects")
        print("to receive complete volume records and decide separately")
        print("whether a site can be spatially used.")
else:
    # Mirrors 03's fallback: if the location file is genuinely
    # missing, don't crash — output without coordinates and warn.
    print(f"\nWarning: site location file not found: {location_file}")
    print("Output will not contain coordinates.")
    print("Download from:")
    print("  https://data.smartdublin.ie/dataset/"
          "traffic-signals-and-scats-sites-locations-dcc")
    df_site["lat"] = None
    df_site["lon"] = None

# 5. Basic data quality checks
print("\n=== Data Quality ===")
print(f"Rows with sum_volume = 0: "
      f"{(df_site['sum_volume'] == 0).sum():,} "
      f"(kept — zero traffic is valid at night)")
print(f"Rows with null coordinates: "
      f"{df_site['lat'].isna().sum():,}")

# 6. Sort and export
df_site = df_site.sort_values(
    ["site_id", "datetime"]
).reset_index(drop=True)

output_path = "output/cleaned_traffic_dcc_2025.csv"
df_site.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(df_site):,}")
print(f"Columns: {list(df_site.columns)}")
print("\nSample:")
print(df_site.head(5).to_string(index=False))
print("\nKnown limitation: DCC 2025 only covers "
      f"{months_present} — other months were not published by DCC.")
print("Next step: update 05_build_feature_dataset.py to merge this")
print("with cleaned_traffic_dlr_2023.csv (DLR), and decide whether to")
print("drop rows with null coordinates before the K-Means handoff.")