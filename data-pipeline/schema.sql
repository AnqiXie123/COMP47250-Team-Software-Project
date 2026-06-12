-- =============================================================================
-- schema.sql
-- EcoCharge Dublin — Database Schema
-- ==================================
-- This file defines all tables required for the EcoCharge Dublin pipeline.
-- Run this file once to initialise the database before ingesting any data.
--
-- Database: PostgreSQL with PostGIS extension (spatial queries)
--           and TimescaleDB extension (time-series optimisation)
--
-- Usage:
--   psql -U postgres -d ecocharge -f schema.sql
-- =============================================================================


-- Enable required extensions
-- PostGIS adds spatial data types (GEOMETRY) and functions (ST_Distance etc.)
-- TimescaleDB optimises storage and queries for time-series tables
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;


-- =============================================================================
-- TABLE: ev_chargers
-- Source: ESB eCars (primary), DLR GeoJSON, SDCC CSV
-- Script: data-pipeline/01_clean_ev_chargers.py
-- =============================================================================
-- Stores the location and attributes of all known public EV charging stations
-- in the Dublin area. This is a static reference table, does not change
-- frequently and is not a time-series table.

CREATE TABLE IF NOT EXISTS ev_chargers (
    id              VARCHAR(50)     PRIMARY KEY,
                    -- Unique identifier, prefixed by source:
                    -- 'esb_0', 'dlr_0', 'sdcc_0' etc.

    lat             DOUBLE PRECISION NOT NULL,
                    -- Latitude in WGS84 (EPSG:4326)

    lon             DOUBLE PRECISION NOT NULL,
                    -- Longitude in WGS84 (EPSG:4326)

    address         TEXT,
                    -- Human-readable address or location name

    operator        VARCHAR(100),
                    -- Charging network operator (e.g. 'ESB eCars', 'EasyGo')

    num_chargers    INTEGER,
                    -- Number of individual charge points at this station

    source_area     VARCHAR(50),
                    -- Which dataset this record came from:
                    -- 'ESB_national', 'DLR', 'SDCC'

    open_hours      VARCHAR(100),
                    -- Opening hours string (e.g. '24 x 7', 'Unknown')

    geom            GEOMETRY(Point, 4326)
                    -- PostGIS geometry column — enables spatial queries
                    -- such as ST_Distance, ST_Within, ST_DWithin
                    -- Populated from lat/lon during ingestion
);

-- Spatial index on geom — speeds up proximity queries
-- (e.g. "find all chargers within 500m of this grid point")
CREATE INDEX IF NOT EXISTS idx_ev_chargers_geom
    ON ev_chargers USING GIST (geom);


-- =============================================================================
-- TABLE: renewable_energy
-- Source: EirGrid Smart Grid Dashboard
-- Script: data-pipeline/02_clean_energy_data.py
-- =============================================================================
-- Stores 15-minute interval renewable energy generation data for Ireland.
-- This is the primary time-series table — converted to a TimescaleDB
-- hypertable for efficient time-range queries.

CREATE TABLE IF NOT EXISTS renewable_energy (
    datetime            TIMESTAMPTZ     NOT NULL,
                        -- Timestamp of the 15-minute interval (UTC)

    wind_mw             DOUBLE PRECISION,
                        -- Actual wind generation in Ireland (MW)

    solar_mw            DOUBLE PRECISION,
                        -- Actual solar generation in Ireland (MW)

    total_demand_mw     DOUBLE PRECISION,
                        -- Total system demand in Ireland (MW)

    wind_penetration    DOUBLE PRECISION,
                        -- Wind as a fraction of total demand (0–1)

    solar_penetration   DOUBLE PRECISION,
                        -- Solar as a fraction of total demand (0–1)

    renewable_score     DOUBLE PRECISION
                        -- Derived field: (wind_mw + solar_mw) / total_demand_mw
                        -- Represents overall grid greenness (0–1)
                        -- Used as the 'renewable_score' feature in ML dataset
);

-- Convert to TimescaleDB hypertable, partitioned by datetime
-- This dramatically speeds up time-range queries on large datasets
SELECT create_hypertable(
    'renewable_energy', 'datetime',
    if_not_exists => TRUE
);

-- Index on datetime for fast lookups by time window
CREATE INDEX IF NOT EXISTS idx_renewable_energy_datetime
    ON renewable_energy (datetime DESC);


-- =============================================================================
-- TABLE: traffic_volumes
-- Source: Smart Dublin SCATS (DLR 2023, DCC 2025)
-- Script: data-pipeline/03_clean_traffic_data.py  (Phase 3)
-- =============================================================================
-- Stores hourly vehicle count data from SCATS traffic sensors across Dublin.
-- Each row represents one detector at one site for one hour.
-- Also a time-series table — converted to a TimescaleDB hypertable.

CREATE TABLE IF NOT EXISTS traffic_volumes (
    datetime        TIMESTAMPTZ     NOT NULL,
                    -- End time of the one-hour counting period (UTC)

    site_id         VARCHAR(20)     NOT NULL,
                    -- SCATS site identifier (e.g. '6000', 'N01111A')

    detector        INTEGER,
                    -- Detector number within the site (sensors per lane)

    region          VARCHAR(50),
                    -- Area label (e.g. 'NCITY', 'SCITY', 'DLR')

    sum_volume      INTEGER,
                    -- Total vehicle count in the preceding hour

    avg_volume      DOUBLE PRECISION,
                    -- Average vehicle count per 5-minute interval

    lat             DOUBLE PRECISION,
                    -- Latitude of the SCATS site (joined from location file)

    lon             DOUBLE PRECISION,
                    -- Longitude of the SCATS site

    geom            GEOMETRY(Point, 4326)
                    -- PostGIS geometry — populated from lat/lon
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'traffic_volumes', 'datetime',
    if_not_exists => TRUE
);

-- Composite index: common query pattern is site + time window
CREATE INDEX IF NOT EXISTS idx_traffic_volumes_site_time
    ON traffic_volumes (site_id, datetime DESC);

-- Spatial index for proximity queries
CREATE INDEX IF NOT EXISTS idx_traffic_volumes_geom
    ON traffic_volumes USING GIST (geom);

-- =============================================================================
-- TABLE: recommended_locations
-- Source: ML pipeline (K-Means clustering)
-- Script: ml-engine/kmeans_clustering.py (ML)
-- =============================================================================
-- Stores AI-recommended new EV charging station locations produced by the
-- K-Means clustering algorithm. Each row is one recommended site, ranked
-- by priority score derived from supply-demand gap analysis.

CREATE TABLE IF NOT EXISTS recommended_locations (
    id                  SERIAL          PRIMARY KEY,
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    cluster_id          INTEGER,
    avg_gap_score       DOUBLE PRECISION,
                        -- Mean supply-demand gap score for this cluster;
                        -- higher = higher priority for new charger
    avg_traffic         DOUBLE PRECISION,
                        -- Mean hourly traffic volume in this cluster
    avg_chargers        DOUBLE PRECISION,
                        -- Mean existing charger count nearby in this cluster
    site_count          INTEGER,
                        -- Number of SCATS sites in this cluster
    rank                INTEGER,
                        -- Priority rank (1 = highest priority)
    geom                GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_recommended_locations_geom
    ON recommended_locations USING GIST (geom);
