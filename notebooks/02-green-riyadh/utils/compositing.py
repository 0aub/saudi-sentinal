# Implementation guide: see docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Notebook Structure → compositing.py"
"""
Cloud-free monthly composite builder for Sentinel-2 vegetation monitoring.

Creates monthly median composites from all valid (cloud-free) chip acquisitions.
Composites are the input to SAVI/EVI computation and LSTM trend modeling.

Method:
  For each pixel in each month, compute the median across all valid acquisitions
  (where valid = SCL cloud mask passes). This reduces noise and cloud contamination.

See: docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Monthly Composites" notebook
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np


def build_monthly_composite(
    chips: List[Dict],
    year: int,
    month: int,
    bands: List[str],
    tile_api_url: str,
) -> Optional[np.ndarray]:
    """
    Build a cloud-free monthly median composite.

    Args:
        chips:        List of chip metadata dicts from Tile API for this month
        year, month:  Target composite period
        bands:        Band names to include (e.g. ["B04", "B08"])
        tile_api_url: Level 0 Tile API base URL

    Returns:
        Composite array of shape (len(bands), H, W) float32, or None if no valid chips.

    Implementation notes:
    - Load each chip's data from Tile API
    - Stack valid pixels per band across all acquisitions
    - Compute per-pixel median (np.nanmedian) — handles remaining NaN (cloud) pixels
    - Return NaN where all acquisitions were masked (inevitable for some pixels)
    """
    raise NotImplementedError(
        "Implement monthly median compositing. "
        "See docs/plans/level-1-notebooks/02-green-riyadh-monitor.md."
    )


def build_annual_composites(
    aoi_id: str,
    year_range: Tuple[int, int],
    bands: List[str],
    tile_api_url: str,
) -> Dict[Tuple[int, int], np.ndarray]:
    """
    Build composites for all months across a year range.

    Returns:
        Dict mapping (year, month) → composite array.
        Covers 60 months for 2019–2024.
    """
    raise NotImplementedError
