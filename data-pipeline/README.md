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
- 133 records covering all Dublin areas (ESB eCars + DLR + SDCC)
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

Output: `output/unified_features_v2.csv` (supersedes `unified_features.csv`, which is kept for comparison)
- 974 rows (1 DLR-only site + 973 DCC sites, including deduplicated overlap)
- Fields: `location_id, lat, lon, traffic_volume, traffic_source, charger_count_nearby, road_density, ev_penetration_proxy`
- `traffic_source` indicates which dataset traffic_volume came from (`DLR_2023` or `DCC_2024_2025`)
- `renewable_score` has been removed (was a constant national value, no spatial signal — see Known Limitations)
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

> Note: The `raw/` and `output/` directories are excluded from version
> control via `.gitignore`. Raw data files must be obtained separately.
> Additionally, `output/cleaned_traffic_dcc_2025.csv` (~190MB) is
> excluded from version control for the same reason as the DLR
> traffic file above (GitHub's 100MB file size limit). Run
> `06_clean_traffic_dcc.py` locally to regenerate it.

---

## Known Limitations

- SDCC charger data: 23 out of 33 records could not be geocoded due to
  ambiguous address strings; these are excluded from the output
- EirGrid data covers Ireland nationally; no Dublin sub-region breakdown
  is available. renewable_score was previously included as a K-Means
  feature but added no spatial signal (single national constant) — it
  has been removed from unified_features_v2.csv as of 06-29-2026. The
  full time-series (02 output) is still used separately as a dashboard
  visualisation layer
- Coordinate-based deduplication of EV chargers (merging records within
  50m radius) has not yet been implemented — ESB and DLR datasets may
  contain duplicate physical charging stations recorded by different
  operators
- Traffic coverage: DLR (03) covers 223 sites for all of 2023; DCC (06)
  covers 1,090 sites but only for the months Dublin City Council has
  published (Dec 2024, Mar/Apr/May/Aug 2025 — other months are missing
  from the source). SDCC traffic data exists but lacks a usable site
  location file for spatial joining; FCC (Fingal) has no traffic data
  source identified at all
- The unified feature dataset (05) currently uses DLR sites only;
  merging in DCC coverage is planned but not yet implemented