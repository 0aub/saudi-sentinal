# Implementation guide: see docs/plans/level-1-notebooks/06-neom-construction-tracker.md — "Model Architecture"
"""
Sentinel-1 SAR preprocessing for NEOM construction tracking.

SAR advantage for construction monitoring:
  - Detects metal structures and concrete independent of illumination/clouds
  - High backscatter = metal/concrete (construction materials)
  - Texture changes indicate surface disturbance (earthworks, grading)

Preprocessing steps:
  1. Radiometric calibration (convert DN to sigma0 in linear power)
  2. Speckle filtering (Lee filter or Gamma-MAP)
  3. Terrain correction (if significant topography — NEOM area has mountains)
  4. Convert to dB: 10 * log10(sigma0)

See: docs/plans/level-1-notebooks/06-neom-construction-tracker.md
"""

from __future__ import annotations

import numpy as np


def apply_lee_filter(image: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Apply Lee speckle filter to reduce SAR noise.

    Args:
        image:       2D float32 SAR intensity array (linear scale)
        window_size: Filter window size (5×5 or 7×7 recommended)

    Returns:
        Speckle-filtered array, same shape.

    Implementation notes:
    - Lee filter: output = mean + k * (pixel - mean)
      where k = variance_signal / (variance_signal + variance_noise)
    - Estimate variance_noise from homogeneous water area
    - Use scipy.ndimage for efficient sliding window operations
    """
    raise NotImplementedError


def linear_to_db(linear_intensity: np.ndarray) -> np.ndarray:
    """Convert linear SAR intensity to dB scale: 10 * log10(intensity). Clip at -30 dB."""
    raise NotImplementedError


def compute_sar_texture(image_db: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Compute local standard deviation as a texture feature.

    High texture = construction site (heterogeneous surfaces).
    Low texture = bare desert (homogeneous).

    Returns:
        Local std array, same shape as input.
    """
    raise NotImplementedError
