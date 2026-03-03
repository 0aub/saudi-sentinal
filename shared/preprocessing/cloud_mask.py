# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Sentinel-2 L2A → Cloud mask"
"""
SCL-based cloud masking for Sentinel-2 L2A imagery.

SCL (Scene Classification Layer) pixel values (from ESA documentation):
  0  = No data
  1  = Saturated / Defective
  2  = Dark area pixels
  3  = Cloud shadows
  4  = Vegetation              ← VALID
  5  = Bare soils              ← VALID
  6  = Water                   ← VALID
  7  = Unclassified
  8  = Cloud medium probability
  9  = Cloud high probability
  10 = Thin cirrus
  11 = Snow or ice

Valid pixels (used in Level 0): SCL values 4, 5, 6
Everything else is masked (set to NaN in output arrays).

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Sentinel-2 L2A → Cloud mask" and "TileProcessor"
"""

from __future__ import annotations

import numpy as np

VALID_SCL_VALUES = frozenset({4, 5, 6})  # vegetation, bare soil, water


def scl_to_valid_mask(scl: np.ndarray) -> np.ndarray:
    """
    Convert SCL array to a boolean valid-pixel mask.

    Args:
        scl: 2D uint8 array from Sentinel-2 L2A SCL band

    Returns:
        Boolean array: True = valid pixel (SCL in {4, 5, 6}), False = masked.
    """
    return np.isin(scl, list(VALID_SCL_VALUES))


def apply_cloud_mask(
    bands: dict,
    scl: np.ndarray,
    fill_value: float = float("nan"),
) -> dict:
    """
    Apply cloud mask to a dict of band arrays.

    Args:
        bands:      Dict mapping band_name → 2D float32 array
        scl:        SCL array (resampled to match bands resolution)
        fill_value: Value to use for masked pixels (default NaN)

    Returns:
        Dict with same keys; cloudy pixels replaced by fill_value.
    """
    mask = scl_to_valid_mask(scl)
    return {
        name: np.where(mask, arr, fill_value).astype(np.float32)
        for name, arr in bands.items()
    }


def compute_cloud_percentage(scl: np.ndarray) -> float:
    """
    Compute percentage of pixels that are invalid (cloud/shadow/etc).

    Returns:
        Float in [0, 100]: 0.0 = fully clear, 100.0 = fully covered.
    """
    valid_count = np.isin(scl, list(VALID_SCL_VALUES)).sum()
    return 100.0 * (1.0 - valid_count / scl.size)
