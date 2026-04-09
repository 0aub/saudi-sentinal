# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Chip Specification" section
"""
256x256 chip slicing logic for converting full-AOI rasters into ML-ready tiles.

Chip specification:
    Size:       256x256 pixels (2.56 km x 2.56 km at 10m resolution)
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

import math
from pathlib import Path
from typing import Generator, Tuple

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window


class ChipCreator:
    """
    Slices a full-AOI raster array into non-overlapping 256x256 chips.

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
        num_bands, height, width = data.shape
        cs = self.chip_size

        n_rows = math.ceil(height / cs)
        n_cols = math.ceil(width / cs)

        for row_idx in range(n_rows):
            for col_idx in range(n_cols):
                row_off = row_idx * cs
                col_off = col_idx * cs

                # Determine the actual window size (may be smaller at edges)
                win_h = min(cs, height - row_off)
                win_w = min(cs, width - col_off)

                window = Window(col_off=col_off, row_off=row_off, width=win_w, height=win_h)

                # Extract chip data from the source array
                chip_data = np.full((num_bands, cs, cs), np.nan, dtype=np.float32)
                chip_data[:, :win_h, :win_w] = data[:, row_off:row_off + win_h, col_off:col_off + win_w]

                # Compute the affine transform for this chip
                chip_transform = rasterio.windows.transform(window, transform)

                yield chip_data, chip_transform, row_idx, col_idx

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
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        num_bands, height, width = chip_data.shape

        with rasterio.open(
            str(output_path),
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=num_bands,
            dtype="float32",
            crs=crs,
            transform=chip_transform,
            compress="lzw",
            nodata=np.nan,
        ) as dst:
            dst.write(chip_data.astype(np.float32))

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
