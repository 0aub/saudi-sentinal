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
import rasterio
from minio import Minio
from minio.error import S3Error


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
        self.endpoint = endpoint or os.environ["MINIO_ENDPOINT"]
        self.access_key = access_key or os.environ["MINIO_ACCESS_KEY"]
        self.secret_key = secret_key or os.environ["MINIO_SECRET_KEY"]

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure,
        )

        # Ensure the chips bucket exists
        if not self.client.bucket_exists(CHIPS_BUCKET):
            self.client.make_bucket(CHIPS_BUCKET)

    def _minio_key(self, chip_id: str) -> str:
        """Return the MinIO object key for a given chip_id."""
        return f"{chip_id}.tif"

    def store_chip(self, chip_id: str, data: np.ndarray, metadata: dict | None = None) -> str:
        """
        Serialize chip array to GeoTIFF bytes and upload to MinIO.

        Args:
            chip_id:  Canonical chip ID (used as object key in MinIO).
                      Example: "s2/riyadh-metro/2024/03/15/chip_0024_0031"
            data:     Float32 array of shape (C, H, W).
            metadata: Optional dict of tags (aoi_id, sensor, acquisition_date, etc.)
                      May contain 'transform' and 'crs' keys for georeferencing.

        Returns:
            MinIO object key (chip_id + ".tif")

        Implementation notes:
        - Serialize with rasterio in-memory (io.BytesIO) to avoid temp files
        - Use LZW compression for ~4x size reduction
        - Set content-type: "image/tiff"
        """
        metadata = metadata or {}
        bands, height, width = data.shape
        transform = metadata.get("transform", rasterio.transform.from_bounds(0, 0, width, height, width, height))
        crs = metadata.get("crs", "EPSG:4326")

        # Write GeoTIFF to in-memory buffer
        buf = io.BytesIO()
        with rasterio.MemoryFile(buf) as memfile:
            with memfile.open(
                driver="GTiff",
                height=height,
                width=width,
                count=bands,
                dtype="float32",
                crs=crs,
                transform=transform,
                compress="lzw",
                nodata=np.nan,
            ) as dst:
                dst.write(data.astype(np.float32))

        buf.seek(0)
        minio_key = self._minio_key(chip_id)
        data_bytes = buf.getvalue()

        self.client.put_object(
            CHIPS_BUCKET,
            minio_key,
            io.BytesIO(data_bytes),
            length=len(data_bytes),
            content_type="image/tiff",
        )

        return minio_key

    def load_chip(self, chip_id: str) -> np.ndarray:
        """
        Download a chip from MinIO and deserialize to numpy array.

        Args:
            chip_id: Canonical chip ID (without .tif extension).

        Returns:
            Float32 array of shape (C, H, W).

        Raises:
            KeyError if chip_id not found in MinIO.
        """
        minio_key = self._minio_key(chip_id)
        try:
            response = self.client.get_object(CHIPS_BUCKET, minio_key)
            data_bytes = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise KeyError(f"Chip not found in MinIO: {minio_key}") from e
            raise

        with rasterio.MemoryFile(data_bytes) as memfile:
            with memfile.open() as src:
                array = src.read().astype(np.float32)

        return array

    def chip_exists(self, chip_id: str) -> bool:
        """Check if a chip is already stored (for idempotent ingestion)."""
        minio_key = self._minio_key(chip_id)
        try:
            self.client.stat_object(CHIPS_BUCKET, minio_key)
            return True
        except S3Error:
            return False

    def delete_chip(self, chip_id: str) -> None:
        """Remove a chip from storage (e.g. when quality_flag = 'corrupt')."""
        minio_key = self._minio_key(chip_id)
        self.client.remove_object(CHIPS_BUCKET, minio_key)
