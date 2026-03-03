# Implementation guide: see docs/plans/level-1-notebooks/05-desertification-warning.md — "Model Architecture"
"""
Desertification risk score calibration and map generation.

Risk levels:
  Low risk:    Core agricultural area (stable NDVI > 0.2 for 5 years)
  Medium risk: Agricultural margin (declining NDVI trend)
  High risk:   Actively degrading (NDVI collapsed in last 2 years)

XGBoost target metric: AUC > 0.83, High-risk F1 > 0.75
Export: XGBoost model as pickle or ONNX for MLOps serving

See: docs/plans/level-1-notebooks/05-desertification-warning.md — "Model Architecture"
"""

from __future__ import annotations

from typing import Dict

import numpy as np


RISK_LEVELS = {0: "low", 1: "medium", 2: "high"}


def calibrate_risk_scores(
    raw_probabilities: np.ndarray,
    calibration_data: np.ndarray | None = None,
) -> np.ndarray:
    """
    Calibrate raw XGBoost probability outputs into well-calibrated risk scores.

    Args:
        raw_probabilities: Array of shape (N, 3) — P(low), P(medium), P(high) per pixel
        calibration_data:  Optional labeled data for Platt scaling or isotonic regression

    Returns:
        Calibrated probabilities of same shape.

    Implementation notes:
    - Use sklearn.calibration.CalibratedClassifierCV
    - Or simple isotonic regression on held-out validation set
    """
    raise NotImplementedError


def generate_risk_map(
    feature_matrix: np.ndarray,
    model,
    spatial_shape: tuple,
) -> np.ndarray:
    """
    Run XGBoost model on full-AOI feature matrix and reshape to spatial risk map.

    Args:
        feature_matrix: Shape (H*W, 14) — flattened spatial features
        model:          Trained XGBoost classifier
        spatial_shape:  (H, W) of the original raster

    Returns:
        Risk class array of shape (H, W) uint8:
          0=low, 1=medium, 2=high
    """
    raise NotImplementedError


def compute_risk_statistics(risk_map: np.ndarray, resolution_m: float = 10.0) -> Dict:
    """
    Compute summary statistics for a risk map.

    Returns:
        Dict with keys: low_area_km2, medium_area_km2, high_area_km2,
                        high_risk_pct, medium_risk_pct
    """
    raise NotImplementedError
