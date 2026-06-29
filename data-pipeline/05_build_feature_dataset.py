"""
05_build_feature_dataset.py
---------------------------
Constructs the unified feature dataset for K-Means clustering.

Each row represents one SCATS traffic sensor site. Coverage now
combines two traffic sources rather than DLR alone:
  - DLR (Dun Laoghaire-Rathdown), 223 sites, full year 2023
  - DCC (Dublin City), 973 sites with coordinates, partial coverage
    (Dec 2024, Mar/Apr/May/Aug 2025 — other months not published)

IMPORTANT — these two sources overlap substantially. A check against
the real data (see check_dlr_dcc_overlap.py) found that 222 of the
223 DLR sites share the same site_id, at 0m apart, with a DCC site —
i.e. DLR's coverage area sits almost entirely inside DCC's, and most
"DLR sites" are the same physical SCATS sensors also captured in the
DCC dataset, just reported by a different council and for a
different time period. This is not simply two complementary
datasets to concatenate; site_id must be deduplicated across them.

Deduplication rule (decided 2026-06-29, see team chat log): for any
site_id present in both sources, the DCC value (2024-2025, more
recent) is kept and the DLR value (2023) is discarded. Sites present
in only one source are kept as-is. This means traffic_volume for a
formerly-DLR site may now reflect a different time period than
before — see the `traffic_source` column for full traceability.

renewable_score has been REMOVED from this version's output. It
was previously a single national mean value (~0.41) duplicated
across every row, contributing no spatial signal to clustering.
EirGrid does not publish sub-regional data, so until a spatially
explicit energy data source is found (e.g. ESB Networks substation
locations), this column is dropped rather than populated with a
constant placeholder. The full EirGrid time-series is still used
separately as a dashboard visualisation layer (see
02_clean_energy_data.py output), just not as a clustering feature.

For each site, we calculate:
  - traffic_volume        : mean hourly vehicle count (DLR 2023 or
                             DCC 2024-2025, per the dedup rule above)
  - traffic_source         : which dataset traffic_volume came from
                             ("DLR_2023" or "DCC_2024_2025") — kept
                             for traceability since the two sources
                             cover different time periods
  - charger_count_nearby  : number of EV chargers within 500m
  - road_density          : number of road segments within 500m
  - ev_penetration_proxy  : fixed Dublin weighting (0.049)

Input files:
  output/cleaned_traffic_dlr_2023.csv   (from 03_clean_traffic_data.py)
  output/cleaned_traffic_dcc_2025.csv   (from 06_clean_traffic_dcc.py)
  output/dublin_ev_chargers.geojson     (from 01_clean_ev_chargers.py,
                                          deduplicated version, 115 records)
  output/dublin_roads.geojson           (from 04_fetch_osm_roads.py)

Output:
  output/unified_features_v2.csv
  - ~974 rows (one per unique site across DLR + DCC; exact count
    depends on how many DCC sites have valid coordinates at run
    time, since the DCC site location join is not 100% complete —
    see 06_clean_traffic_dcc.py)
  - Fields: location_id, lat, lon, traffic_volume, traffic_source,
            charger_count_nearby, road_density, ev_penetration_proxy
  - No null values
  - Named _v2 (not overwriting unified_features.csv) so the
    interim-stage file remains available for comparison/reference

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

# 1. Load traffic data from BOTH sources and merge with deduplication
#
# Step 1a: DLR — compute mean hourly volume per site (2023 full year)
print("Loading DLR traffic data...")
dlr_traffic = pd.read_csv("output/cleaned_traffic_dlr_2023.csv")

dlr_site_traffic = (
    dlr_traffic.groupby("site_id")
    .agg(
        traffic_volume=("sum_volume", "mean"),
        lat=("lat", "first"),
        lon=("lon", "first")
    )
    .reset_index()
)
dlr_site_traffic["traffic_volume"] = dlr_site_traffic["traffic_volume"].round(2)
dlr_site_traffic["site_id"] = dlr_site_traffic["site_id"].astype(str)
dlr_site_traffic["traffic_source"] = "DLR_2023"
# Drop any site with no coordinates — can't be used spatially
dlr_site_traffic = dlr_site_traffic.dropna(subset=["lat", "lon"])
print(f"DLR sites loaded (with coords): {len(dlr_site_traffic)}")

# Step 1b: DCC — compute mean hourly volume per site (2024-12, 2025
# Mar/Apr/May/Aug — see 06_clean_traffic_dcc.py for the documented
# month gaps)
print("Loading DCC traffic data...")
dcc_traffic = pd.read_csv("output/cleaned_traffic_dcc_2025.csv")

dcc_site_traffic = (
    dcc_traffic.groupby("site_id")
    .agg(
        traffic_volume=("sum_volume", "mean"),
        lat=("lat", "first"),
        lon=("lon", "first")
    )
    .reset_index()
)
dcc_site_traffic["traffic_volume"] = dcc_site_traffic["traffic_volume"].round(2)
dcc_site_traffic["site_id"] = dcc_site_traffic["site_id"].astype(str)
dcc_site_traffic["traffic_source"] = "DCC_2024_2025"
# Drop sites with no coordinates — 06's site-location join is not
# 100% complete (95.1% match rate), so some DCC sites have null
# lat/lon and cannot be used here.
dcc_site_traffic = dcc_site_traffic.dropna(subset=["lat", "lon"])
print(f"DCC sites loaded (with coords): {len(dcc_site_traffic)}")

# Step 1c: Merge with deduplication.
#
# A check against the real data (check_dlr_dcc_overlap.py) found
# that DLR's coverage area sits almost entirely inside DCC's — 222
# of 223 DLR site_ids are also present in DCC, at the same physical
# location (0m apart in nearly every case). These are NOT two
# independent datasets to concatenate; they are largely the same
# real-world sensors, reported by two different councils for two
# different time periods.
#
# Decision: where a site_id exists in both, keep the DCC value
# (2024-2025, more recent) and discard the DLR value (2023). Sites
# present in only one source are kept as-is. See module docstring
# for the full reasoning.
print("\nMerging DLR and DCC, with DCC taking priority for overlapping site_ids...")

dcc_site_ids = set(dcc_site_traffic["site_id"])
dlr_only = dlr_site_traffic[~dlr_site_traffic["site_id"].isin(dcc_site_ids)]

print(f"DLR sites also present in DCC (dropped, DCC value used instead): "
      f"{len(dlr_site_traffic) - len(dlr_only)}")
print(f"DLR sites NOT in DCC (kept as DLR_2023): {len(dlr_only)}")

site_traffic = pd.concat(
    [dcc_site_traffic, dlr_only], ignore_index=True
)

# Sanity check: site_id should now be unique. If this fails, the
# dedup logic above has a bug and must be fixed before continuing —
# duplicate site_ids would silently double-count locations in the
# K-Means input, the same kind of issue this script is being
# revised to avoid.
n_dupes = site_traffic["site_id"].duplicated().sum()
if n_dupes > 0:
    raise ValueError(
        f"{n_dupes} duplicate site_id(s) remain after merge — "
        "dedup logic is broken, do not proceed to K-Means with this output."
    )

print(f"Total unique sites after merge: {len(site_traffic)}")
print(f"  By source: {site_traffic['traffic_source'].value_counts().to_dict()}")

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

# 4. (Renewable energy step removed — see module docstring. The
# renewable_score column is no longer produced here; the full
# EirGrid time-series remains available separately in
# output/eirgrid_renewable_2026.csv for dashboard visualisation.)

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
    "location_id":          site_traffic["site_id"],
    "lat":                  site_traffic["lat"].round(6),
    "lon":                  site_traffic["lon"].round(6),
    "traffic_volume":       site_traffic["traffic_volume"],
    "traffic_source":       site_traffic["traffic_source"],
    "charger_count_nearby": charger_counts,
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
print(f"By traffic_source: {features_df['traffic_source'].value_counts().to_dict()}")
print(f"traffic_volume  — mean: {features_df['traffic_volume'].mean():.1f}, "
      f"min: {features_df['traffic_volume'].min():.1f}, "
      f"max: {features_df['traffic_volume'].max():.1f}")
print(f"charger_count_nearby — mean: {features_df['charger_count_nearby'].mean():.2f}, "
      f"max: {features_df['charger_count_nearby'].max()}")
print(f"road_density    — mean: {features_df['road_density'].mean():.1f}, "
      f"max: {features_df['road_density'].max()}")

# 8. Export
output_path = "output/unified_features_v2.csv"
features_df.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"Final record count: {len(features_df)}")
print("\nSample:")
print(features_df.head(5).to_string(index=False))
print("\nNOTE: renewable_score is no longer included in this file —")
print("see module docstring for why. Inform the ML teammate before")
print("they re-run K-Means: the feature set, row count, and traffic")
print("time period composition have all changed from unified_features.csv.")
print("\nFeature dataset ready for ML teammate (K-Means clustering).")