# Implementation guide: see docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Stage 2: Look-Alike Discrimination"
"""
Geometric shape descriptors for oil slick vs. look-alike discrimination.

Shape is a powerful discriminator:
  Oil slicks:      Elongated streaks aligned with wind direction (high elongation)
  Biogenic slicks: Irregular, blob-like shapes
  Wind shadows:    Often rectangular/angular (aligned with wind field boundaries)
  Rain cells:      Circular or amorphous

Features per detected dark patch:
  area:           Patch area in km²
  perimeter:      Patch boundary length in km
  elongation:     Major axis / minor axis ratio (oil → high elongation)
  compactness:    4π × area / perimeter² (circle=1, elongated→0)
  orientation:    Angle of major axis vs wind direction (oil aligns with wind)
  solidity:       area / convex_hull_area (irregular shapes → low solidity)

See: docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Stage 2: Look-Alike Discrimination"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ShapeFeatures:
    """Geometric descriptors for a single dark patch."""
    area_km2: float
    perimeter_km: float
    elongation: float       # Major axis / minor axis (> 3 suggests oil)
    compactness: float      # 4π × area / perimeter² ∈ (0, 1]
    orientation_deg: float  # Angle of major axis (compare with wind direction)
    solidity: float         # Convex hull fill ratio


def compute_shape_features(
    binary_mask: np.ndarray,
    pixel_size_m: float = 10.0,
    wind_direction_deg: float | None = None,
) -> ShapeFeatures:
    """
    Compute geometric shape features from a binary patch mask.

    Args:
        binary_mask:        Boolean 2D array — True = dark patch pixels
        pixel_size_m:       Spatial resolution
        wind_direction_deg: Optional wind direction for orientation alignment

    Returns:
        ShapeFeatures dataclass.

    Implementation:
    - Use skimage.measure.regionprops for all geometric properties
    - elongation = major_axis_length / minor_axis_length
    - solidity from regionprops directly
    """
    raise NotImplementedError
