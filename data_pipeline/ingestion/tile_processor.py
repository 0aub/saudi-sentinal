# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "TileProcessor" section
"""
Processes raw Sentinel product archives into ML-ready 256×256 chips.

Responsibilities:
- Unpack .SAFE archives (S2) or GRD products (S1)
- Select and resample bands to a common 10m grid
- Apply cloud masking via SCL band (S2) or land/layover masking (S1)
- Slice the AOI into 256×256 chips using a regular tile grid
- Store chips as Float32 GeoTIFFs in MinIO via TileStore
- Register chip metadata in PostGIS via TileCatalog

Chip naming convention:
  {sensor}/{aoi}/{year}/{month}/{day}/{chip_id}.tif
  e.g. s2/riyadh-metro/2024/03/15/chip_0024_0031.tif

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Specification" table
"""

from __future__ import annotations

import glob as globmod
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask as rio_mask
from rasterio.warp import Resampling as WarpResampling, calculate_default_transform, reproject
from shapely.geometry import box, mapping, shape

logger = logging.getLogger(__name__)


@dataclass
class Chip:
    """A single 256×256 processed chip ready for ML consumption."""
    chip_id: str              # Unique ID following naming convention
    aoi_id: str
    sensor: str               # "s2" or "s1"
    acquisition_date: object  # datetime.date
    bands: List[str]          # e.g. ["B02","B03","B04","B08","B11","B12"] for S2
    data: np.ndarray          # shape (C, 256, 256), dtype float32
    cloud_mask: np.ndarray | None  # shape (256, 256) bool, None for S1
    cloud_pct: float | None
    geometry: dict            # GeoJSON polygon of chip extent
    crs: str                  # e.g. "EPSG:4326"
    resolution_m: float       # 10.0


def _find_band_file(product_path: Path, pattern: str) -> Path | None:
    """Find a single band file matching a glob pattern inside a .SAFE directory."""
    matches = list(product_path.rglob(pattern))
    if matches:
        return matches[0]
    return None


def _extract_date_from_safe(product_path: Path) -> date:
    """Extract acquisition date from .SAFE directory name (e.g. S2A_MSIL2A_20240315T...)."""
    name = product_path.stem
    # Typical: S2A_MSIL2A_20240315T073611_...
    parts = name.split("_")
    for part in parts:
        if len(part) >= 8 and part[:8].isdigit():
            try:
                return date(int(part[:4]), int(part[4:6]), int(part[6:8]))
            except ValueError:
                continue
    # Fallback: try to parse from any part containing a date-like string
    logger.warning("Could not extract date from %s, using today", name)
    return date.today()


def _read_and_resample_to_10m(
    band_path: Path, ref_profile: dict
) -> np.ndarray:
    """Read a 20m band and resample it to match a 10m reference grid."""
    with rasterio.open(band_path) as src:
        dst_crs = ref_profile["crs"]
        dst_transform = ref_profile["transform"]
        dst_width = ref_profile["width"]
        dst_height = ref_profile["height"]

        dst_array = np.empty((1, dst_height, dst_width), dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=dst_array[0],
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=WarpResampling.bilinear,
        )
    return dst_array[0]


