"""
05_build_feature_dataset.py
---------------------------
Constructs the unified feature dataset for K-Means clustering.

Each row represents one SCATS traffic sensor site (223 sites in
DLR area). For each site, we calculate:
  - traffic_volume        : mean hourly vehicle count across 2023
  - charger_count_nearby  : number of EV chargers within 500m
  - renewable_score       : mean renewable energy score (2026 data)
  - road_density          : number of road segments within 500m
  - ev_penetration_proxy  : fixed Dublin weighting (0.049)

Input files:
  output/cleaned_traffic_dlr_2023.csv   (from 03_clean_traffic_data.py)
  output/dublin_ev_chargers.geojson     (from 01_clean_ev_chargers.py)
  output/eirgrid_renewable_2026.csv     (from 02_clean_energy_data.py)
  output/dublin_roads.geojson           (from 04_fetch_osm_roads.py)

Output:
  output/unified_features.csv
  - 223 rows (one per SCATS site)
  - Fields: location_id, lat, lon, traffic_volume,
            charger_count_nearby, renewable_score,
            road_density, ev_penetration_proxy
  - No null values

Usage:
  python 05_build_feature_dataset.py
"""

import pandas as pd
import json
import math
import os

os.makedirs("output", exist_ok=True)

# Helper: Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in metres between two lat/lon points
    using the Haversine formula.
    Used to check if a charger or road segment is within 500m of a site.
    """
    R = 6371000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 1. Load traffic data — compute mean hourly volume per site
print("Loading traffic data...")
traffic = pd.read_csv("output/cleaned_traffic_dlr_2023.csv")

# Get one row per site with mean traffic volume and coordinates
site_traffic = (
    traffic.groupby("site_id")
    .agg(
        traffic_volume=("sum_volume", "mean"),
        lat=("lat", "first"),
        lon=("lon", "first")
    )
    .reset_index()
)
site_traffic["traffic_volume"] = site_traffic["traffic_volume"].round(2)
print(f"Sites loaded: {len(site_traffic)}")

# 2. Load EV charger data
print("Loading EV charger data...")
with open("output/dublin_ev_chargers.geojson") as f:
    charger_data = json.load(f)

# Extract charger coordinates into a simple list
chargers = [
    {
        "lat": feat["geometry"]["coordinates"][1],
        "lon": feat["geometry"]["coordinates"][0]
    }
    for feat in charger_data["features"]
]
print(f"Chargers loaded: {len(chargers)}")

# 3. Load road data
print("Loading road data...")
with open("output/dublin_roads.geojson") as f:
    road_data = json.load(f)

# For each road, use its midpoint as a representative coordinate
# This is simpler than checking the full LineString geometry
road_points = []
for feat in road_data["features"]:
    coords = feat["geometry"]["coordinates"]
    mid = coords[len(coords) // 2]  # midpoint of the road
    road_points.append({"lat": mid[1], "lon": mid[0]})

print(f"Road segments loaded: {len(road_points)}")

# 4. Load renewable energy data — compute overall mean score
print("Loading renewable energy data...")
energy = pd.read_csv("output/eirgrid_renewable_2026.csv")

# Use a single mean renewable_score across all timestamps.
# This is a simplification — a more sophisticated version would
# join by timestamp, but for the Interim MVP a static score is sufficient.
mean_renewable_score = round(energy["renewable_score"].mean(), 4)
print(f"Mean renewable score: {mean_renewable_score}")

# 5. Calculate features for each site
print("\nCalculating features for each site (this may take 1-2 minutes)...")

RADIUS_M = 500  # 500 metre radius for proximity calculations

charger_counts = []
road_densities = []

for idx, site in site_traffic.iterrows():
    site_lat = site["lat"]
    site_lon = site["lon"]

    # Count chargers within RADIUS_M metres
    nearby_chargers = sum(
        1 for c in chargers
        if haversine(site_lat, site_lon, c["lat"], c["lon"]) <= RADIUS_M
    )
    charger_counts.append(nearby_chargers)

    # Count road segments within RADIUS_M metres
    nearby_roads = sum(
        1 for r in road_points
        if haversine(site_lat, site_lon, r["lat"], r["lon"]) <= RADIUS_M
    )
    road_densities.append(nearby_roads)

    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(site_traffic)} sites...")

# 6. Assemble final feature dataset
print("\nAssembling feature dataset...")

features_df = pd.DataFrame({
    "location_id":          site_traffic["site_id"].astype(str),
    "lat":                  site_traffic["lat"].round(6),
    "lon":                  site_traffic["lon"].round(6),
    "traffic_volume":       site_traffic["traffic_volume"],
    "charger_count_nearby": charger_counts,
    "renewable_score":      mean_renewable_score,
    "road_density":         road_densities,
    "ev_penetration_proxy": 0.049
    # Dublin EV ownership rate (4.9%) from CSO Sustainable
    # Mobility and Transport 2021 report — used as a fixed
    # proxy since county-level breakdown is not available via API
})

# 7. Quality check
print("\n=== Quality Check ===")
print(f"Total rows: {len(features_df)}")
print(f"Null values: {features_df.isnull().sum().sum()}")
print(f"traffic_volume  — mean: {features_df['traffic_volume'].mean():.1f}, "
      f"min: {features_df['traffic_volume'].min():.1f}, "
      f"max: {features_df['traffic_volume'].max():.1f}")
print(f"charger_count_nearby — mean: {features_df['charger_count_nearby'].mean():.2f}, "
      f"max: {features_df['charger_count_nearby'].max()}")
print(f"road_density    — mean: {features_df['road_density'].mean():.1f}, "
      f"max: {features_df['road_density'].max()}")

# 8. Export
output_path = "output/unified_features.csv"
features_df.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(features_df)}")
print("\nSample:")
print(features_df.head(5).to_string(index=False))
print("\nFeature dataset ready for ML teammate (K-Means clustering).")