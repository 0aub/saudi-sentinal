# Implementation guide: see docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Model Architecture → Baseline"
"""
Trend detection utilities for vegetation time-series analysis.

Methods:
  Mann-Kendall test:  Non-parametric test for monotonic trend (baseline)
  Sen's slope:        Robust trend slope estimator (pairs well with MK test)
  Linear regression:  Parametric trend quantification (slope = rate of SAVI change/month)

These are the statistical baselines against which the Bi-LSTM model is compared.

See: docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Model Architecture → Baseline Comparison"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class TrendResult:
    """Result of a trend test on a single pixel time-series."""
    slope: float            # Sen's slope (SAVI units per month)
    p_value: float          # Mann-Kendall p-value
    significant: bool       # p_value < 0.05
    trend: str              # "greening", "browning", or "stable"
    tau: float              # Mann-Kendall Kendall's tau statistic


def mann_kendall_test(ts: np.ndarray) -> TrendResult:
    """
    Apply Mann-Kendall monotonic trend test to a 1D time-series.

    Args:
        ts: 1D array of SAVI values (e.g. 60 monthly values)

    Returns:
        TrendResult with slope, p_value, significant, trend, tau.

    Implementation notes:
    - Use pymannkendall library or implement from scratch
    - Classify as "greening" if slope > 0 and p < 0.05
    - Classify as "browning" if slope < 0 and p < 0.05
    - Otherwise "stable"
    """
    raise NotImplementedError


def sens_slope(ts: np.ndarray) -> float:
    """
    Compute Sen's slope estimator (median of all pairwise slopes).
    More robust to outliers than OLS regression.
    """
    raise NotImplementedError


def apply_trend_pixelwise(savi_stack: np.ndarray) -> np.ndarray:
    """
    Apply Mann-Kendall trend test to every pixel in a SAVI time-series stack.

    Args:
        savi_stack: Array of shape (T, H, W) — T monthly SAVI composites

    Returns:
        Classified trend array of shape (H, W), uint8:
          0 = stable
          1 = greening (positive significant trend)
          2 = browning (negative significant trend)

    Note: This is slow for large arrays — use multiprocessing or vectorized MK.
    """
    raise NotImplementedError
