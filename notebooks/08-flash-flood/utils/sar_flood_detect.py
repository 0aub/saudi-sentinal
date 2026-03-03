# Implementation guide: see docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Component A: Historical Flood Extent"
"""
SAR change detection for historical flood extent extraction.

Method: Temporal anomaly detection on Sentinel-1 backscatter.
  1. Build per-pixel baseline: mean and std of VV backscatter across all dry-period scenes
  2. For each new SAR scene, flag pixels where VV < (mean - 2×std) as potentially flooded
     (flooded soil has lower backscatter due to specular reflection)
  3. Cross-reference with rainfall records (ERA5 or CHIRPS) to confirm flood events
  4. Accumulate into flood frequency map (how many times each pixel was flagged)

Limitation: S1 revisit every 6-12 days. Most Saudi flash floods last hours.
Value comes from building a historical flood frequency map for risk modeling,
not real-time detection.

See: docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Component A: Historical Flood Extent"
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def build_sar_baseline(
    sar_scenes: List[np.ndarray],
    dry_season_mask: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build per-pixel mean and std of VV backscatter from dry-period scenes.

    Args:
        sar_scenes:       List of 2D VV arrays (dB), ordered by acquisition date
        dry_season_mask:  Optional boolean mask of which scenes are known dry (June–Sep)

    Returns:
        (mean_vv, std_vv) — baseline statistics per pixel, same shape as scenes.
    """
    raise NotImplementedError


def detect_flood_pixels(
    new_scene_vv: np.ndarray,
    mean_vv: np.ndarray,
    std_vv: np.ndarray,
    n_sigma: float = 2.0,
) -> np.ndarray:
    """
    Flag pixels where backscatter drops significantly below baseline.

    Returns:
        Boolean mask: True = potentially flooded.

    Formula: flooded if vv < (mean_vv - n_sigma × std_vv)
    """
    raise NotImplementedError


def build_flood_frequency_map(
    flood_masks: List[np.ndarray],
) -> np.ndarray:
    """
    Aggregate per-scene flood masks into a flood frequency map.

    Returns:
        Integer array: value = number of times pixel was detected as flooded.
    """
    raise NotImplementedError
