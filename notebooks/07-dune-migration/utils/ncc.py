# Implementation guide: see docs/plans/level-1-notebooks/07-sand-dune-migration.md — "Label Generation"
"""
Normalized Cross-Correlation (NCC) displacement field generation.

Used to create self-supervised labels for dune migration prediction.
This replaces the need for manual annotation — displacement vectors
are computed from image pairs directly.

Algorithm:
  1. Take SAR image pair (T1, T2) separated by 1 year
  2. For each pixel, compute NCC in a search window (e.g. 32×32 px)
  3. Peak of correlation surface → displacement vector (dx, dy)
  4. Filter low-confidence vectors (correlation peak < threshold)
  5. Output: dense displacement field (optical flow equivalent for SAR)

Reference: standard technique in glaciology and geomorphology literature.

See: docs/plans/level-1-notebooks/07-sand-dune-migration.md — "Label Generation (Self-Supervised)"
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


def normalized_cross_correlation(
    image_t1: np.ndarray,
    image_t2: np.ndarray,
    search_window: int = 32,
    template_size: int = 16,
    confidence_threshold: float = 0.6,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute NCC displacement field between two SAR images.

    Args:
        image_t1:            2D float32 SAR image at time T1
        image_t2:            2D float32 SAR image at time T2
        search_window:       Size of search window in pixels (how far dunes can move)
        template_size:       Size of template patch for correlation
        confidence_threshold: Minimum peak correlation to keep displacement estimate

    Returns:
        Tuple of (dx, dy, confidence):
          dx:         Displacement in x-direction (columns), shape (H, W)
          dy:         Displacement in y-direction (rows), shape (H, W)
          confidence: Peak NCC value at displacement, shape (H, W)
          NaN where confidence < threshold (unreliable estimate)

    Implementation notes:
    - Use scipy.signal.correlate2d for small patches
    - Or scikit-image template matching for better performance
    - Apply sub-pixel refinement by fitting parabola to correlation peak
    """
    raise NotImplementedError


def displacement_to_velocity(
    dx: np.ndarray,
    dy: np.ndarray,
    time_delta_days: int,
    pixel_size_m: float = 10.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert pixel displacement to physical velocity (m/year).

    Returns:
        (vx, vy) velocity components in m/year
    """
    raise NotImplementedError
