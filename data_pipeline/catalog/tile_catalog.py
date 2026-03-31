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

from datetime import date
from typing import List


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
        raise NotImplementedError(
            "Create SQLAlchemy engine + session factory. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md — PostGIS schema."
        )

    def register_chip(self, chip) -> None:
        """
        Insert chip metadata into the chips table.

        Idempotent: skip if chip_id already exists (ON CONFLICT DO NOTHING).
        Also updates the minio_key if the chip was previously partially processed.
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def get_aoi(self, aoi_id: str) -> dict:
        """
        Return AOI record including geometry as GeoJSON.

        Raises:
            KeyError if aoi_id not found.
        """
        raise NotImplementedError

    def list_aois(self) -> List[dict]:
        """Return all registered AOIs."""
        raise NotImplementedError

    def register_aoi(self, aoi_id: str, name: str, geometry: dict, projects: List[str]) -> None:
        """Insert or update an AOI record. Used by seed_aois.py."""
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError
