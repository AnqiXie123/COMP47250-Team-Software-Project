-- schema_local.sql
-- EcoCharge Dublin — Local Development Schema (no TimescaleDB)
--
-- Decision: TimescaleDB is intentionally omitted from this file.
-- Rationale: The project risk register (Preliminary Project Plan, Section 9)
--   documents an explicit fallback: "Fall back to PostgreSQL + PostGIS if
--   TimescaleDB blocks Sprint 2." TimescaleDB is an optimisation for
--   time-series queries only; it adds no new functionality.
-- Plan: TimescaleDB will be added in Sprint 4 via Docker Compose, where it
--   can be installed as a Docker image without manual local setup.
--   Use data-pipeline/schema.sql (with TimescaleDB) for Docker deployment.
--
-- Usage:
--   psql -d ecocharge -f backend/schema_local.sql

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
