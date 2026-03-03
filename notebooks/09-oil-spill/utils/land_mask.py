# Implementation guide: see docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Known Challenges"
"""
Land masking for SAR oil spill detection in the Arabian Gulf.

Land pixels must be removed before oil detection because:
  - Land has very different backscatter characteristics from water
  - Near-coast SAR processing artifacts are common
  - Oil spills only occur on water

Masking approach:
  1. Use a static land/water mask derived from OSM coastline or ESA WorldCover
  2. Apply 1km buffer from coast (removes artifact-prone near-shore zone)
  3. Optionally mask shallow water (<20m depth) from GEBCO bathymetry

Source for coastline: Natural Earth or GADM (both free)

See: docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Known Challenges → Near-coast SAR artifacts"
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_land_mask(
    bounds: tuple,
    resolution_m: float = 10.0,
    coastline_path: Path | None = None,
) -> np.ndarray:
    """
    Load or generate a land mask for the given bounding box.

    Args:
        bounds:          (min_lon, min_lat, max_lon, max_lat) in EPSG:4326
        resolution_m:    Output resolution in meters
        coastline_path:  Path to vector coastline file (GeoJSON or Shapefile)
                         If None, attempts to load from Natural Earth data

    Returns:
        Boolean mask array: True = water pixel (include), False = land (exclude).
    """
    raise NotImplementedError


def apply_coast_buffer(
    land_mask: np.ndarray,
    buffer_km: float = 1.0,
    resolution_m: float = 10.0,
) -> np.ndarray:
    """
    Erode the water mask to exclude pixels within buffer_km of the coast.

    Args:
        land_mask:    Boolean water mask (True = water)
        buffer_km:    Distance from coast to exclude (1km recommended)
        resolution_m: Pixel size in meters

    Returns:
        Eroded water mask — smaller water area, safer for detection.

    Implementation: scipy.ndimage.binary_erosion with circular structuring element
    """
    raise NotImplementedError
