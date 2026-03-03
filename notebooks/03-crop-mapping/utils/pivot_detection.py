# Implementation guide: see docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Labeling Strategy → Circle Detection"
"""
Circular pivot irrigation farm detection using Hough Transform.

Saudi pivot farms have a distinctive circular shape (500m–1km diameter) that is
clearly visible at Sentinel-2's 10m resolution. Detection steps:
  1. Compute annual maximum NDVI composite
  2. Apply Hough Circle Transform to find circular farm boundaries
  3. Filter by radius range (50–100 px at 10m → 500m–1km farms)
  4. Return detected farm polygons as GeoJSON circles

See: docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Labeling Strategy"
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def detect_pivot_farms(
    ndvi_annual_max: np.ndarray,
    transform: object,
    crs: str,
    min_radius_px: int = 25,
    max_radius_px: int = 100,
    min_confidence: float = 0.6,
) -> List[dict]:
    """
    Detect circular pivot farms in an annual maximum NDVI image.

    Args:
        ndvi_annual_max: 2D float32 array of annual max NDVI
        transform:       Rasterio affine transform
        crs:             CRS string
        min_radius_px:   Minimum farm radius in pixels (25px = 250m)
        max_radius_px:   Maximum farm radius in pixels (100px = 1km)
        min_confidence:  Hough accumulator threshold

    Returns:
        List of GeoJSON circle polygons, each with properties:
          {farm_id, center_lat, center_lon, radius_m, confidence}

    Implementation notes:
    - Threshold NDVI at 0.15 to get binary vegetation mask
    - Apply skimage.transform.hough_circle or cv2.HoughCircles
    - Convert pixel coordinates to geographic coordinates using transform
    """
    raise NotImplementedError(
        "Implement Hough circle detection on NDVI image. "
        "See docs/plans/level-1-notebooks/03-crop-type-mapping.md."
    )


def farm_to_geojson_polygon(
    center_px: Tuple[int, int],
    radius_px: int,
    transform: object,
    crs: str,
    n_points: int = 64,
) -> dict:
    """Convert a detected circle (pixel coords) to a GeoJSON polygon."""
    raise NotImplementedError
