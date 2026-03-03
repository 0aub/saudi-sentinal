# Implementation guide: see docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Stage 2: Look-Alike Discrimination"
"""
Gray-Level Co-occurrence Matrix (GLCM) texture features for oil spill discrimination.

GLCM features help distinguish true oil slicks from look-alikes:
  - Oil patches: smooth texture (damped surface), homogeneous
  - Wind shadows: similar in backscatter but often non-elongated
  - Biogenic slicks: irregular texture (biological material)
  - Construction zones: not applicable (this is marine detection)

GLCM features per dark patch:
  contrast:      Local variation intensity
  homogeneity:   Spatial closeness of GLCM elements
  energy:        Sum of squared GLCM elements (uniformity)
  correlation:   Linear dependency of pixel pairs
  dissimilarity: Similar to contrast but linear weighting

See: docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Stage 2: Look-Alike Discrimination"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GLCMFeatures:
    """GLCM-derived texture features for a single image patch."""
    contrast: float
    homogeneity: float
    energy: float
    correlation: float
    dissimilarity: float
    contrast_ratio: float  # inside / outside dark patch (key discriminator)


def compute_glcm_features(
    patch: np.ndarray,
    distances: list = None,
    angles: list = None,
) -> GLCMFeatures:
    """
    Compute GLCM texture features for a single SAR image patch.

    Args:
        patch:     2D float32 array — the dark anomaly patch
        distances: GLCM distances (default [1, 2])
        angles:    GLCM angles in radians (default [0, π/4, π/2, 3π/4])

    Returns:
        GLCMFeatures with averaged features across all distances/angles.

    Implementation:
    - Use skimage.feature.graycomatrix and graycoprops
    - Quantize patch to uint8 (0-255) before GLCM computation
    """
    raise NotImplementedError


def compute_damping_ratio(
    patch_backscatter: float,
    surrounding_backscatter: float,
) -> float:
    """
    Compute damping ratio: backscatter inside patch / outside patch.

    Lower damping ratio = darker patch = more likely oil (not low wind).
    Oil typically shows damping ratio of 0.3–0.6; wind shadows 0.6–0.8.
    """
    raise NotImplementedError
