"""
09_clean_wind_farms.py
-----------------------
Processes the SEAI Wind Farms Connected dataset to extract wind farm
locations as a spatial renewable energy feature for K-Means clustering.

Background:
  The ESB Networks substation distance feature (distance_to_nearest_
  substation_m, added in v3) was found to have insufficient spatial
  variation for K-Means — Dublin's grid density is so high (~7,780
  substations) that almost every traffic site is within 100m of a
  substation, making the feature near-constant in practice (Anqi's
  analysis, 2026-07-07).

  Wind farms are far fewer in number and spatially sparse — there are
  only ~14 wind farms within 60km of Dublin, concentrated in Co. Wicklow,
  Meath, and Louth. The distance from a Dublin traffic site to the
  nearest wind farm will vary from a few km (sites near Wicklow) to
  30-40km (central city sites), providing genuine spatial variation for
  K-Means to use.

  This also strengthens the renewable energy thematic connection: wind
  farms are direct renewable generation sources, and proximity to a wind
  farm reflects the local renewable energy supply landscape in a way
  that substation proximity does not.

Data source:
  SEAI Wind Farms Connected (June 2022)
  Landing page: https://data.gov.ie/dataset/wind-farms-in-ireland
  Publisher: Sustainable Energy Authority of Ireland (SEAI)
  Direct download:
    https://seaiopendata.blob.core.windows.net/wind/WindFarmsConnectedJune2022.csv
  Format: CSV
  Licence: Creative Commons Attribution 4.0
  Coverage: All connected wind farms in Ireland (ex Northern Ireland),
    313 records, no missing coordinates

Coordinate system note:
  The source file uses Irish Grid coordinates (Nat_Grid_E, Nat_Grid_N)
  in EPSG:29902 (TM75 / Irish Grid), not WGS84 lat/lon. This script
  converts them to WGS84 (EPSG:4326) using pyproj before export.

  Install pyproj if not already present:
    pip install pyproj

Input:
  raw/WindFarmsConnectedJune2022.csv
  (manual download required — see landing page above)

Output:
  output/ireland_wind_farms.csv
  - All 313 connected wind farms in Ireland with WGS84 coordinates
  - Fields: name, county, capacity_mw, lat, lon
  - Includes small urban wind installations (e.g. supermarket rooftop
    turbines) as well as large wind farms — downstream scripts can
    filter by capacity_mw if needed

Usage:
  python 09_clean_wind_farms.py
"""

import pandas as pd
import os

os.makedirs("output", exist_ok=True)

try:
    from pyproj import Transformer
except ImportError:
    print("ERROR: pyproj not installed.")
    print("Run: pip install pyproj")
    exit(1)

CSV_PATH = "raw/WindFarmsConnectedJune2022.csv"

if not os.path.exists(CSV_PATH):
    print(f"ERROR: File not found: {CSV_PATH}")
    print("Download from:")
    print("  https://data.gov.ie/dataset/wind-farms-in-ireland")
    print("Save as: raw/WindFarmsConnectedJune2022.csv")
    exit(1)

print(f"Loading wind farm data from {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)
print(f"Records loaded: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# Column names in the source file use double underscores for parentheses
# e.g. Nat_Grid_E_(substation_) becomes Nat_Grid_E__substation_
E_COL = "Nat_Grid_E__substation_"
N_COL = "Nat_Grid_N__substation_"
NAME_COL = "Windfarm_Name"
COUNTY_COL = "County"
CAPACITY_COL = "Installed_Capacity__MW_"

# Check for missing coordinates
missing_coords = df[[E_COL, N_COL]].isna().any(axis=1).sum()
print(f"Records with missing coordinates: {missing_coords}")
df = df.dropna(subset=[E_COL, N_COL])
print(f"Records with valid coordinates: {len(df)}")

# Convert Irish Grid (EPSG:29902) to WGS84 (EPSG:4326)
# pyproj always_xy=True: input order is (Easting, Northing),
# output order is (lon, lat) — not (lat, lon)
print("\nConverting Irish Grid coordinates to WGS84...")
transformer = Transformer.from_crs("EPSG:29902", "EPSG:4326", always_xy=True)

lons, lats = transformer.transform(
    df[E_COL].values,
    df[N_COL].values
)

df_out = pd.DataFrame({
    "name":        df[NAME_COL].str.strip(),
    "county":      df[COUNTY_COL].str.strip(),
    "capacity_mw": df[CAPACITY_COL],
    "lat":         lats.round(6),
    "lon":         lons.round(6),
})

# Sanity check: all converted coordinates should fall within
# Ireland's bounding box (lat 51.4-55.4, lon -10.5 to -5.4)
outside = df_out[
    ~(df_out["lat"].between(51.4, 55.4) & df_out["lon"].between(-10.5, -5.4))
]
if len(outside) > 0:
    print(f"WARNING: {len(outside)} records outside Ireland bounding box "
          f"after conversion — check source coordinates:")
    print(outside[["name", "county", "lat", "lon"]].to_string())
else:
    print("Coordinate sanity check passed — all points within Ireland bounds.")

# Summary statistics
print(f"\nTotal wind farms: {len(df_out)}")
print(f"\nCounty distribution (top 10):")
print(df_out["county"].value_counts().head(10).to_string())

print(f"\nWind farms within 60km of Dublin "
      f"(lat 52.8–53.8, lon -7.0 to -5.8):")
dublin_nearby = df_out[
    df_out["lat"].between(52.8, 53.8) &
    df_out["lon"].between(-7.0, -5.8)
]
print(f"  Count: {len(dublin_nearby)}")
print(dublin_nearby[["name", "county", "capacity_mw", "lat", "lon"]]
      .to_string(index=False))

output_path = "output/ireland_wind_farms.csv"
df_out.to_csv(output_path, index=False)
print(f"\nSaved: {output_path}")
print(f"Final record count: {len(df_out)}")
print("\nSample:")
print(df_out.head(5).to_string(index=False))
print("\nNext step: update 05_build_feature_dataset.py to compute")
print("distance_to_nearest_windfarm_km for each traffic site.")
print("Unlike the substation distance feature, wind farm distances")
print("will range from ~2km to ~50km across Dublin — providing")
print("meaningful spatial variation for K-Means clustering.")
