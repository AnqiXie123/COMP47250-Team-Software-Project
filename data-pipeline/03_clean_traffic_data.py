"""
03_clean_traffic_data.py
------------------------
Cleans and consolidates SCATS traffic volume data for the Dublin
area, producing a single time-series CSV ready for spatial join
in the feature dataset construction step.

SCATS (Sydney Coordinated Adaptive Traffic System) is the
intelligent traffic management system used across Dublin.
Sensors at each junction count vehicles passing every hour.

Sources processed:
  1. SCATS DLR 2023 — 12 monthly CSV files (primary, complete year)
     raw/scats_dlr_jan_2023.csv ... raw/scats_dlr_dec_2023.csv
  2. SCATS Site Location — maps site IDs to lat/lon coordinates
     Must be obtained separately (see Notes below)

Output:
  output/cleaned_traffic_dlr_2023.csv
  - One row per site per hour
  - Fields: site_id, datetime, region, sum_volume, avg_volume,
            lat, lon
  - Only sites with known coordinates are included

Notes on site location file:
  The SCATS volume CSV contains only a numeric Site ID.
  To map Site IDs to coordinates, a separate site location file
  is required. For DLR 2023, this file should be named:
    raw/scats_dlr_site_locations.csv
  If not available, the script will output traffic data without
  coordinates and print a warning.

Usage:
  python 03_clean_traffic_data.py
"""

import pandas as pd
import os
import glob

os.makedirs("output", exist_ok=True)

# 1. Load all 12 monthly DLR SCATS files
# glob: finds all files matching the pattern scats_dlr_*.csv in raw/
# This avoids hardcoding 12 filenames and handles any ordering automatically
print("Loading DLR SCATS monthly files...")
dlr_files = sorted([
    f for f in glob.glob("raw/scats_dlr_*.csv")
    if "site_location" not in f
])

if not dlr_files:
    print("ERROR: No DLR SCATS files found in raw/")
    print("Expected files named: raw/scats_dlr_jan_2023.csv etc.")
    exit(1)

print(f"Found {len(dlr_files)} files:")
for f in dlr_files:
    print(f"  {f}")

# Read all monthly files and concatenate into one DataFrame
# Each file has identical columns so pd.concat works directly
dfs = []
for filepath in dlr_files:
    df_month = pd.read_csv(filepath)
    dfs.append(df_month)
    print(f"  Loaded {filepath}: {len(df_month):,} rows")

df = pd.concat(dfs, ignore_index=True)
print(f"\nTotal rows after concat: {len(df):,}")
print(f"Columns: {list(df.columns)}")

# 2. Parse and clean the datetime column
# End_Time is stored as an integer in format YYYYMMDDHHmmss
# e.g. 20230131050000 = 2023-01-31 05:00:00
# pd.to_datetime with format parameter parses this correctly
print("\nParsing datetime column...")
df["datetime"] = pd.to_datetime(
    df["End_Time"].astype(str),
    format="%Y%m%d%H%M%S",
    errors="coerce"
)

# Drop rows where datetime parsing failed
invalid_dt = df["datetime"].isna().sum()
if invalid_dt > 0:
    print(f"Warning: {invalid_dt} rows with invalid datetime — dropping")
df = df.dropna(subset=["datetime"])

# 3. Aggregate to site level (sum across all detectors per site/hour)
# Each site has multiple detectors (one per lane).
# For traffic demand modelling we want total volume per site per hour,
# not per individual detector — so we group by site + datetime and sum.
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
# The SCATS volume data has no coordinates — only a numeric Site ID.
# We join with a site location file to add lat/lon.
location_file = "raw/scats_dlr_site_locations.csv"

if os.path.exists(location_file):
    print(f"\nLoading site locations from {location_file}...")
    locations = pd.read_csv(location_file)
    print(f"Location file columns: {list(locations.columns)}")

    # Normalise column names to lowercase for safe merging
    locations.columns = [c.lower().strip() for c in locations.columns]

    # Try to find lat/lon columns — different files use different names
    lat_col = next((c for c in locations.columns
                    if "lat" in c), None)
    lon_col = next((c for c in locations.columns
                    if "lon" in c or "lng" in c), None)
    site_col = next((c for c in locations.columns
                     if "site" in c), None)

    if lat_col and lon_col and site_col:
        locations = locations[[site_col, lat_col, lon_col]].rename(columns={
            site_col: "site_id",
            lat_col:  "lat",
            lon_col:  "lon"
        })
        # Ensure site_id types match for the join
        df_site["site_id"] = df_site["site_id"].astype(str)
        locations["site_id"] = locations["site_id"].astype(str)

        df_site = df_site.merge(locations, on="site_id", how="left")

        matched = df_site["lat"].notna().sum()
        total = len(df_site)
        print(f"Coordinates matched: {matched:,} / {total:,} rows "
              f"({matched/total*100:.1f}%)")
    else:
        print("Warning: could not identify lat/lon/site columns "
              f"in {location_file}")
        df_site["lat"] = None
        df_site["lon"] = None
else:
    # Site location file not found: output without coordinates
    # This is a known limitation documented in data-sources.md
    print(f"\nWarning: site location file not found: {location_file}")
    print("Output will not contain coordinates.")
    print("To add coordinates, obtain the DLR SCATS site location file")
    print("and save it as raw/scats_dlr_site_locations.csv")
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

output_path = "output/cleaned_traffic_dlr_2023.csv"
df_site.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(df_site):,}")
print(f"Columns: {list(df_site.columns)}")
print("\nSample:")
print(df_site.head(5).to_string(index=False))
print("\nNext step: run 04_fetch_osm_roads.py")