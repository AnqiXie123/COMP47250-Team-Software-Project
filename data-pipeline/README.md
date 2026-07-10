# EcoCharge Dublin — Data Pipeline

This directory contains all data ingestion and cleaning scripts
for the EcoCharge Dublin project (COMP47250 Team llxw).

---

## Prerequisites

Install required Python packages:

```bash
pip install pandas geopandas geopy openpyxl requests
```

---

## Pipeline Scripts

Run the scripts in order:

### Step 0 — Fetch raw data
```bash
python 00_fetch_raw_data.py
```
Downloads the following files into `raw/`:
- `its-data-ecars-sites-roi-ni.csv` — ESB eCars charge point locations (Ireland)
- `System-Data-Qtr-Hourly-2026-V4.xlsx` — EirGrid wind & solar generation 2026

### Step 1 — Clean EV charger data
```bash
python 01_clean_ev_chargers.py
```
Merges three EV charger datasets and geocodes missing coordinates.

**Manual setup required:** Before running, place these files in `raw/`:
- `ev-charging-points-dlr.geojson` — download from [Smart Dublin](https://data.smartdublin.ie/dataset/public-ev-charging-points-dlr)
- `Public_EV_Charging_Points_SDCC.csv` — download from [Smart Dublin](https://data.smartdublin.ie/dataset/public-ev-charging-points-sdcc1)

Output: `output/dublin_ev_chargers.geojson`
- 115 records covering all Dublin areas (ESB eCars + DLR + SDCC, deduplicated using 50m radius union-find)
- Fields: `id, lat, lon, address, operator, num_chargers, source_area, open_hours`

### Step 2 — Clean EirGrid energy data
```bash
python 02_clean_energy_data.py
```
Processes EirGrid quarterly hourly system data.

Output: `output/eirgrid_renewable_2026.csv`
- 11,516 rows, 15-minute intervals, January–April 2026
- Fields: `datetime, wind_mw, solar_mw, total_demand_mw,`
  `wind_penetration, solar_penetration, renewable_score`

### Step 3 — Clean DLR traffic data
```bash
python 03_clean_traffic_data.py
```
Cleans and aggregates SCATS DLR 2023 monthly traffic data to site level, joined with site location coordinates.

**Manual setup required:** Before running, place these files in `raw/`:
- `scats_dlr_<month>_2023.csv` (12 monthly files) — download from [Smart Dublin](https://data.smartdublin.ie/dataset/traffic-volumes-from-scats-traffic-management-system-2023)
- `scats_dlr_site_locations.csv` — download from [Smart Dublin](https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dlr)

Output: `output/cleaned_traffic_dlr_2023.csv` (not committed to GitHub — 110MB, exceeds size limit; see Known Limitations)
- ~1.9 million rows, 223 monitored sites, hourly resolution
- Fields: `site_id, datetime, region, sum_volume, avg_volume, lat, lon`

### Step 4 — Fetch OSM road network
```bash
python 04_fetch_osm_roads.py
```
Fetches Dublin's primary/secondary/tertiary road network from OpenStreetMap via the Overpass API.

Output: `output/dublin_roads.geojson`
- 10,667 road segments
- Fields: `road_id, name, highway_type, oneway, maxspeed`

### Step 5 — Build unified feature dataset
```bash
python 05_build_feature_dataset.py
```
Combines DLR and DCC traffic data with EV charger and road data into a single feature table for K-Means clustering, using Haversine distance to compute proximity features.

**Note:** DLR's 223 sites overlap almost entirely with DCC's coverage (222 of 223 are the same physical SCATS sensors, confirmed by site_id and 0m distance match). Where a site exists in both sources, the DCC value (2024-2025, more recent) is kept and the DLR value (2023) is discarded — see script docstring for full reasoning.

Output: `output/unified_features_v4.csv` (supersedes v2/v3, which are kept for reference)
- 1,039 rows (DLR + DCC + SDCC combined, deduplicated)
- Fields: `location_id, lat, lon, traffic_volume, traffic_source, distance_to_nearest_windfarm_km, distance_to_nearest_substation_m, charger_count_nearby, road_density, ev_penetration_proxy`
- `distance_to_nearest_windfarm_km`: primary spatial renewable proxy for K-Means — Haversine distance to nearest connected wind farm (SEAI dataset, 313 farms across Ireland, range 0.07–22.3km across Dublin sites; see Step 9)
- `distance_to_nearest_substation_m`: retained as reference field for dashboard display; NOT recommended for K-Means — Dublin's grid density is too high (range 8–504m) to provide meaningful spatial variation (see `docs/spatial_renewable_investigation.md`)
- `traffic_source` indicates which dataset traffic_volume came from (`DLR_2023`, `DCC_2024_2025`, or `SDCC_2024`)
- Delivered to ML teammate for K-Means clustering

### Step 6 — Clean DCC traffic data
```bash
python 06_clean_traffic_dcc.py
```
Extends traffic coverage beyond DLR by cleaning SCATS DCC (Dublin City Council) monthly data and joining DCC site location coordinates.

**Manual setup required:** Before running, place these files in `raw/`:
- `SCATS<Month><Year>.csv` (available months only: Dec 2024, Mar/Apr/May/Aug 2025 — DCC has not published all months) — download from Smart Dublin DCC SCATS datasets
- `dcc_site_locations.csv` — download from [Smart Dublin](https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dcc)

Output: `output/cleaned_traffic_dcc_2025.csv` (not committed to GitHub — ~190MB, exceeds size limit; see Known Limitations)
- ~3.16 million rows, 1,090 sites, hourly resolution
- 95.1% coordinate match rate (117 site_ids have no matching location record)
- Fields: `site_id, datetime, region, sum_volume, avg_volume, lat, lon`

### Step 7 — Clean SDCC traffic data
```bash
python 07_clean_traffic_sdcc.py
```
Extends traffic coverage into South Dublin by cleaning SCOOT-based traffic flow data and joining SDCC site location coordinates.

**Manual setup required:** Before running, place these files in `raw/`:
- `Traffic_Flow_Data_*_SDCC.geojson` — download from Smart Dublin (SDCC traffic flow datasets)
- `sdcc_site_names.csv` — download from [South Dublin County Council Open Data](https://data-sdublincoco.opendata.arcgis.com/datasets/sdublincoco::traffic-data-site-names-sdcc) (CSV download, not the data.smartdublin.ie listing page, which does not host the file directly)

Output: `output/cleaned_traffic_sdcc_2024.csv`
- 65 sites (37 physical junctions, multiple detection directions each) — confirmed via repeated download that this is South Dublin's full SCOOT network extent, not a truncated/partial download
- 100% coordinate match rate
- Fields: `site_id, flow, lat, lon, locn`
- **Note:** `flow` is a SCOOT-modelled demand estimate, not a direct SCATS vehicle count — values are ~5x smaller than DCC/DLR on average. See 05's docstring for how this is flagged downstream.

### Step 8 — Clean ESB Networks substation data
```bash
python 08_clean_esb_substations.py
```
Extracts Dublin-area ESB Networks substation locations from the
Network Capacity Heatmap Excel file, producing coordinates for
use as a spatial renewable energy proxy feature in Step 5.

**Manual setup required:** Before running, place this file in `raw/`:
- `customer-heatmap-download-december-2025.xlsx` — download from
  [ESB Networks Network Capacity Heatmap](https://www.esbnetworks.ie/services/get-connected/renewable-connection/network-capacity-heatmap)
  (free download, no registration required, updated quarterly)

Output: `output/dublin_substations.csv`
- 7,780 substations in the Dublin bounding box (LV: 7,664 / MV: 96 / HV: 20)
- Fields: `name, voltage_class, lat, lon`
- MV/LV coordinates are exact; HV coordinates are approximate
  per ESB Networks' own documentation

### Step 9 — Clean SEAI wind farm data
```bash
python 09_clean_wind_farms.py
```
Processes the SEAI Wind Farms Connected dataset to extract wind farm locations as the primary spatial renewable energy feature for K-Means clustering. Converts coordinates from Irish Grid (EPSG:29902) to WGS84 using pyproj.

**Manual setup required:** Before running, place this file in `raw/`:
- `WindFarmsConnectedJune2022.csv` — download from [data.gov.ie — SEAI Wind Farms](https://data.gov.ie/dataset/wind-farms-in-ireland) (CSV resource, CC BY 4.0, free download)

**Additional dependency:** `pip install pyproj`

Output: `output/ireland_wind_farms.csv`
- 313 connected wind farms across Ireland (no missing coordinates)
- Fields: `name, county, capacity_mw, lat, lon`
- ~14 wind farms within 60km of Dublin — sparse enough to produce 0.07–22.3km distance variation across Dublin traffic sites, unlike the ESB substation feature which proved too dense for meaningful K-Means differentiation

---

## Database Schema

See `schema.sql` for the full PostgreSQL + PostGIS + TimescaleDB schema.

Tables defined:
- `ev_chargers` — static EV charging station locations
- `renewable_energy` — time-series wind/solar generation data
- `traffic_volumes` — hourly SCATS traffic counts (DLR + DCC)
- `recommended_locations` — AI-recommended new charger sites (ML pipeline output)
To initialise the database:
```bash
psql -U postgres -d ecocharge -f schema.sql
```

---

## Raw Data Sources

| File | Source | Access |
|---|---|---|
| `its-data-ecars-sites-roi-ni.csv` | [data.gov.ie — ESB eCars](https://data.gov.ie/en_GB/dataset/esb-ev-public-charging-network) | Auto-downloaded by `00_fetch_raw_data.py` |
| `System-Data-Qtr-Hourly-2026-V4.xlsx` | [EirGrid](https://www.eirgrid.ie/grid/system-and-renewable-data-reports) | Auto-downloaded by `00_fetch_raw_data.py` |
| `ev-charging-points-dlr.geojson` | [Smart Dublin — DLR](https://data.smartdublin.ie/dataset/public-ev-charging-points-dlr) | Manual download required |
| `Public_EV_Charging_Points_SDCC.csv` | [Smart Dublin — SDCC](https://data.smartdublin.ie/dataset/public-ev-charging-points-sdcc1) | Manual download required |
| `SCATS<Month><Year>.csv` | Smart Dublin — DCC SCATS volumes | Manual download required (months vary — see Step 6) |
| `dcc_site_locations.csv` | [Smart Dublin — DCC site locations](https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dcc) | Manual download required |
| `customer-heatmap-download-december-2025.xlsx` | [ESB Networks Network Capacity Heatmap](https://www.esbnetworks.ie/services/get-connected/renewable-connection/network-capacity-heatmap) | Manual download required (free, no registration, updated quarterly) |
| `WindFarmsConnectedJune2022.csv` | [data.gov.ie — SEAI Wind Farms](https://data.gov.ie/dataset/wind-farms-in-ireland) | Manual download required (CC BY 4.0, free) |

> Note: The `raw/` and `output/` directories are excluded from version
> control via `.gitignore`. Raw data files must be obtained separately.
> Additionally, `output/cleaned_traffic_dcc_2025.csv` (~190MB) is
> excluded from version control for the same reason as the DLR
> traffic file above (GitHub's 100MB file size limit). Run
> `06_clean_traffic_dcc.py` locally to regenerate it.
> `output/dublin_substations.csv` is generated by running
> `08_clean_esb_substations.py` from the downloaded Excel file.

---

## Known Limitations

- SDCC charger data: 23 out of 33 records could not be geocoded due to
  ambiguous address strings; these are excluded from the output
- EirGrid data covers Ireland nationally; no Dublin sub-region breakdown
  is available. The constant `renewable_score` feature has been replaced
  by `distance_to_nearest_windfarm_km` in `unified_features_v4.csv` —
  distance to the nearest connected wind farm (SEAI dataset, 313 farms).
  `distance_to_nearest_substation_m` was evaluated as an intermediate
  candidate but found unsuitable for K-Means due to Dublin's extremely
  high grid density (almost all sites within 100m of a substation).
  See `docs/spatial_renewable_investigation.md` for the full investigation.
  The full EirGrid time-series (02 output) is still used separately as
  a dashboard visualisation layer
- Coordinate-based deduplication of EV chargers has been implemented
  (50m radius union-find, 134 → 115 records); however, 23 SDCC charger
  records remain excluded due to geocoding failures (see first point above)
- Traffic coverage: DLR (03), DCC (06), and SDCC (07) are all integrated
  into `unified_features_v4.csv` (1,039 sites total). FCC (Fingal) has
  no usable traffic data source — confirmed after re-investigation on
  2026-06-29. SDCC uses SCOOT (not SCATS); its `flow` values average ~5x
  lower than DCC's `sum_volume` and are excluded from K-Means training
  per ML teammate's decision, but retained in `traffic_sites` for
  dashboard heatmap display
- `output/cleaned_traffic_dlr_2023.csv` (~110MB) and
  `output/cleaned_traffic_dcc_2025.csv` (~190MB) and
  `output/cleaned_traffic_sdcc_2024.csv` are excluded from version
  control due to GitHub's 100MB file size limit; run scripts 03, 06,
  and 07 locally to regenerate them