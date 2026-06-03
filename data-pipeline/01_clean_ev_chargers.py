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
esb = pd.read_csv("raw/its-data-ecars-sites-roi-ni.csv")
esb_dublin = esb[esb["County"] == "Dublin"].copy()

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
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dlr_gdf = gpd.read_file("raw/ev-charging-points-dlr.geojson")

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
sdcc = pd.read_csv("raw/Public_EV_Charging_Points_SDCC.csv")

geolocator = Nominatim(user_agent="ecocharge_dublin_p15")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

print("Geocoding SDCC addresses (33 records, ~1 min)...")
lats, lons = [], []
for idx, row in sdcc.iterrows():
    query = f"{row['Location']}, {row['LEA']}, Dublin, Ireland"
    try:
        loc = geocode(query)
        if loc:
            lats.append(loc.latitude)
            lons.append(loc.longitude)
            print(f"  [{idx+1}/33] {row['Location']} → {loc.latitude:.4f}, {loc.longitude:.4f}")
        else:
            lats.append(None)
            lons.append(None)
            print(f"  [{idx+1}/33] {row['Location']} → NOT FOUND")
    except Exception as e:
        lats.append(None)
        lons.append(None)
        print(f"  [{idx+1}/33] {row['Location']} → ERROR: {e}")

sdcc["lat"] = lats
sdcc["lon"] = lons

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
combined = pd.concat([esb_clean, dlr_clean, sdcc_clean], ignore_index=True)
print(f"\nTotal before dedup: {len(combined)} records")

combined = combined.dropna(subset=["lat", "lon"])
print(f"Total after dropping null coords: {len(combined)} records")

# 5. Export to GeoJSON
geometry = [Point(row.lon, row.lat) for _, row in combined.iterrows()]
gdf = gpd.GeoDataFrame(combined, geometry=geometry, crs="EPSG:4326")
gdf.to_file("output/dublin_ev_chargers.geojson", driver="GeoJSON")
print(f"\nSaved: output/dublin_ev_chargers.geojson")
print(f"Final record count: {len(gdf)}")
print("\nSample:")
print(combined[["id","address","operator","num_chargers","source_area"]].head(5).to_string())