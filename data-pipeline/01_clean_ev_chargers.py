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

os.makedirs("output", exist_ok=True)

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
combined = combined.dropna(subset=["lat", "lon"])
print(f"Total after dropping null coords: {len(combined)} records")

# 5. Export to GeoJSON
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