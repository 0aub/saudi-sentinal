# Implementation guide: see docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md — "Data Requirements"
"""
Annual peak-season NDVI composite builder for groundwater depletion tracking.

Compositing strategy:
  - Use only Feb–Apr acquisitions (peak growing season for Saudi winter crops)
  - Compute annual median NDVI per pixel across all Feb–Apr scenes
  - Output: one composite per year (2019–2024) = 6 composites total

The peak-season window is critical: this is when active farms show maximum NDVI
and abandoned farms are most distinguishable (NDVI below 0.15 threshold).

See: docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md — "Data Requirements"
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

PEAK_SEASON_MONTHS = [2, 3, 4]  # Feb, Mar, Apr


def build_peak_season_composite(
    aoi_id: str,
    year: int,
    tile_api_url: str,
    max_cloud_pct: float = 15.0,
) -> Optional[np.ndarray]:
    """
    Build annual peak-season NDVI composite for groundwater proxy detection.

    Args:
        aoi_id:       AOI to process (e.g. "aljouf-farms")
        year:         Target year
        tile_api_url: Level 0 Tile API URL
        max_cloud_pct: Maximum cloud % for included chips

    Returns:
        2D float32 array of median NDVI, or None if no valid chips found.

    Implementation notes:
    - Query Tile API for chips in Feb/Mar/Apr for this AOI and year
    - Compute NDVI = (B08 - B04) / (B08 + B04) per chip
    - Stack and compute per-pixel median (np.nanmedian)
    """
    raise NotImplementedError


def build_all_annual_composites(
    aoi_id: str,
    year_range: Tuple[int, int],
    tile_api_url: str,
) -> Dict[int, np.ndarray]:
    """Build peak-season composites for each year in range. Returns Dict[year → ndvi_array]."""
    raise NotImplementedError
