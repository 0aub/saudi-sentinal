# Implementation guide: see docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Labeling Strategy → DTW"
"""
Dynamic Time Warping (DTW) for crop type classification from temporal NDVI profiles.

DTW measures similarity between two temporal sequences while allowing elastic
time-warping — ideal for matching crop phenological curves that may shift ±2 weeks
due to planting date variability.

Used for:
1. Propagating crop labels from hand-labeled template farms to unlabeled farms
2. Baseline crop classification by nearest-neighbor DTW matching
3. Alfalfa identification (distinctive multi-peak signature)

See: docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Labeling Strategy → DTW similarity"
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def dtw_distance(ts1: np.ndarray, ts2: np.ndarray, window: int = 3) -> float:
    """
    Compute DTW distance between two equal-length time-series.

    Args:
        ts1, ts2: 1D arrays of monthly NDVI values
        window:   Sakoe-Chiba band width (constrains warping path, speeds up computation)

    Returns:
        DTW distance (lower = more similar)

    Implementation notes:
    - Use dynamic programming (O(n×m) cost matrix)
    - Apply Sakoe-Chiba band for efficiency: |i-j| <= window
    - Normalize by path length to make distances comparable across lengths
    - Alternatively: use dtaidistance library for vectorized C implementation
    """
    raise NotImplementedError


def classify_farms_by_dtw(
    query_profiles: np.ndarray,
    template_profiles: Dict[str, np.ndarray],
    k: int = 3,
) -> List[str]:
    """
    Classify farms using k-NN DTW (k nearest labeled templates).

    Args:
        query_profiles:    Array of shape (N_query, 12) — unlabeled farm NDVI profiles
        template_profiles: Dict mapping crop_class → array of shape (N_templates, 12)
        k:                 Number of nearest neighbors

    Returns:
        List of N_query predicted crop class labels.
    """
    raise NotImplementedError
