# Implementation guide: see docs/plans/level-1-notebooks/05-desertification-warning.md — "Feature Engineering Details"
"""
Sentinel-2 optical feature extraction for desertification risk scoring.

Per-pixel features computed over a 24-month rolling window:
  NDVI_mean:              Average vegetation health
  NDVI_trend:             Sen's slope of NDVI (robust to outliers)
  NDVI_std:               Instability indicator
  NDVI_min:               Worst-case vegetation state
  SAVI_mean:              Soil-adjusted vegetation (better for arid regions)
  NMDI_mean:              Normalized Moisture Difference Index
  months_below_threshold: Count of months where NDVI < 0.08

See: docs/plans/level-1-notebooks/05-desertification-warning.md — "Feature Engineering Details"
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


def nmdi(nir: np.ndarray, swir1: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """
    NMDI = (B08 - (B11 - B12)) / (B08 + (B11 - B12)).
    Normalized Moisture Difference Index — sensitive to soil and vegetation moisture.
    """
    raise NotImplementedError


def compute_ndvi_temporal_features(
    monthly_ndvi: List[np.ndarray],
    window_months: int = 24,
) -> Dict[str, np.ndarray]:
    """
    Compute 7 NDVI-based temporal features per pixel.

    Args:
        monthly_ndvi: List of 2D NDVI arrays (one per month), length >= window_months
        window_months: Lookback window for statistics

    Returns:
        Dict with keys:
          'ndvi_mean', 'ndvi_trend', 'ndvi_std', 'ndvi_min', 'ndvi_max',
          'months_below_threshold'

    Implementation notes:
    - Use pymannkendall or scipy.stats.theilslopes for trend (Sen's slope)
    - Handle NaN via np.nanmean, np.nanstd, etc.
    """
    raise NotImplementedError


def build_full_feature_vector(
    optical_features: Dict[str, np.ndarray],
    sar_features: Dict[str, np.ndarray],
    dem_features: Dict[str, np.ndarray],
) -> np.ndarray:
    """
    Stack all 14 features into a single feature matrix for XGBoost.

    The 14 features per pixel (from plan doc):
      [ndvi_mean, ndvi_trend, ndvi_std, savi_mean, nmdi_mean,
       soil_moisture_mean, soil_moisture_trend, cross_pol_ratio,
       ndvi_min, ndvi_max, months_below_threshold,
       distance_to_desert_edge, elevation, slope]

    Returns:
        Array of shape (H*W, 14) — flattened spatial dimensions for sklearn/XGBoost
    """
    raise NotImplementedError
