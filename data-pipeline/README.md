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

---

## Database Schema

See `schema.sql` for the full PostgreSQL + PostGIS + TimescaleDB schema.

Tables defined:
- `ev_chargers` — static EV charging station locations
- `renewable_energy` — time-series wind/solar generation data
- `traffic_volumes` — hourly SCATS traffic counts (Phase 3)

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

> Note: The `raw/` and `output/` directories are excluded from version
> control via `.gitignore`. Raw data files must be obtained separately.

---

## Known Limitations

- SDCC charger data: 23 out of 33 records could not be geocoded due to
  ambiguous address strings; these are excluded from the output
- EirGrid data covers Ireland nationally; no Dublin sub-region breakdown
  is available — national figures are used as a documented proxy
- Coordinate-based deduplication of EV chargers (merging records within
  50m radius) is planned as a Phase 2 database task