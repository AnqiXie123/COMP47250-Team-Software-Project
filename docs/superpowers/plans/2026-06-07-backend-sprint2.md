# Backend Sprint 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up a local PostgreSQL database, load EV charger and energy data into it, and expose two FastAPI endpoints (`GET /api/chargers` and `GET /api/energy/latest`) for the frontend map.

**Architecture:** FastAPI app with two routers (chargers, energy), each backed by an async SQLAlchemy session. Ingestion is handled by separate one-off Python scripts that run once to populate the database. Tests use FastAPI's TestClient with a dependency override to avoid needing a real database during testing.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), asyncpg, psycopg2-binary, PostgreSQL 17 + PostGIS, pytest, httpx

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `backend/schema_local.sql` | Create | Schema without TimescaleDB lines (for local dev) |
| `backend/requirements.txt` | Create | Python dependencies |
| `backend/__init__.py` | Create | Makes `backend` a Python package |
| `backend/database.py` | Create | Async SQLAlchemy engine + `get_db` dependency |
| `backend/main.py` | Create | FastAPI app entry point, mounts routers |
| `backend/routers/__init__.py` | Create | Package marker |
| `backend/routers/chargers.py` | Create | `GET /api/chargers` |
| `backend/routers/energy.py` | Create | `GET /api/energy/latest` |
| `backend/ingest/__init__.py` | Create | Package marker |
| `backend/ingest/load_chargers.py` | Create | Loads `dublin_ev_chargers.geojson` into `ev_chargers` |
| `backend/ingest/load_energy.py` | Create | Loads `eirgrid_renewable_2026.csv` into `renewable_energy` |
| `backend/tests/__init__.py` | Create | Package marker |
| `backend/tests/test_chargers.py` | Create | Tests for `GET /api/chargers` |
| `backend/tests/test_energy.py` | Create | Tests for `GET /api/energy/latest` |

All paths are relative to the repo root (`COMP47250-Team-Software-Projec/`).
Run all commands from the repo root unless stated otherwise.

---

## Task 1: Install PostgreSQL and create the database

**Files:**
- Create: `backend/schema_local.sql`

- [ ] **Step 1: Install PostgreSQL 17 and PostGIS via Homebrew**

```bash
brew install postgresql@17
brew install postgis
```

- [ ] **Step 2: Start PostgreSQL and add it to PATH**

