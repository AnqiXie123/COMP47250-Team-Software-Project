"""
08_clean_esb_substations.py
----------------------------
Extracts Dublin-area substation locations from the ESB Networks
Network Capacity Heatmap Excel file, producing a clean CSV of
substation coordinates for use as a spatial renewable energy
proxy feature in 05_build_feature_dataset.py.

Background:
  The unified feature dataset (unified_features_v2.csv) currently
  has no spatially differentiated renewable energy feature — the
  previous renewable_score column was a single national constant
  (~0.41) providing zero spatial signal for K-Means clustering.

  ESB Networks is Ireland's licensed electricity distribution
  operator and the primary conduit through which renewable energy
  (wind, solar) enters the distribution grid. The distance from a
  traffic monitoring site to the nearest ESB substation is a
  meaningful spatial proxy for:
    - Cost of connecting new EV charging infrastructure to the grid
    - Proximity to renewable energy injection points

  This produces a feature (distance_to_nearest_substation_m) with
  genuine spatial variation across Dublin — unlike a national
  average, each traffic site gets a different value based on its
  actual geography relative to the grid infrastructure.

Data source:
  ESB Networks Network Capacity Heatmap (December 2025)
  Landing page:
    https://www.esbnetworks.ie/services/get-connected/
    renewable-connection/network-capacity-heatmap
  Direct download:
    https://media.esbnetworks.ie/media/docs/default-source/
    publications/customer-heatmap-download-december-2025.xlsx
  Format: Excel (.xlsx), sheet "Heatmap data"
  Update frequency: quarterly
  Licence: published by ESB Networks (public utility), freely
    downloadable without registration

File structure (confirmed by inspection):
  - Row 1: merged section header (ignored)
  - Row 2: column headers
  - Rows 3+: data
  Key columns: Station Name, Voltage Class (LV/MV/110kV/38kV),
               Latitude, Longitude
  MV/LV coordinates are exact; HV (110kV/38kV) are approximate
  per ESB Networks' own notes on the heatmap page.

Dublin coverage (verified):
  LV:    7,664 substations
  MV:       96 substations
  38 kV:    14 substations
  110 kV:    6 substations
  Total: 7,780 substations with coordinates in the Dublin
         bounding box (lat 53.2–53.45, lon -6.5 to -6.0)

Input:
  raw/customer-heatmap-december-2025.xlsx
  (manual download required — see landing page above)

Output:
  output/dublin_substations.csv
  - One row per substation in the Dublin bounding box
  - Fields: name, voltage_class, lat, lon
  - All records have valid coordinates (WGS84 / EPSG:4326)

Usage:
  python 08_clean_esb_substations.py
"""

import openpyxl
import pandas as pd
import os

os.makedirs("output", exist_ok=True)

# Dublin bounding box — same bounds used in 04_fetch_osm_roads.py
# (lat 53.2–53.45, lon -6.5 to -6.0) to maintain consistency
# across pipeline scripts
DUBLIN_LAT_MIN, DUBLIN_LAT_MAX = 53.2, 53.45
DUBLIN_LON_MIN, DUBLIN_LON_MAX = -6.5, -6.0

EXCEL_PATH = "raw/customer-heatmap-download-december-2025.xlsx"
SHEET_NAME = "Heatmap data"

print(f"Loading ESB Networks heatmap from {EXCEL_PATH}...")
print("(This may take a few seconds — the file covers all of Ireland)")

if not os.path.exists(EXCEL_PATH):
    print(f"\nERROR: File not found: {EXCEL_PATH}")
    print("Download from:")
    print("  https://www.esbnetworks.ie/services/get-connected/"
          "renewable-connection/network-capacity-heatmap")
    print("Save as: raw/customer-heatmap-december-2025.xlsx")
    exit(1)

wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
ws = wb[SHEET_NAME]

# Row 1 is a merged section header; row 2 contains the actual column names
all_rows = list(ws.iter_rows(min_row=2, values_only=True))
headers = all_rows[0]
print(f"Columns found: {len(headers)}")

# Locate the columns we need by name — more robust than hardcoding
# indices since ESB may reorder columns in future file versions
def find_col(name):
    try:
        return list(headers).index(name)
    except ValueError:
        raise ValueError(
            f"Column '{name}' not found in sheet. "
            f"Available columns: {[h for h in headers if h]}"
        )

lat_idx  = find_col("Latitude")
lon_idx  = find_col("Longitude")
name_idx = find_col("Station Name")
vc_idx   = find_col("Voltage Class")

print(f"Column indices — Name:{name_idx}, Voltage:{vc_idx}, "
      f"Lat:{lat_idx}, Lon:{lon_idx}")

# Extract all substations, filter to Dublin bounding box
print(f"\nFiltering to Dublin area "
      f"(lat {DUBLIN_LAT_MIN}–{DUBLIN_LAT_MAX}, "
      f"lon {DUBLIN_LON_MIN}–{DUBLIN_LON_MAX})...")

records = []
skipped_no_coords = 0

for row in all_rows[1:]:  # skip header row
    lat = row[lat_idx]
    lon = row[lon_idx]

    # Skip rows with missing coordinates
    if lat is None or lon is None:
        skipped_no_coords += 1
        continue

    lat, lon = float(lat), float(lon)

    # Keep only Dublin-area substations
    if not (DUBLIN_LAT_MIN <= lat <= DUBLIN_LAT_MAX and
            DUBLIN_LON_MIN <= lon <= DUBLIN_LON_MAX):
        continue

    records.append({
        "name":          row[name_idx],
        "voltage_class": row[vc_idx],
        "lat":           round(lat, 8),
        "lon":           round(lon, 8),
    })

wb.close()

print(f"Rows skipped (no coordinates): {skipped_no_coords:,}")
print(f"Dublin substations extracted: {len(records):,}")

# Summary by voltage class
df = pd.DataFrame(records)
print()
print("=== By Voltage Class ===")
print(df["voltage_class"].value_counts().to_string())

# Note on HV coordinate accuracy
hv_count = df[df["voltage_class"].isin(["110 kV", "38 kV"])].shape[0]
if hv_count > 0:
    print(f"\nNote: {hv_count} HV (110kV/38kV) substations have approximate "
          f"coordinates per ESB Networks' own documentation — their locations "
          f"are 'indicative only'. These are retained here since the nearest-"
          f"substation distance feature will typically be dominated by the far "
          f"more numerous LV/MV substations anyway.")

# Export
output_path = "output/dublin_substations.csv"
df.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(df)}")
print()
print("Sample:")
print(df.head(5).to_string(index=False))
print()
print("Next step: run 05_build_feature_dataset.py — it will read this file")
print("to compute distance_to_nearest_substation_m for each traffic site.")
