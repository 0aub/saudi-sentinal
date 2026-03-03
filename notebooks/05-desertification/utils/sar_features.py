# Implementation guide: see docs/plans/level-1-notebooks/05-desertification-warning.md — "Derived Features → S1"
"""
Sentinel-1 SAR feature extraction for desertification risk scoring.

SAR-derived features (from plan doc):
  Soil moisture proxy:      VH/VV ratio (higher ratio = more soil moisture)
  Cross-polarization ratio: VH - VV in dB (sensitive to surface roughness)
  Soil moisture trend:      Linear slope of 12-month VH/VV time-series

These are combined with Sentinel-2 optical features in an XGBoost classifier.

Sensor fusion note:
  S1 revisit: 6-12 days; S2 revisit: 5 days.
  Both are resampled to monthly composites on the same 10m grid before fusion.

See: docs/plans/level-1-notebooks/05-desertification-warning.md — "Derived Features"
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


def soil_moisture_proxy(vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
    """
    Compute VH/VV ratio as soil moisture proxy.

    Higher ratio indicates more moisture (wetter soil backscatters differently
    in cross-polarization vs co-polarization).

    Args:
        vv, vh: Linear intensity arrays (NOT in dB). Shape (H, W).

    Returns:
        Float32 array of VH/VV ratio. Clip to [0, 1] to remove outliers.
    """
    raise NotImplementedError


def cross_polarization_ratio_db(vv_db: np.ndarray, vh_db: np.ndarray) -> np.ndarray:
    """
    Compute VH - VV in dB (cross-polarization ratio).

    Args:
        vv_db, vh_db: Backscatter in dB. Shape (H, W).

    Returns:
        Float32 array of (VH - VV) in dB.
        Sensitive to surface roughness changes caused by wind erosion.
    """
    raise NotImplementedError


def compute_sar_temporal_features(
    monthly_vv: List[np.ndarray],
    monthly_vh: List[np.ndarray],
    window_months: int = 12,
) -> Dict[str, np.ndarray]:
    """
    Compute temporal SAR features over a rolling window.

    Args:
        monthly_vv:    List of monthly VV composites (each shape (H, W))
        monthly_vh:    List of monthly VH composites
        window_months: Number of months to compute statistics over

    Returns:
        Dict with keys:
          'soil_moisture_mean':  Mean VH/VV ratio over window
          'soil_moisture_trend': Linear slope of VH/VV over window
          'cross_pol_ratio':     Mean (VH-VV) over window
    """
    raise NotImplementedError
