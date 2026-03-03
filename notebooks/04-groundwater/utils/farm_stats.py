# Implementation guide: see docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md — "Key Outputs"
"""
Farm counting and area calculation utilities for groundwater depletion analysis.

Implements the core detection and classification logic:
  - NDVI threshold (>0.15) → binary active/inactive farm mask per year
  - Year-over-year transition classification (persisted/disappeared/appeared/never)
  - Regional statistics aggregation

Classification logic (from plan doc):
  Year N Active  + Year N+1 Active   → "persisted"
  Year N Active  + Year N+1 Inactive → "disappeared" (abandoned farm — proxy for groundwater loss)
  Year N Inactive + Year N+1 Active  → "appeared"   (new farm)
  Year N Inactive + Year N+1 Inactive → "never_farmed"

See: docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md — "Approach → Classification Logic"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

ACTIVE_NDVI_THRESHOLD = 0.15


@dataclass
class RegionalStats:
    """Per-region annual statistics for groundwater depletion tracking."""
    region: str
    year: int
    active_farms: int         # Count of active farm pixels / typical farm size
    total_area_ha: float      # Total area of active farms in hectares
    pct_change_from_prev: float  # % change vs previous year (negative = depletion)


def detect_active_farms(ndvi_composite: np.ndarray, threshold: float = ACTIVE_NDVI_THRESHOLD) -> np.ndarray:
    """
    Binary active farm mask from annual NDVI composite.

    Returns:
        Boolean array: True = active farm (NDVI > threshold), False = inactive.

    Implementation notes:
    - Apply morphological opening (remove small isolated pixels < 5px)
    - Apply circular geometry filter optionally (only count round objects)
    - Require minimum contiguous area > 1 ha (100 × 100m = 10×10 px at 10m)
    """
    raise NotImplementedError


def classify_transitions(
    mask_year_n: np.ndarray,
    mask_year_n1: np.ndarray,
) -> np.ndarray:
    """
    Classify per-pixel year-over-year transitions.

    Returns:
        uint8 array with values:
          0 = never_farmed
          1 = persisted
          2 = disappeared (abandoned)
          3 = appeared (new farm)
    """
    raise NotImplementedError


def compute_regional_stats(
    active_mask: np.ndarray,
    aoi_id: str,
    year: int,
    prev_active_mask: np.ndarray | None,
    resolution_m: float = 10.0,
) -> RegionalStats:
    """Aggregate pixel-level farm masks into regional statistics."""
    raise NotImplementedError


def compute_depletion_rate(annual_stats: List[RegionalStats]) -> float:
    """
    Compute linear depletion rate via linear regression on active farm area vs year.

    Returns:
        Slope in ha/year (negative = depletion trend).
    """
    raise NotImplementedError
