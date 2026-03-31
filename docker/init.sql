-- Auto-run by PostgreSQL on first container boot (via docker-entrypoint-initdb.d).
-- Enables PostGIS extensions in the sentinel_catalog database.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