```bash
brew services start postgresql@17
echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify with:
```bash
psql --version
```
Expected output contains: `psql (PostgreSQL) 17.x`

- [ ] **Step 3: Create the ecocharge database**

```bash
createdb ecocharge
```

Verify:
```bash
psql -d ecocharge -c "\l" | grep ecocharge
```
Expected: a row showing `ecocharge` in the list.

- [ ] **Step 4: Create `backend/schema_local.sql`**

This is a copy of `data-pipeline/schema.sql` with TimescaleDB removed so it works without that extension locally.

```sql
-- schema_local.sql
-- Same as schema.sql but without TimescaleDB.
-- Use this for local development. Use schema.sql for Docker deployment.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS ev_chargers (
    id              VARCHAR(50)      PRIMARY KEY,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    address         TEXT,
    operator        VARCHAR(100),
    num_chargers    INTEGER,
    source_area     VARCHAR(50),
    open_hours      VARCHAR(100),
    geom            GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_ev_chargers_geom
    ON ev_chargers USING GIST (geom);

CREATE TABLE IF NOT EXISTS renewable_energy (
    datetime            TIMESTAMPTZ      NOT NULL,
    wind_mw             DOUBLE PRECISION,
    solar_mw            DOUBLE PRECISION,
    total_demand_mw     DOUBLE PRECISION,
    wind_penetration    DOUBLE PRECISION,
    solar_penetration   DOUBLE PRECISION,
    renewable_score     DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_renewable_energy_datetime
    ON renewable_energy (datetime DESC);

CREATE TABLE IF NOT EXISTS traffic_volumes (
    datetime        TIMESTAMPTZ      NOT NULL,
    site_id         VARCHAR(20)      NOT NULL,
    detector        INTEGER,
    region          VARCHAR(50),
    sum_volume      INTEGER,
    avg_volume      DOUBLE PRECISION,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    geom            GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_traffic_volumes_site_time
    ON traffic_volumes (site_id, datetime DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_volumes_geom
    ON traffic_volumes USING GIST (geom);
```

- [ ] **Step 5: Apply the schema**

```bash
psql -d ecocharge -f backend/schema_local.sql
```

Expected output:
```
CREATE EXTENSION
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE INDEX
CREATE INDEX
```

- [ ] **Step 6: Verify tables exist**

```bash
psql -d ecocharge -c "\dt"
```

Expected: three tables listed — `ev_chargers`, `renewable_energy`, `traffic_volumes`.

- [ ] **Step 7: Commit**

```bash
git add backend/schema_local.sql
git commit -m "feat: add local dev schema without TimescaleDB"
```

---

## Task 2: Python project skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/ingest/__init__.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
psycopg2-binary==2.9.9
pandas==2.2.2
pytest==8.2.2
httpx==0.27.0
```

- [ ] **Step 2: Create the empty `__init__.py` files**

```bash
touch backend/__init__.py
touch backend/routers/__init__.py
touch backend/ingest/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r backend/requirements.txt
```

Expected: all packages install without errors. Check with:
```bash
python -c "import fastapi, sqlalchemy, asyncpg; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt backend/__init__.py backend/routers/__init__.py backend/ingest/__init__.py backend/tests/__init__.py
git commit -m "feat: add backend project skeleton and requirements"
```

---

## Task 3: Database connection module

**Files:**
- Create: `backend/database.py`

- [ ] **Step 1: Create `backend/database.py`**

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost/ecocharge"
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: Verify it imports without error**

```bash
python -c "from backend.database import get_db; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/database.py
git commit -m "feat: add async database connection module"
```

---

## Task 4: FastAPI app entry point

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Create `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chargers, energy

app = FastAPI(title="EcoCharge Dublin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(chargers.router)
app.include_router(energy.router)
```

This won't run yet because the router files don't exist. That's fine — create them in Tasks 5 and 6.

- [ ] **Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: add FastAPI app entry point with CORS"
```

---

## Task 5: Chargers endpoint (TDD)

**Files:**
- Create: `backend/routers/chargers.py`
- Create: `backend/tests/test_chargers.py`

- [ ] **Step 1: Write the failing test — create `backend/tests/test_chargers.py`**

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

SAMPLE_CHARGER = {
    "id": "esb_0",
    "lat": 53.611523,
    "lon": -6.182852,
    "address": "Irish Rail, Railway Street, Balbriggan",
    "operator": "ESB eCars",
    "num_chargers": 1,
    "source_area": "ESB_national",
    "open_hours": "24 x 7",
}


class _MockResult:
    def mappings(self):
        return self

    def all(self):
        return [SAMPLE_CHARGER]


class _MockSession:
    async def execute(self, query):
        return _MockResult()


async def _mock_get_db():
    yield _MockSession()


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = _mock_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_chargers_status_200():
    response = client.get("/api/chargers")
    assert response.status_code == 200


def test_get_chargers_returns_list():
    response = client.get("/api/chargers")
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_chargers_fields():
    response = client.get("/api/chargers")
    charger = response.json()[0]
    assert charger["id"] == "esb_0"
    assert charger["lat"] == 53.611523
    assert charger["lon"] == -6.182852
    assert charger["operator"] == "ESB eCars"
    assert charger["num_chargers"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_chargers.py -v
```

Expected: FAIL — `ImportError` or `404` because `chargers.py` doesn't exist yet.

- [ ] **Step 3: Create `backend/routers/chargers.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/chargers")
async def get_chargers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(
        "SELECT id, lat, lon, address, operator, num_chargers, source_area, open_hours "
        "FROM ev_chargers"
    ))
    rows = result.mappings().all()
    return [dict(row) for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_chargers.py -v
```

Expected:
```
PASSED backend/tests/test_chargers.py::test_get_chargers_status_200
PASSED backend/tests/test_chargers.py::test_get_chargers_returns_list
PASSED backend/tests/test_chargers.py::test_get_chargers_fields
```

- [ ] **Step 5: Commit**

```bash
git add backend/routers/chargers.py backend/tests/test_chargers.py
git commit -m "feat: add GET /api/chargers endpoint with tests"
```

---

## Task 6: Energy endpoint (TDD)

**Files:**
- Create: `backend/routers/energy.py`
- Create: `backend/tests/test_energy.py`

- [ ] **Step 1: Write the failing test — create `backend/tests/test_energy.py`**

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

SAMPLE_ENERGY = {
    "datetime": "2026-04-30T23:45:00+00:00",
    "wind_mw": 1823.4,
    "solar_mw": 0.0,
    "total_demand_mw": 3241.0,
    "renewable_score": 0.563,
}


class _MockResult:
    def mappings(self):
        return self

    def first(self):
        return SAMPLE_ENERGY


class _MockSession:
    async def execute(self, query):
        return _MockResult()


async def _mock_get_db():
    yield _MockSession()


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = _mock_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_energy_latest_status_200():
    response = client.get("/api/energy/latest")
    assert response.status_code == 200


def test_get_energy_latest_fields():
    response = client.get("/api/energy/latest")
    data = response.json()
    assert "wind_mw" in data
    assert "solar_mw" in data
    assert "renewable_score" in data
    assert "datetime" in data


def test_get_energy_latest_values():
    response = client.get("/api/energy/latest")
    data = response.json()
    assert data["wind_mw"] == 1823.4
    assert data["renewable_score"] == 0.563
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_energy.py -v
```

Expected: FAIL — `404` or `ImportError` because `energy.py` doesn't exist yet.

- [ ] **Step 3: Create `backend/routers/energy.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/energy/latest")
async def get_latest_energy(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(
        "SELECT datetime, wind_mw, solar_mw, total_demand_mw, renewable_score "
        "FROM renewable_energy "
        "ORDER BY datetime DESC "
        "LIMIT 1"
    ))
    row = result.mappings().first()
    return dict(row)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_energy.py -v
```

Expected:
```
PASSED backend/tests/test_energy.py::test_get_energy_latest_status_200
PASSED backend/tests/test_energy.py::test_get_energy_latest_fields
PASSED backend/tests/test_energy.py::test_get_energy_latest_values
```

- [ ] **Step 5: Run the full test suite to confirm nothing broke**

```bash
pytest backend/tests/ -v
```

Expected: all 6 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/energy.py backend/tests/test_energy.py
git commit -m "feat: add GET /api/energy/latest endpoint with tests"
```

---

## Task 7: Ingest EV charger data

**Files:**
- Create: `backend/ingest/load_chargers.py`

- [ ] **Step 1: Create `backend/ingest/load_chargers.py`**

```python
"""
One-off script: loads dublin_ev_chargers.geojson into the ev_chargers table.
Run from the repo root: python -m backend.ingest.load_chargers
Safe to re-run — uses ON CONFLICT DO NOTHING.
"""
import json
import psycopg2
from pathlib import Path

GEOJSON_PATH = Path("data-pipeline/output/dublin_ev_chargers.geojson")
DB_DSN = "dbname=ecocharge"

INSERT_SQL = """
    INSERT INTO ev_chargers (id, lat, lon, address, operator, num_chargers, source_area, open_hours, geom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    ON CONFLICT (id) DO NOTHING
"""

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

with open(GEOJSON_PATH) as f:
    data = json.load(f)

loaded = 0
for feature in data["features"]:
    p = feature["properties"]
    cur.execute(INSERT_SQL, (
        p["id"], p["lat"], p["lon"],
        p.get("address"), p.get("operator"), p.get("num_chargers"),
        p.get("source_area"), p.get("open_hours"),
        p["lon"], p["lat"],  # ST_MakePoint takes (lon, lat)
    ))
    loaded += 1

conn.commit()
cur.close()
conn.close()
print(f"Loaded {loaded} EV charger records into ev_chargers.")
```

- [ ] **Step 2: Run the script**

```bash
python -m backend.ingest.load_chargers
```

Expected output:
```
Loaded 133 EV charger records into ev_chargers.
```

- [ ] **Step 3: Verify the data is in the database**

```bash
psql -d ecocharge -c "SELECT COUNT(*) FROM ev_chargers;"
```

Expected: `133`

```bash
psql -d ecocharge -c "SELECT id, address, operator FROM ev_chargers LIMIT 3;"
```

Expected: three rows with real data (e.g. `esb_0`, `esb_1`, `esb_2`).

- [ ] **Step 4: Commit**

```bash
git add backend/ingest/load_chargers.py
git commit -m "feat: add EV charger ingestion script"
```

---

## Task 8: Ingest renewable energy data

**Files:**
- Create: `backend/ingest/load_energy.py`

- [ ] **Step 1: Create `backend/ingest/load_energy.py`**

```python
"""
One-off script: loads eirgrid_renewable_2026.csv into the renewable_energy table.
Run from the repo root: python -m backend.ingest.load_energy
Truncates the table before inserting — safe to re-run.
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

CSV_PATH = Path("data-pipeline/output/eirgrid_renewable_2026.csv")
DB_DSN = "dbname=ecocharge"

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

df = pd.read_csv(CSV_PATH)
df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

cur.execute("TRUNCATE TABLE renewable_energy")

rows = [
    (
        row["datetime"],
        row["wind_mw"],
        row["solar_mw"],
        row["total_demand_mw"],
        row["wind_penetration"],
        row["solar_penetration"],
        row["renewable_score"],
    )
    for _, row in df.iterrows()
]

execute_values(cur, """
    INSERT INTO renewable_energy
        (datetime, wind_mw, solar_mw, total_demand_mw, wind_penetration, solar_penetration, renewable_score)
    VALUES %s
""", rows)

conn.commit()
cur.close()
conn.close()
print(f"Loaded {len(rows)} energy records into renewable_energy.")
```

- [ ] **Step 2: Run the script**

```bash
python -m backend.ingest.load_energy
```

Expected output:
```
Loaded 11516 energy records into renewable_energy.
```

- [ ] **Step 3: Verify the data**

```bash
psql -d ecocharge -c "SELECT COUNT(*) FROM renewable_energy;"
```

Expected: `11516`

```bash
psql -d ecocharge -c "SELECT datetime, wind_mw, renewable_score FROM renewable_energy ORDER BY datetime DESC LIMIT 3;"
```

Expected: three rows with timestamps and numeric values.

- [ ] **Step 4: Commit**

```bash
git add backend/ingest/load_energy.py
git commit -m "feat: add EirGrid energy ingestion script"
```

---

## Task 9: Start the server and verify end-to-end

No new files — this verifies everything works together against the real database.

- [ ] **Step 1: Start the API server**

```bash
uvicorn backend.main:app --reload
```

Expected output includes:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

- [ ] **Step 2: Test the chargers endpoint**

In a new terminal:
```bash
curl http://127.0.0.1:8000/api/chargers | python -m json.tool | head -30
```

Expected: a JSON array starting with entries like `{"id": "esb_0", "lat": 53.611523, ...}`

- [ ] **Step 3: Test the energy endpoint**

```bash
curl http://127.0.0.1:8000/api/energy/latest | python -m json.tool
```

Expected: a JSON object like:
```json
{
  "datetime": "2026-04-30T23:45:00+00:00",
  "wind_mw": ...,
  "solar_mw": ...,
  "total_demand_mw": ...,
  "renewable_score": ...
}
```

- [ ] **Step 4: Check the auto-generated API docs**

Open in browser: `http://127.0.0.1:8000/docs`

Expected: Swagger UI showing both endpoints — `GET /api/chargers` and `GET /api/energy/latest`.

The backend is now ready for the frontend to connect to.
