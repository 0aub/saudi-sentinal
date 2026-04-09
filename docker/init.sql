-- Auto-run by PostgreSQL on first container boot (via docker-entrypoint-initdb.d).
-- Enables PostGIS extensions and creates the sentinel_catalog schema.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

CREATE TABLE aois (
    aoi_id      VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(256),
    geometry    GEOMETRY(Polygon, 4326),
    projects    TEXT[],
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chips (
    chip_id         VARCHAR(256) PRIMARY KEY,
    aoi_id          VARCHAR(64) REFERENCES aois(aoi_id),
    sensor          VARCHAR(10),
    acquisition_date DATE,
    cloud_pct       FLOAT,
    geometry        GEOMETRY(Polygon, 4326),
    minio_key       VARCHAR(512),
    bands           TEXT[],
    chip_size_px    INTEGER,
    resolution_m    FLOAT,
    processed_at    TIMESTAMP DEFAULT NOW(),
    quality_flag    VARCHAR(20) DEFAULT 'valid'
);

CREATE INDEX idx_chips_aoi_date ON chips(aoi_id, acquisition_date);
CREATE INDEX idx_chips_sensor ON chips(sensor);
CREATE INDEX idx_chips_geom ON chips USING GIST(geometry);

CREATE TABLE ingestion_runs (
    run_id      SERIAL PRIMARY KEY,
    aoi_id      VARCHAR(64),
    sensor      VARCHAR(10),
    date_from   DATE,
    date_to     DATE,
    chips_added INTEGER,
    status      VARCHAR(20),
    error_msg   TEXT,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP
);
