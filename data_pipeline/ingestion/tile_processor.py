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

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np


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

    def process_s2(self, product_path: Path, aoi: dict) -> List[Chip]:
        """
        Process a Sentinel-2 L2A .SAFE product into 256×256 chips.

        Steps:
        1. Locate band files (B02, B03, B04, B08 at 10m; B11, B12, SCL at 20m)
        2. Resample 20m bands to 10m using bilinear interpolation (rasterio.warp)
        3. Clip to AOI bounding box
        4. Apply SCL cloud mask
        5. Normalize reflectance: divide by 10000, clip to [0, 1]
        6. Slice into 256×256 chips on a regular grid
        7. Return list of Chip objects (only chips with cloud_pct < threshold)
        """
        raise NotImplementedError(
            "Implement S2 processing. See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def process_s1(self, product_path: Path, aoi: dict) -> List[Chip]:
        """
        Process a Sentinel-1 GRD product into 256×256 chips.

        Steps:
        1. Locate VV and VH band files
        2. Convert linear intensity to dB: 10 * log10(intensity)
        3. Apply terrain correction if needed (SNAP or pyroSAR)
        4. Clip to AOI bounding box
        5. Slice into 256×256 chips
        6. Return list of Chip objects
        """
        raise NotImplementedError(
            "Implement S1 processing. See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def cloud_mask_s2(self, bands: dict, scl: np.ndarray) -> np.ndarray:
        """
        Generate boolean cloud mask from SCL (Scene Classification Layer).

        Args:
            bands: Dict mapping band name → np.ndarray
            scl:   SCL array (uint8), resampled to 10m

        Returns:
            Boolean mask: True = valid pixel, False = cloudy/shadow/invalid
        """
        raise NotImplementedError(
            "Return np.isin(scl, list(self.VALID_SCL_VALUES)). "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md — cloud mask spec."
        )

    def _slice_to_chips(
        self,
        data: np.ndarray,
        transform: object,
        aoi_id: str,
        sensor: str,
        acquisition_date: object,
        chip_size: int = 256,
    ) -> List[Chip]:
        """Slice a full-AOI array into non-overlapping chip_size×chip_size tiles."""
        raise NotImplementedError
