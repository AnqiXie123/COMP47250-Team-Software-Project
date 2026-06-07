# Backend Design — EcoCharge Dublin
Date: 2026-06-07
Sprint target: Sprint 2 (MVP by 22 Jun)

## Overview

The backend provides a FastAPI REST service that serves EV charger and renewable energy data to the React + Leaflet frontend. It connects to a local PostgreSQL + PostGIS database populated by one-off ingestion scripts.

TimescaleDB is deferred to Docker deployment (Sprint 4). For local development, the `create_hypertable` calls in `schema.sql` are skipped.

---

## Project Structure

```
backend/
├── main.py              # FastAPI app entry point, mounts routers
├── database.py          # Async SQLAlchemy engine + session factory
├── routers/
│   ├── chargers.py      # GET /api/chargers
│   └── energy.py        # GET /api/energy/latest
├── ingest/
│   ├── load_chargers.py # One-off: loads dublin_ev_chargers.geojson into ev_chargers table
│   └── load_energy.py   # One-off: loads eirgrid_renewable_2026.csv into renewable_energy table
└── requirements.txt
```

`ingest/` scripts are run once to populate the database. They are not part of the API.

---

## Database

- **Engine:** PostgreSQL 17 (local) with PostGIS extension
- **Schema:** defined in `data-pipeline/schema.sql`
- **Local setup:**
  1. `brew install postgresql@17 postgis`
  2. Create database: `createdb ecocharge`
  3. Apply schema with TimescaleDB lines commented out:
     ```bash
     psql -U postgres -d ecocharge -f data-pipeline/schema.sql
     ```
  Lines to comment out for local dev (no TimescaleDB):
  - `CREATE EXTENSION IF NOT EXISTS timescaledb;`
  - Both `SELECT create_hypertable(...)` blocks

---

## Ingestion Scripts

### `ingest/load_chargers.py`
- Reads `data-pipeline/output/dublin_ev_chargers.geojson`
- Inserts each feature as a row in `ev_chargers`
- Populates `geom` using `ST_MakePoint(lon, lat)` with SRID 4326
- Uses `ON CONFLICT (id) DO NOTHING` to allow safe re-runs

### `ingest/load_energy.py`
- Reads `data-pipeline/output/eirgrid_renewable_2026.csv`
- Bulk inserts into `renewable_energy`
- Parses `datetime` column as UTC-aware timestamp

---

## API Endpoints (Sprint 2)

### `GET /api/chargers`
Returns all EV charging stations.

Response:
```json
[
  {
    "id": "esb_0",
    "lat": 53.611523,
    "lon": -6.182852,
    "address": "Irish Rail, Railway Street, Balbriggan",
    "operator": "ESB eCars",
    "num_chargers": 1,
    "source_area": "ESB_national",
    "open_hours": "24 x 7"
  }
]
```

### `GET /api/energy/latest`
Returns the most recent 15-minute renewable energy record.

Response:
```json
{
  "datetime": "2026-04-30T23:45:00Z",
  "wind_mw": 1823.4,
  "solar_mw": 0.0,
  "total_demand_mw": 3241.0,
  "renewable_score": 0.563
}
```

---

## Tech Stack

| Component | Library |
|---|---|
| Web framework | FastAPI |
| Async DB driver | asyncpg |
| ORM / connection | SQLAlchemy 2.0 (async) |
| Ingestion scripts | psycopg2 (sync, one-off use) |
| Data parsing | pandas, json (stdlib) |

---

## Deferred to Later Sprints

- `GET /api/traffic` — traffic volume heatmap data (Sprint 3, after SCATS spatial join is done)
- `GET /api/recommendations` — K-Means ranked charging site suggestions (Sprint 3)
- `GET /api/energy/range` — time-range renewable score query (Sprint 3)
- TimescaleDB hypertables (Sprint 4, Docker deployment)
- CORS configuration for production (Sprint 4)
