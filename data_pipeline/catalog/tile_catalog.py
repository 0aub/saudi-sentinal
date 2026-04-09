# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "PostGIS Catalog Schema" section
"""
PostGIS-backed catalog for all processed satellite chips.

Database schema (see full SQL in docs/plans/LEVEL-0-DATA-PIPELINE.md):
  - aois:            Area of interest definitions with geometry
  - chips:           Metadata for every processed chip (sensor, date, cloud%, geometry, MinIO key)
  - ingestion_runs:  Audit log of each ingestion run

Environment variables required:
  DATABASE_URL  — PostgreSQL connection string, e.g.:
                  postgresql://sentinel:<password>@localhost:5432/sentinel_catalog
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import List

from sqlalchemy import create_engine, text


class ChipMeta:
    """Lightweight metadata container for a chip (no array data)."""
    chip_id: str
    aoi_id: str
    sensor: str
    acquisition_date: date
    cloud_pct: float | None
    geometry: dict    # GeoJSON polygon
    minio_key: str
    bands: List[str]
    chip_size_px: int
    resolution_m: float
    quality_flag: str  # "valid" | "cloudy" | "partial" | "corrupt"

    def __init__(
        self,
        chip_id: str,
        aoi_id: str,
        sensor: str,
        acquisition_date: date,
        cloud_pct: float | None,
        geometry: dict,
        minio_key: str,
        bands: List[str],
        chip_size_px: int,
        resolution_m: float,
        quality_flag: str = "valid",
    ) -> None:
        self.chip_id = chip_id
        self.aoi_id = aoi_id
        self.sensor = sensor
        self.acquisition_date = acquisition_date
        self.cloud_pct = cloud_pct
        self.geometry = geometry
        self.minio_key = minio_key
        self.bands = bands
        self.chip_size_px = chip_size_px
        self.resolution_m = resolution_m
        self.quality_flag = quality_flag


_INIT_SQL = """
CREATE TABLE IF NOT EXISTS aois (
    aoi_id      VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(256),
    geometry    GEOMETRY(Polygon, 4326),
    projects    TEXT[],
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chips (
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

CREATE INDEX IF NOT EXISTS idx_chips_aoi_date ON chips(aoi_id, acquisition_date);
CREATE INDEX IF NOT EXISTS idx_chips_sensor ON chips(sensor);
CREATE INDEX IF NOT EXISTS idx_chips_geom ON chips USING GIST(geometry);

CREATE TABLE IF NOT EXISTS ingestion_runs (
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
"""


class TileCatalog:
    """
    PostGIS-backed catalog interface for chip metadata.

    Implementation guide: docs/plans/LEVEL-0-DATA-PIPELINE.md — "PostGIS Catalog Schema"

    Uses SQLAlchemy + GeoAlchemy2 for ORM mapping to PostGIS tables.
    Connection pool is shared across the service lifetime.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy-style PostgreSQL URL.
                          Falls back to DATABASE_URL env var.
        """
        url = database_url or os.environ["DATABASE_URL"]
        self.engine = create_engine(url, pool_pre_ping=True)
        with self.engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology;"))
            for statement in _INIT_SQL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))

    def register_aoi(self, aoi_id: str, name: str, geometry: dict, projects: List[str]) -> None:
        """Insert or update an AOI record. Used by seed_aois.py."""
        geojson_str = json.dumps(geometry) if isinstance(geometry, dict) else geometry
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO aois (aoi_id, name, geometry, projects)
                    VALUES (:aoi_id, :name, ST_GeomFromGeoJSON(:geometry), :projects)
                    ON CONFLICT (aoi_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        geometry = EXCLUDED.geometry,
                        projects = EXCLUDED.projects
                    """
                ),
                {
                    "aoi_id": aoi_id,
                    "name": name,
                    "geometry": geojson_str,
                    "projects": projects,
                },
            )

    def get_aoi(self, aoi_id: str) -> dict:
        """
        Return AOI record including geometry as GeoJSON.

        Raises:
            KeyError if aoi_id not found.
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT aoi_id, name, ST_AsGeoJSON(geometry)::json AS geometry,
                           projects, created_at
                    FROM aois
                    WHERE aoi_id = :aoi_id
                    """
                ),
                {"aoi_id": aoi_id},
            )
            row = result.mappings().fetchone()
            if row is None:
                raise KeyError(f"AOI not found: {aoi_id}")
            return dict(row)

    def list_aois(self) -> List[dict]:
        """Return all registered AOIs."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT aoi_id, name, ST_AsGeoJSON(geometry)::json AS geometry,
                           projects, created_at
                    FROM aois
                    ORDER BY created_at
                    """
                )
            )
            return [dict(row) for row in result.mappings().fetchall()]

    def register_chip(self, chip: ChipMeta) -> None:
        """
        Insert chip metadata into the chips table.

        Idempotent: skip if chip_id already exists (ON CONFLICT DO NOTHING).
        Also updates the minio_key if the chip was previously partially processed.
        """
        geojson_str = json.dumps(chip.geometry) if isinstance(chip.geometry, dict) else chip.geometry
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO chips (
                        chip_id, aoi_id, sensor, acquisition_date, cloud_pct,
                        geometry, minio_key, bands, chip_size_px, resolution_m, quality_flag
                    ) VALUES (
                        :chip_id, :aoi_id, :sensor, :acquisition_date, :cloud_pct,
                        ST_GeomFromGeoJSON(:geometry), :minio_key, :bands,
                        :chip_size_px, :resolution_m, :quality_flag
                    )
                    ON CONFLICT (chip_id) DO NOTHING
                    """
                ),
                {
                    "chip_id": chip.chip_id,
                    "aoi_id": chip.aoi_id,
                    "sensor": chip.sensor,
                    "acquisition_date": chip.acquisition_date,
                    "cloud_pct": chip.cloud_pct,
                    "geometry": geojson_str,
                    "minio_key": chip.minio_key,
                    "bands": chip.bands,
                    "chip_size_px": chip.chip_size_px,
                    "resolution_m": chip.resolution_m,
                    "quality_flag": chip.quality_flag,
                },
            )

    def query_chips(
        self,
        aoi_id: str,
        date_range: tuple,
        sensor: str,
        max_cloud: float = 20.0,
    ) -> List[ChipMeta]:
        """
        Query chips matching the given filters.

        Args:
            aoi_id:      AOI identifier (e.g. "riyadh-metro")
            date_range:  Tuple of (start_date, end_date)
            sensor:      "s1" or "s2"
            max_cloud:   Maximum cloud percentage (ignored for S1)

        Returns:
            List of ChipMeta objects sorted by acquisition_date ascending.
        """
        start_date, end_date = date_range

        # For SAR (s1), cloud percentage is not relevant
        if sensor.lower() == "s1":
            query = text(
                """
                SELECT chip_id, aoi_id, sensor, acquisition_date, cloud_pct,
                       ST_AsGeoJSON(geometry)::json AS geometry, minio_key,
                       bands, chip_size_px, resolution_m, quality_flag
                FROM chips
                WHERE aoi_id = :aoi_id
                  AND sensor = :sensor
                  AND acquisition_date >= :start_date
                  AND acquisition_date <= :end_date
                ORDER BY acquisition_date ASC
                """
            )
            params = {
                "aoi_id": aoi_id,
                "sensor": sensor,
                "start_date": start_date,
                "end_date": end_date,
            }
        else:
            query = text(
                """
                SELECT chip_id, aoi_id, sensor, acquisition_date, cloud_pct,
                       ST_AsGeoJSON(geometry)::json AS geometry, minio_key,
                       bands, chip_size_px, resolution_m, quality_flag
                FROM chips
                WHERE aoi_id = :aoi_id
                  AND sensor = :sensor
                  AND acquisition_date >= :start_date
                  AND acquisition_date <= :end_date
                  AND (cloud_pct IS NULL OR cloud_pct <= :max_cloud)
                ORDER BY acquisition_date ASC
                """
            )
            params = {
                "aoi_id": aoi_id,
                "sensor": sensor,
                "start_date": start_date,
                "end_date": end_date,
                "max_cloud": max_cloud,
            }

        with self.engine.connect() as conn:
            result = conn.execute(query, params)
            chips = []
            for row in result.mappings().fetchall():
                chips.append(
                    ChipMeta(
                        chip_id=row["chip_id"],
                        aoi_id=row["aoi_id"],
                        sensor=row["sensor"],
                        acquisition_date=row["acquisition_date"],
                        cloud_pct=row["cloud_pct"],
                        geometry=row["geometry"],
                        minio_key=row["minio_key"],
                        bands=list(row["bands"]) if row["bands"] else [],
                        chip_size_px=row["chip_size_px"],
                        resolution_m=row["resolution_m"],
                        quality_flag=row["quality_flag"],
                    )
                )
            return chips

    def get_timeseries(
        self,
        aoi_id: str,
        sensor: str,
        band: str | None = None,
        aggregation: str = "monthly",
    ) -> List[dict]:
        """
        Return time-ordered chip list for timeseries queries.

        Args:
            aggregation: "monthly" groups chips by month, "all" returns individual scenes.
        """
        if aggregation == "monthly":
            query = text(
                """
                SELECT DATE_TRUNC('month', acquisition_date) AS month,
                       COUNT(*) AS chip_count,
                       AVG(cloud_pct) AS avg_cloud_pct,
                       ARRAY_AGG(chip_id ORDER BY acquisition_date) AS chip_ids
                FROM chips
                WHERE aoi_id = :aoi_id AND sensor = :sensor
                GROUP BY DATE_TRUNC('month', acquisition_date)
                ORDER BY month ASC
                """
            )
        else:
            query = text(
                """
                SELECT chip_id, acquisition_date, cloud_pct, minio_key,
                       bands, quality_flag
                FROM chips
                WHERE aoi_id = :aoi_id AND sensor = :sensor
                ORDER BY acquisition_date ASC
                """
            )

        with self.engine.connect() as conn:
            result = conn.execute(query, {"aoi_id": aoi_id, "sensor": sensor})
            return [dict(row) for row in result.mappings().fetchall()]

    def record_ingestion_run(
        self,
        aoi_id: str,
        sensor: str,
        date_from: date,
        date_to: date,
        chips_added: int,
        status: str,
        error_msg: str | None = None,
    ) -> None:
        """Insert a row into the ingestion_runs audit table."""
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO ingestion_runs
                        (aoi_id, sensor, date_from, date_to, chips_added,
                         status, error_msg, started_at, finished_at)
                    VALUES
                        (:aoi_id, :sensor, :date_from, :date_to, :chips_added,
                         :status, :error_msg, :started_at, NOW())
                    """
                ),
                {
                    "aoi_id": aoi_id,
                    "sensor": sensor,
                    "date_from": date_from,
                    "date_to": date_to,
                    "chips_added": chips_added,
                    "status": status,
                    "error_msg": error_msg,
                    "started_at": datetime.utcnow(),
                },
            )
