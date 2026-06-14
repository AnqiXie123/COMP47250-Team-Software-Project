"""
04_fetch_osm_roads.py
---------------------
Fetches the Dublin road network from OpenStreetMap via the
Overpass API and saves it as a GeoJSON file.

Only primary, secondary, and tertiary roads are included to
keep the file size manageable (~5MB vs ~30MB for all roads).
These road types represent the main routes where EV charging
demand is highest.

Output:
  output/dublin_roads.geojson
  - Fields: road_id, name, highway_type, geometry (LineString)
  - Coordinate system: WGS84 (EPSG:4326)

Usage:
  python 04_fetch_osm_roads.py
"""

import requests
import json
import os

os.makedirs("output", exist_ok=True)

# Define the Overpass API query
# We query for ways (roads) within the Dublin administrative area.
# admin_level=7: corresponds to Dublin City Council boundary in OSM.
# Filter to only primary, secondary, and tertiary road types:
#   primary   = major roads (e.g. N11, N81)
#   secondary = important local roads
#   tertiary  = connecting roads
# This reduces data volume from ~30MB to ~5MB while keeping
# all roads relevant to EV charging demand modelling.
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERY = """
[out:json][timeout:90];
(
  way["highway"="primary"](53.2,-6.45,53.45,-6.0);
  way["highway"="secondary"](53.2,-6.45,53.45,-6.0);
  way["highway"="tertiary"](53.2,-6.45,53.45,-6.0);
);
out geom;
"""

# 2. Send request to Overpass API
print("Fetching Dublin road network from OpenStreetMap...")
print("(This may take 20-30 seconds)")

try:
    response = requests.get(
        OVERPASS_URL,
        params={"data": QUERY},
        headers={
            "Accept": "application/json",
            "User-Agent": "EcoChargeDublin/1.0"
        },
        timeout=120
    )
    response.raise_for_status()
    osm_data = response.json()
    print(f"Received {len(osm_data['elements'])} elements from OSM")

except requests.exceptions.RequestException as e:
    print(f"ERROR: Could not fetch OSM data: {e}")
    exit(1)

# 3. Parse OSM response into GeoJSON format
# With "out geom", each way element contains geometry directly
# as a list of {lat, lon} objects — no need for separate node lookup.

features = []
road_count = 0

for element in osm_data["elements"]:
    if element["type"] != "way":
        continue

    # Extract coordinates directly from geometry field
    geometry = element.get("geometry", [])
    if len(geometry) < 2:
        continue

    # GeoJSON uses [lon, lat] order
    coords = [[pt["lon"], pt["lat"]] for pt in geometry]

    tags = element.get("tags", {})

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        },
        "properties": {
            "road_id":      str(element["id"]),
            "name":         tags.get("name", ""),
            "highway_type": tags.get("highway", ""),
            "oneway":       tags.get("oneway", "no"),
            "maxspeed":     tags.get("maxspeed", "")
        }
    }
    features.append(feature)
    road_count += 1

print(f"Roads parsed: {road_count}")

# 4. Save as GeoJSON
geojson = {
    "type": "FeatureCollection",
    "features": features
}

output_path = "output/dublin_roads.geojson"
with open(output_path, "w") as f:
    json.dump(geojson, f)

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"\nSaved: {output_path}")
print(f"File size: {size_mb:.1f} MB")
print(f"Total roads: {road_count}")
print("\nSample road properties:")
if features:
    print(json.dumps(features[0]["properties"], indent=2))
print("\nNext step: run 05_build_feature_dataset.py")