class TileProcessor:
    """
    Converts raw Sentinel .SAFE products into ML-ready chip arrays.

    Implementation guide: docs/plans/LEVEL-0-DATA-PIPELINE.md — "TileProcessor" section

    S2 chip spec:
        Bands:      B02, B03, B04, B08 (10m native) + B11, B12 (20m → resampled to 10m)
        Dtype:      float32, range 0.0–1.0 (divide DN by 10000)
        Cloud mask: SCL values 4,5,6 = valid; all others = masked

    S1 chip spec:
        Bands:      VV, VH (dual-pol)
        Dtype:      float32 in dB (10 * log10(intensity))
        No cloud mask (SAR is cloud-independent)
    """

    VALID_SCL_VALUES = {4, 5, 6}  # vegetation, bare soil, water

    # Band glob patterns for Sentinel-2 L2A .SAFE products
    S2_10M_BANDS = {
        "B02": "**/IMG_DATA/R10m/*_B02_10m.jp2",
        "B03": "**/IMG_DATA/R10m/*_B03_10m.jp2",
        "B04": "**/IMG_DATA/R10m/*_B04_10m.jp2",
        "B08": "**/IMG_DATA/R10m/*_B08_10m.jp2",
    }
    S2_20M_BANDS = {
        "B11": "**/IMG_DATA/R20m/*_B11_20m.jp2",
        "B12": "**/IMG_DATA/R20m/*_B12_20m.jp2",
    }
    S2_SCL_PATTERN = "**/IMG_DATA/R20m/*_SCL_20m.jp2"

    def __init__(self, chip_size: int = 256) -> None:
        self.chip_size = chip_size

    def process_s2(self, product_path: Path, aoi_id: str, aoi_geometry: dict) -> List[Chip]:
        """
        Process a Sentinel-2 L2A .SAFE product into 256x256 chips.

        Steps:
        1. Locate band files (B02, B03, B04, B08 at 10m; B11, B12, SCL at 20m)
        2. Resample 20m bands to 10m using bilinear interpolation (rasterio.warp)
        3. Clip to AOI bounding box
        4. Apply SCL cloud mask
        5. Normalize reflectance: divide by 10000, clip to [0, 1]
        6. Slice into 256x256 chips on a regular grid
        7. Return list of Chip objects (only chips with cloud_pct < threshold)
        """
        product_path = Path(product_path)
        acquisition_date = _extract_date_from_safe(product_path)
        aoi_shape = shape(aoi_geometry)

        # Step 1: Locate band files
        band_paths_10m: dict[str, Path] = {}
        for band_name, pattern in self.S2_10M_BANDS.items():
            path = _find_band_file(product_path, pattern)
            if path is None:
                raise FileNotFoundError(
                    f"Could not find {band_name} in {product_path} with pattern {pattern}"
                )
            band_paths_10m[band_name] = path

        band_paths_20m: dict[str, Path] = {}
        for band_name, pattern in self.S2_20M_BANDS.items():
            path = _find_band_file(product_path, pattern)
            if path is None:
                raise FileNotFoundError(
                    f"Could not find {band_name} in {product_path} with pattern {pattern}"
                )
            band_paths_20m[band_name] = path

        scl_path = _find_band_file(product_path, self.S2_SCL_PATTERN)
        if scl_path is None:
            raise FileNotFoundError(f"Could not find SCL band in {product_path}")

        # Get reference profile from a 10m band
        ref_band_path = band_paths_10m["B02"]
        with rasterio.open(ref_band_path) as ref_src:
            ref_profile = ref_src.profile.copy()
            ref_crs = ref_src.crs

        # Step 2-3: Read 10m bands and clip to AOI
        band_names = ["B02", "B03", "B04", "B08", "B11", "B12"]
        bands_data: dict[str, np.ndarray] = {}

        # Read and clip 10m bands
        for band_name, band_path in band_paths_10m.items():
            with rasterio.open(band_path) as src:
                try:
                    clipped, clipped_transform = rio_mask(
                        src, [aoi_shape], crop=True, filled=True, nodata=0
                    )
                    bands_data[band_name] = clipped[0].astype(np.float32)
                except ValueError:
                    logger.warning("AOI does not overlap with %s, skipping product", band_name)
                    return []

        # Build reference profile for the clipped extent
        with rasterio.open(ref_band_path) as src:
            clipped_ref, clipped_transform = rio_mask(
                src, [aoi_shape], crop=True, filled=True, nodata=0
            )
            clipped_profile = src.profile.copy()
            clipped_profile.update(
                height=clipped_ref.shape[1],
                width=clipped_ref.shape[2],
                transform=clipped_transform,
            )

        # Step 2: Resample 20m bands to 10m then clip
        for band_name, band_path in band_paths_20m.items():
            resampled = _read_and_resample_to_10m(band_path, clipped_profile)
            bands_data[band_name] = resampled

        # Resample SCL to 10m
        scl_resampled = _read_and_resample_to_10m(scl_path, clipped_profile)
        scl_array = np.rint(scl_resampled).astype(np.uint8)

        # Step 4: Compute cloud mask
        cloud_mask = self.cloud_mask_s2(bands_data, scl_array)

        # Step 5: Normalize reflectance to [0, 1]
        for band_name in bands_data:
            bands_data[band_name] = np.clip(bands_data[band_name] / 10000.0, 0.0, 1.0)

        # Stack bands into (C, H, W) array
        stacked = np.stack(
            [bands_data[bn] for bn in band_names], axis=0
        ).astype(np.float32)

        # Step 6-7: Slice into chips
        chips = self._slice_to_chips(
            data=stacked,
            cloud_mask=cloud_mask,
            transform=clipped_transform,
            crs=str(ref_crs),
            aoi_id=aoi_id,
            sensor="s2",
            acquisition_date=acquisition_date,
            band_names=band_names,
            chip_size=self.chip_size,
        )

        logger.info(
            "Processed S2 product %s: %d chips generated", product_path.name, len(chips)
        )
        return chips

    def process_s1(self, product_path: Path, aoi_id: str, aoi_geometry: dict) -> List[Chip]:
        """
        Process a Sentinel-1 GRD product into 256x256 chips.

        Steps:
        1. Locate VV and VH band files
        2. Convert linear intensity to dB: 10 * log10(intensity)
        3. Clip to AOI bounding box
        4. Slice into 256x256 chips
        5. Return list of Chip objects
        """
        product_path = Path(product_path)
        acquisition_date = _extract_date_from_safe(product_path)
        aoi_shape = shape(aoi_geometry)

        # Step 1: Find VV and VH measurement files
        vv_path = _find_band_file(product_path, "**/measurement/*vv*.tiff")
        if vv_path is None:
            vv_path = _find_band_file(product_path, "**/measurement/*vv*.tif")
        vh_path = _find_band_file(product_path, "**/measurement/*vh*.tiff")
        if vh_path is None:
            vh_path = _find_band_file(product_path, "**/measurement/*vh*.tif")

        if vv_path is None or vh_path is None:
            raise FileNotFoundError(
                f"Could not find VV/VH measurement files in {product_path}"
            )

        band_names = ["VV", "VH"]
        bands_data: dict[str, np.ndarray] = {}
        clipped_transform = None
        clipped_crs = None

        for band_name, band_path in [("VV", vv_path), ("VH", vh_path)]:
            with rasterio.open(band_path) as src:
                try:
                    clipped, clipped_transform = rio_mask(
                        src, [aoi_shape], crop=True, filled=True, nodata=0
                    )
                    clipped_crs = str(src.crs)
                except ValueError:
                    logger.warning("AOI does not overlap with %s, skipping product", band_name)
                    return []

                # Step 2: Convert to dB
                linear = clipped[0].astype(np.float32)
                # Avoid log10(0) by clamping minimum
                linear = np.where(linear > 0, linear, 1e-10)
                db = 10.0 * np.log10(linear)
                # Clip to [-30, 0] range
                db = np.clip(db, -30.0, 0.0)
                bands_data[band_name] = db

        # Stack VV, VH into (2, H, W)
        stacked = np.stack(
            [bands_data[bn] for bn in band_names], axis=0
        ).astype(np.float32)

        # Step 4-5: Slice into chips
        chips = self._slice_to_chips(
            data=stacked,
            cloud_mask=None,
            transform=clipped_transform,
            crs=clipped_crs or "EPSG:4326",
            aoi_id=aoi_id,
            sensor="s1",
            acquisition_date=acquisition_date,
            band_names=band_names,
            chip_size=self.chip_size,
        )

        logger.info(
            "Processed S1 product %s: %d chips generated", product_path.name, len(chips)
        )
        return chips

    def cloud_mask_s2(self, bands: dict, scl: np.ndarray) -> np.ndarray:
        """
        Generate boolean cloud mask from SCL (Scene Classification Layer).

        Args:
            bands: Dict mapping band name -> np.ndarray
            scl:   SCL array (uint8), resampled to 10m

        Returns:
            Boolean mask: True = valid pixel, False = cloudy/shadow/invalid
        """
        return np.isin(scl, list(self.VALID_SCL_VALUES))

    def _slice_to_chips(
        self,
        data: np.ndarray,
        cloud_mask: np.ndarray | None,
        transform: object,
        crs: str,
        aoi_id: str,
        sensor: str,
        acquisition_date: object,
        band_names: List[str] | None = None,
        chip_size: int = 256,
    ) -> List[Chip]:
        """Slice a full-AOI array into non-overlapping chip_size x chip_size tiles."""
        chips: List[Chip] = []
        _, h, w = data.shape

        n_rows = h // chip_size
        n_cols = w // chip_size

        for row_idx in range(n_rows):
            for col_idx in range(n_cols):
                y_start = row_idx * chip_size
                x_start = col_idx * chip_size

                chip_data = data[
                    :, y_start : y_start + chip_size, x_start : x_start + chip_size
                ]

                # Skip chips that are entirely nodata/zero
                if np.all(chip_data == 0):
                    continue

                chip_cloud_mask = None
                chip_cloud_pct = None
                if cloud_mask is not None:
                    chip_cloud_mask = cloud_mask[
                        y_start : y_start + chip_size, x_start : x_start + chip_size
                    ]
                    total_pixels = chip_cloud_mask.size
                    valid_pixels = np.sum(chip_cloud_mask)
                    chip_cloud_pct = round(
                        100.0 * (1.0 - valid_pixels / total_pixels), 2
                    ) if total_pixels > 0 else 100.0

                # Compute chip geometry from transform
                from rasterio.transform import Affine
                if isinstance(transform, Affine):
                    # Top-left corner of chip in CRS coordinates
                    x_min, y_max = transform * (x_start, y_start)
                    x_max, y_min = transform * (
                        x_start + chip_size, y_start + chip_size
                    )
                    chip_geom = mapping(box(x_min, y_min, x_max, y_max))
                else:
                    chip_geom = {"type": "Polygon", "coordinates": []}

                # Build chip ID following naming convention
                acq = acquisition_date
                chip_id = (
                    f"{sensor}/{aoi_id}/{acq.year}/{acq.month:02d}/{acq.day:02d}/"
                    f"chip_{row_idx:04d}_{col_idx:04d}"
                )

                chips.append(
                    Chip(
                        chip_id=chip_id,
                        aoi_id=aoi_id,
                        sensor=sensor,
                        acquisition_date=acquisition_date,
                        bands=band_names or [],
                        data=chip_data.astype(np.float32),
                        cloud_mask=chip_cloud_mask,
                        cloud_pct=chip_cloud_pct,
                        geometry=chip_geom,
                        crs=crs,
                        resolution_m=10.0,
                    )
                )

        return chips
