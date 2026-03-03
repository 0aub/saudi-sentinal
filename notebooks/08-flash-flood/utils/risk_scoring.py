# Implementation guide: see docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Model Architecture"
"""
Flash flood risk probability calibration and map generation.

XGBoost classifier input (12 features per pixel):
  [elevation, slope, TWI, flow_accum, aspect, curvature,
   distance_to_wadi, HAND, flood_frequency, mean_backscatter,
   backscatter_variability, land_cover_class]

Target metric: AUC > 0.82, High-risk precision > 0.75
Validation: Known Jeddah flood event extents (2009, 2011 documented)

See: docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Model Architecture"
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


def build_feature_matrix(
    dem_features: Dict[str, np.ndarray],
    flood_frequency: np.ndarray,
    sar_statistics: Dict[str, np.ndarray],
) -> np.ndarray:
    """
    Assemble the 12-feature matrix for XGBoost training.

    Args:
        dem_features:   Dict of DEM-derived features (8 features)
        flood_frequency: How many times each pixel was flagged as flooded
        sar_statistics:  Dict with mean_backscatter, backscatter_variability

    Returns:
        Feature matrix shape (H*W, 12), flattened for sklearn/XGBoost.
    """
    raise NotImplementedError


def generate_flood_risk_map(
    feature_matrix: np.ndarray,
    model,
    spatial_shape: tuple,
) -> np.ndarray:
    """
    Run XGBoost on full feature matrix and reshape to flood risk probability map.

    Returns:
        Float32 risk probability array of shape (H, W), range [0, 1].
    """
    raise NotImplementedError
