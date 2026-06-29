"""
01_clean_ev_chargers.py
-----------------------
Cleans and merges EV charging station data from three sources
covering the Dublin area into a single unified GeoJSON file.

Sources:
  1. ESB eCars national dataset (primary — covers all Dublin areas)
  2. DLR GeoJSON (supplementary — includes non-ESB operators e.g. EasyGo)
  3. SDCC CSV (supplementary — geocoded from address strings)

Input files (place in raw/ before running):
  raw/its-data-ecars-sites-roi-ni.csv      (auto-downloaded by 00_fetch_raw_data.py)
  raw/ev-charging-points-dlr.geojson       (manual download from Smart Dublin)
  raw/Public_EV_Charging_Points_SDCC.csv   (manual download from Smart Dublin)

Output:
  output/dublin_ev_chargers.geojson
  - 133 records covering ESB_national (88), DLR (35), SDCC (10)
  - Fields: id, lat, lon, address, operator, num_chargers,
            source_area, open_hours
  - All records have valid coordinates (WGS84 / EPSG:4326)
  - 23 SDCC records excluded due to unresolvable address strings

Usage:
  python 01_clean_ev_chargers.py
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import json
import os
import math

os.makedirs("output", exist_ok=True)


# Helper: Haversine distance
# Same formula as used in 05_build_feature_dataset.py, kept here as
# well (rather than imported) so this script has no dependency on
# 05 and can be run standalone, in pipeline order, before 05 exists
# in a fresh checkout.
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in metres between two lat/lon points
    using the Haversine formula. Used here to detect duplicate
    charging stations recorded by more than one data source.
    """
    R = 6371000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 1. ESB eCars (primary, covers all Dublin)
# ESB eCars is Ireland's largest public charging network operator.
# The national dataset covers all Dublin areas including city centre (DCC)
# and Fingal (FCC), which are not available on Smart Dublin open data.
# Filter to County == "Dublin" to keep only relevant records.
esb = pd.read_csv("raw/its-data-ecars-sites-roi-ni.csv")
esb_dublin = esb[esb["County"] == "Dublin"].copy()

# Standardise into a common schema shared by all three sources.
# id is prefixed with the source name to ensure uniqueness across datasets.
esb_clean = pd.DataFrame({
    "id":           ["esb_" + str(i) for i in range(len(esb_dublin))],
    "lat":          esb_dublin["Latitude"].values,
    "lon":          esb_dublin["Longitude"].values,
    "address":      esb_dublin["Address"].values,
    "operator":     "ESB eCars",
    "num_chargers": esb_dublin["Nr. Chargers"].values,
    "source_area":  "ESB_national",
    "open_hours":   esb_dublin["Open Hours"].values
})
print(f"ESB clean: {len(esb_clean)} records")

# 2. DLR GeoJSON (supplementary)
# The DLR dataset covers Dún Laoghaire-Rathdown and includes chargers
# operated by EasyGo and other non-ESB providers not in the ESB dataset.
# Coordinates are already embedded in the GeoJSON geometry field.
# Suppress the RuntimeWarning about duplicate feature IDs —
# this is a known quirk of the source file and does not affect the data.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dlr_gdf = gpd.read_file("raw/ev-charging-points-dlr.geojson")

# Extract lat/lon from the GeoJSON geometry column.
# geometry.y = latitude, geometry.x = longitude (standard convention)
dlr_clean = pd.DataFrame({
    "id":           ["dlr_" + str(i) for i in range(len(dlr_gdf))],
    "lat":          dlr_gdf.geometry.y.values,
    "lon":          dlr_gdf.geometry.x.values,
    "address":      dlr_gdf["Location"].values,
    "operator":     dlr_gdf["ServiceProvider"].values,
    "num_chargers": dlr_gdf["NumChargers"].values,
    "source_area":  "DLR",
    "open_hours":   "Unknown"
})
print(f"DLR clean: {len(dlr_clean)} records")

# 3. SDCC CSV — geocode missing coordinates
# The SDCC dataset covers South Dublin County (Tallaght, Clondalkin, Lucan).
# Unlike the other two sources, it contains no lat/lon coordinates —
# only text address strings. Use geocoding to convert these to coordinates.
sdcc = pd.read_csv("raw/Public_EV_Charging_Points_SDCC.csv")

# Nominatim: the OpenStreetMap geocoding service (free, no API key needed).
# RateLimiter: enforces a minimum delay between requests to respect
# Nominatim's usage policy (max 1 request per second).
geolocator = Nominatim(user_agent="ecocharge_dublin_p15")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

print("Geocoding SDCC addresses (33 records, ~1 min)...")
lats, lons = [], []
for idx, row in sdcc.iterrows():
    # Build a specific query string: location + district + city + country
    # The more context provided, the better the geocoding accuracy
    query = f"{row['Location']}, {row['LEA']}, Dublin, Ireland"
    try:
        loc = geocode(query)
        if loc:
            lats.append(loc.latitude)
            lons.append(loc.longitude)
            print(f"  [{idx+1}/33] {row['Location']} → {loc.latitude:.4f}, {loc.longitude:.4f}")
        else:
            # Nominatim returned no result for this address
            # Common causes: ambiguous name, private property, typo in source
            lats.append(None)
            lons.append(None)
            print(f"  [{idx+1}/33] {row['Location']} → NOT FOUND")
    except Exception as e:
        lats.append(None)
        lons.append(None)
        print(f"  [{idx+1}/33] {row['Location']} → ERROR: {e}")

