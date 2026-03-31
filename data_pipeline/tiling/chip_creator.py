# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Specification" section
"""
256×256 chip slicing logic for converting full-AOI rasters into ML-ready tiles.

Chip specification:
    Size:       256×256 pixels (2.56 km × 2.56 km at 10m resolution)
    Sentinel-2: 6 bands (B02,B03,B04,B08,B11,B12), float32 [0.0, 1.0]
    Sentinel-1: 2 bands (VV, VH), float32 dB backscatter
    Format:     GeoTIFF with CRS and affine transform metadata
    NoData:     NaN

Naming convention:
    {sensor}/{aoi}/{year}/{month}/{day}/{chip_id}.tif
    chip_id = chip_{row:04d}_{col:04d}

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Naming Convention" and "Chip Specification"
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Tuple

import numpy as np


class ChipCreator:
    """
    Slices a full-AOI raster array into non-overlapping 256×256 chips.

    Implementation guide: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Specification"
    """

    def __init__(self, chip_size: int = 256) -> None:
        self.chip_size = chip_size

    def slice_array(
        self,
        data: np.ndarray,
        transform: object,
        crs: str,
    ) -> Generator[Tuple[np.ndarray, object, int, int], None, None]:
        """
        Yield (chip_data, chip_transform, row_idx, col_idx) for each tile.

        Args:
            data:      Full raster array of shape (C, H, W)
            transform: Rasterio affine transform for the full array
            crs:       Coordinate reference system string (e.g. "EPSG:32637")

        Yields:
            Tuple of:
              - chip_data: np.ndarray shape (C, chip_size, chip_size), float32
              - chip_transform: affine transform for this chip
              - row_idx: grid row index (used in chip_id)
              - col_idx: grid column index (used in chip_id)

        Notes:
        - Chips at the right/bottom edges are zero-padded if the array dimensions
          are not evenly divisible by chip_size.
        - Chips that are >90% NaN (cloud or nodata) should be filtered by the caller.
        """
        raise NotImplementedError(
            "Implement sliding window slicing. "
            "Use rasterio.windows.Window for correct affine sub-transforms. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def save_chip_geotiff(
        self,
        chip_data: np.ndarray,
        chip_transform: object,
        crs: str,
        output_path: Path,
    ) -> None:
        """
        Write a chip to a GeoTIFF file with correct metadata.

        Implementation notes:
        - Use rasterio.open(..., 'w', driver='GTiff', dtype='float32', nodata=np.nan)
        - Set compression='lzw' for smaller file sizes
        - Write transform and CRS for proper georeferencing
        """
        raise NotImplementedError(
            "Implement GeoTIFF writer using rasterio. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    @staticmethod
    def chip_id_from_parts(
        sensor: str,
        aoi_id: str,
        acquisition_date: object,
        row_idx: int,
        col_idx: int,
    ) -> str:
        """
        Generate canonical chip ID string.

        Example: "s2/riyadh-metro/2024/03/15/chip_0024_0031"
        """
        d = acquisition_date
        return f"{sensor}/{aoi_id}/{d.year}/{d.month:02d}/{d.day:02d}/chip_{row_idx:04d}_{col_idx:04d}"
