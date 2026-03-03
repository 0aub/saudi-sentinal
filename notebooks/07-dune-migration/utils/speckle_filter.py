# Implementation guide: see docs/plans/level-1-notebooks/07-sand-dune-migration.md — "Notebook Structure"
"""
SAR speckle filtering algorithms for sand dune morphology analysis.

Speckle is the granular noise inherent to SAR imagery caused by coherent
interference. For dune detection, speckle must be reduced to reveal
gradual dune crest morphology.

Filters implemented:
  Lee filter:      Standard adaptive speckle filter (fast, widely used)
  Gamma-MAP:       Gamma distribution maximum a posteriori (better edge preservation)
  Boxcar filter:   Simple mean filter (baseline — blurs edges)

For quarterly composites, temporal averaging also reduces speckle significantly.

See: docs/plans/level-1-notebooks/07-sand-dune-migration.md — "speckle_filter.py"
"""

from __future__ import annotations

import numpy as np


def lee_filter(image: np.ndarray, window_size: int = 7, looks: float = 1.0) -> np.ndarray:
    """
    Lee adaptive speckle filter for SAR imagery.

    Args:
        image:       2D float32 intensity array (linear scale)
        window_size: Local window size (7 recommended for quarterly composites)
        looks:       Equivalent number of looks (1 for single-look, > 1 for multilook)

    Returns:
        Filtered array, same shape.
    """
    raise NotImplementedError


def gamma_map_filter(image: np.ndarray, window_size: int = 7, looks: float = 1.0) -> np.ndarray:
    """
    Gamma-MAP speckle filter (better edge preservation than Lee).
    Preferred for dune crest detection where sharp transitions matter.
    """
    raise NotImplementedError


def temporal_average_filter(image_stack: np.ndarray) -> np.ndarray:
    """
    Average multiple SAR acquisitions to suppress speckle via temporal diversity.

    Args:
        image_stack: 3D array shape (T, H, W) — T SAR acquisitions

    Returns:
        2D mean array of shape (H, W). Equivalent to multi-look processing.
    """
    raise NotImplementedError