sdcc["lat"] = lats
sdcc["lon"] = lons

# Report which records could not be geocoded
failed = sdcc[sdcc["lat"].isna()]
if len(failed) > 0:
    print(f"\nWarning: {len(failed)} records could not be geocoded:")
    print(failed[["LEA", "Location"]].to_string())

sdcc_clean = pd.DataFrame({
    "id":           ["sdcc_" + str(i) for i in range(len(sdcc))],
    "lat":          sdcc["lat"].values,
    "lon":          sdcc["lon"].values,
    "address":      sdcc["Location"].values,
    "operator":     sdcc["Operator"].values,
    "num_chargers": sdcc["Number_of_chargers"].values,
    "source_area":  "SDCC",
    "open_hours":   "Unknown"
})
print(f"SDCC clean: {len(sdcc_clean)} records")

# 4. Merge all three sources
# Concatenate into one DataFrame. ignore_index resets row numbers.
combined = pd.concat([esb_clean, dlr_clean, sdcc_clean], ignore_index=True)
print(f"\nTotal before dedup: {len(combined)} records")

# Remove any records where geocoding failed (lat or lon is None/NaN).
# These cannot be used for spatial analysis.
combined = combined.dropna(subset=["lat", "lon"]).reset_index(drop=True)
print(f"Total after dropping null coords: {len(combined)} records")

# 5. Deduplicate physically-identical charging stations
# ESB (national), DLR, and SDCC are independent datasets that can
# describe the same real-world charging station — e.g. a Luas park
# & ride site appearing once in ESB's national list and once in
# DLR's local list with near-identical coordinates and address text.
# We merge any records within DEDUP_RADIUS_M of each other.
#
# Records are grouped using a union-find (connected components)
# approach rather than simple pairwise merging. This matters because
# duplication is sometimes transitive across three records, not just
# two — e.g. esb_65, dlr_8, and dlr_27 all describe the same
# Stillorgan Luas Park & Ride site, with dlr_8 and dlr_27 also being
# an internal DLR duplicate. A naive pairwise pass risks merging only
# two of the three and leaving one stray duplicate behind; union-find
# guarantees the full group is merged together in one pass.
#
# When a group contains multiple records, the representative kept is:
#   1. The ESB_national record, if one exists in the group (ESB is
#      the primary, most complete national dataset — see README).
#   2. Otherwise, the record that appears first in the merged table
#      (i.e. lowest row index — earliest in ESB > DLR > SDCC order).
DEDUP_RADIUS_M = 50

print(f"\nChecking for duplicate stations within {DEDUP_RADIUS_M}m...")

n = len(combined)
parent = list(range(n))


def find(x):
    while parent[x] != x:
        x = parent[x]
    return x


def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[rx] = ry


lats = combined["lat"].to_numpy()
lons = combined["lon"].to_numpy()

# O(n^2) pairwise comparison. With ~134 records this runs in well
# under a second; if the merged dataset grows substantially larger
# (e.g. after adding more county council sources), a spatial index
# (e.g. a KD-tree via scipy.spatial.cKDTree) would be a faster
# alternative, but is not necessary at this scale.
for i in range(n):
    for j in range(i + 1, n):
        d = haversine(lats[i], lons[i], lats[j], lons[j])
        if d <= DEDUP_RADIUS_M:
            union(i, j)

groups = {}
for i in range(n):
    root = find(i)
    groups.setdefault(root, []).append(i)

duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
n_duplicate_records = sum(len(v) for v in duplicate_groups.values())
print(f"Found {len(duplicate_groups)} duplicate groups "
      f"covering {n_duplicate_records} records "
      f"({n_duplicate_records - len(duplicate_groups)} will be removed)")

# Pick a representative index for each group, then build the final
# row order by keeping one row per group (sorted by the original
# index of the representative, to keep output order stable).
keep_indices = []
for root, idxs in groups.items():
    if len(idxs) == 1:
        keep_indices.append(idxs[0])
        continue
    # Prefer ESB_national if present in this group
    esb_idxs = [i for i in idxs if combined.loc[i, "source_area"] == "ESB_national"]
    representative = esb_idxs[0] if esb_idxs else min(idxs)
    keep_indices.append(representative)

    merged_ids = [combined.loc[i, "id"] for i in idxs]
    kept_id = combined.loc[representative, "id"]
    print(f"  Merged {merged_ids} -> kept {kept_id}")

combined = combined.loc[sorted(keep_indices)].reset_index(drop=True)
print(f"Total after deduplication: {len(combined)} records")

# 6. Export to GeoJSON
# Convert the DataFrame to a GeoDataFrame by creating Point geometries.
# Point(lon, lat) — note longitude first, then latitude (GeoJSON standard).
# CRS EPSG:4326 = WGS84, the standard GPS coordinate system.
geometry = [Point(row.lon, row.lat) for _, row in combined.iterrows()]
gdf = gpd.GeoDataFrame(combined, geometry=geometry, crs="EPSG:4326")
gdf.to_file("output/dublin_ev_chargers.geojson", driver="GeoJSON")
print(f"\nSaved: output/dublin_ev_chargers.geojson")
print(f"Final record count: {len(gdf)}")
print("\nSample:")
print(combined[["id","address","operator","num_chargers","source_area"]].head(5).to_string())