# Implementation guide: see docs/plans/level-1-notebooks/02-green-riyadh-monitor.md and 04-groundwater-depletion-tracker.md
"""
Monthly and annual composite builders — shared across multiple notebooks.

Compositing reduces noise and cloud contamination by taking the median
of all valid (cloud-free) acquisitions within a time window.

Used by:
  Notebook 02: Monthly SAVI composites for Green Riyadh trend analysis
  Notebook 04: Annual peak-season NDVI composites for groundwater tracking
  Notebook 05: Monthly S1+S2 composites for desertification features

Compositing method: pixel-wise median (np.nanmedian) — robust to outliers.
Alternative for speed: pixel-wise mean (np.nanmean) — faster but sensitive to clouds.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


def median_composite(
    arrays: List[np.ndarray],
    weights: Optional[List[float]] = None,
) -> np.ndarray:
    """
    Compute pixel-wise median across a list of arrays.

    Args:
        arrays:  List of 2D or 3D float32 arrays (same shape). NaN = invalid/cloudy.
        weights: Optional weights (currently unused; reserved for quality-weighted composites)

    Returns:
        Median composite, same shape as input arrays. NaN where all inputs are NaN.
    """
    if not arrays:
        raise ValueError("Cannot composite empty list")
    stack = np.stack(arrays, axis=0)
    return np.nanmedian(stack, axis=0).astype(np.float32)


def build_monthly_composites(
    chip_time_series: List[Tuple[object, np.ndarray]],
    year: int,
) -> Dict[Tuple[int, int], np.ndarray]:
    """
    Build monthly median composites from a time-series of chips.

    Args:
        chip_time_series: List of (acquisition_date, chip_array) tuples
        year:             Target year (filter to this year's acquisitions)

    Returns:
        Dict mapping (year, month) → composite array.
        Missing months (no valid chips) are absent from the dict.
    """
    raise NotImplementedError(
        "Group chips by month, compute median_composite per group. "
        "See docs/plans/level-1-notebooks/02-green-riyadh-monitor.md."
    )


def build_annual_max_composite(
    chip_time_series: List[Tuple[object, np.ndarray]],
    year: int,
    months: Optional[List[int]] = None,
) -> Optional[np.ndarray]:
    """
    Build annual maximum composite from chips in specified months.

    Args:
        chip_time_series: List of (date, array) tuples
        year:             Target year
        months:           Months to include (default: all). Use [2,3,4] for peak season.

    Returns:
        Per-pixel maximum array, or None if no valid chips found.
        Used for pivot farm detection (annual max NDVI highlights vegetation peak).
    """
    raise NotImplementedError
