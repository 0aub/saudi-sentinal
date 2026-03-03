# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Naming Convention" section
"""
MinIO-backed storage interface for chip array data.

Chips are stored as GeoTIFF files in MinIO under the bucket "sentinel-chips".

Key structure:
    {sensor}/{aoi}/{year}/{month}/{day}/{chip_id}.tif

Environment variables required:
  MINIO_ENDPOINT    — e.g. "localhost:9000" or "minio:9000" (no http://)
  MINIO_ACCESS_KEY  — MinIO root user (same as MINIO_USER in .env)
  MINIO_SECRET_KEY  — MinIO root password (same as MINIO_PASSWORD in .env)

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Naming Convention"
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import numpy as np


CHIPS_BUCKET = "sentinel-chips"


class TileStore:
    """
    MinIO-backed storage for satellite chip arrays.

    Implementation guide: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Naming Convention"
    Uses the minio-py SDK (minio>=7.2).
    """

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
    ) -> None:
        """
        Initialize MinIO client and ensure chips bucket exists.

        Args:
            endpoint:   MinIO host:port (no scheme). Falls back to MINIO_ENDPOINT.
            access_key: Falls back to MINIO_ACCESS_KEY env var.
            secret_key: Falls back to MINIO_SECRET_KEY env var.
            secure:     Use TLS. False for local dev, True for production.
        """
        raise NotImplementedError(
            "Instantiate minio.Minio client. "
            "Create CHIPS_BUCKET if it doesn't exist. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def store_chip(self, chip_id: str, data: np.ndarray, metadata: dict | None = None) -> str:
        """
        Serialize chip array to GeoTIFF bytes and upload to MinIO.

        Args:
            chip_id:  Canonical chip ID (used as object key in MinIO).
                      Example: "s2/riyadh-metro/2024/03/15/chip_0024_0031"
            data:     Float32 array of shape (C, 256, 256).
            metadata: Optional dict of tags (aoi_id, sensor, acquisition_date, etc.)

        Returns:
            MinIO object key (chip_id + ".tif")

        Implementation notes:
        - Serialize with rasterio in-memory (io.BytesIO) to avoid temp files
        - Use LZW compression for ~4× size reduction
        - Set content-type: "image/tiff"
        """
        raise NotImplementedError(
            "Serialize array to GeoTIFF BytesIO, upload via minio.put_object. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def load_chip(self, chip_id: str) -> np.ndarray:
        """
        Download a chip from MinIO and deserialize to numpy array.

        Args:
            chip_id: Canonical chip ID (without .tif extension).

        Returns:
            Float32 array of shape (C, 256, 256).

        Raises:
            KeyError if chip_id not found in MinIO.
        """
        raise NotImplementedError(
            "Use minio.get_object, read bytes, deserialize with rasterio. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def chip_exists(self, chip_id: str) -> bool:
        """Check if a chip is already stored (for idempotent ingestion)."""
        raise NotImplementedError

    def delete_chip(self, chip_id: str) -> None:
        """Remove a chip from storage (e.g. when quality_flag = 'corrupt')."""
        raise NotImplementedError
