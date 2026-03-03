# Implementation guide: see docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Topographic Features"
"""
DEM-derived topographic feature computation for flash flood risk modeling.

Source: Copernicus DEM GLO-30 (30m resolution, free via AWS Open Data).

Features computed (from plan doc):
  elevation:               Height above sea level (m)
  slope:                   Terrain steepness (degrees)
  TWI:                     Topographic Wetness Index = ln(A / tan(slope))
                           Primary indicator of flood susceptibility
  flow_accumulation:       Upstream contributing area (proxy for wadi channels)
  aspect:                  Slope direction (degrees from North)
  curvature:               Surface concavity/convexity (concave = water collection)
  distance_to_wadi:        Distance to nearest extracted drainage network (m)
  HAND:                    Height Above Nearest Drainage — best single flood predictor

See: docs/plans/level-1-notebooks/08-flash-flood-risk.md — "Topographic Features from DEM"
"""

from __future__ import annotations

from typing import Dict

import numpy as np


def compute_slope_and_aspect(dem: np.ndarray, resolution_m: float = 30.0) -> tuple:
    """
    Compute slope (degrees) and aspect (degrees from North) from a DEM.

    Returns:
        (slope_deg, aspect_deg) both shape same as dem.

    Implementation notes:
    - Use numpy gradient: dy, dx = np.gradient(dem, resolution_m)
    - slope = arctan(sqrt(dx² + dy²)) in degrees
    - aspect = arctan2(dy, dx) in degrees, normalized to [0, 360]
    - Or use richdem library for production-quality flow analysis
    """
    raise NotImplementedError


def compute_twi(flow_accumulation: np.ndarray, slope_deg: np.ndarray, resolution_m: float = 30.0) -> np.ndarray:
    """
    Topographic Wetness Index = ln(catchment_area / tan(slope)).

    Args:
        flow_accumulation: Upstream area in pixels
        slope_deg:         Slope in degrees

    Returns:
        TWI array. High values = flat areas with large upstream catchment = flood-prone.

    Note: Add small epsilon to tan(slope) to avoid division by zero on flat terrain.
    """
    raise NotImplementedError


def compute_hand(dem: np.ndarray, drainage_mask: np.ndarray) -> np.ndarray:
    """
    Height Above Nearest Drainage (HAND).

    For each pixel, compute the elevation difference to the nearest
    drainage channel pixel. Best single predictor of flood extent.

    Args:
        dem:           2D elevation array
        drainage_mask: Boolean mask of drainage network pixels (True = wadi/channel)

    Returns:
        HAND array — same shape as dem.

    Implementation notes:
    - Use scipy.ndimage.distance_transform_edt for efficient nearest-drainage computation
    - Or use pysheds library which implements HAND natively
    """
    raise NotImplementedError


def extract_drainage_network(flow_accumulation: np.ndarray, threshold: int = 1000) -> np.ndarray:
    """
    Extract drainage network by thresholding flow accumulation.

    Args:
        flow_accumulation: Upstream pixel count
        threshold:         Minimum upstream area to be considered a channel

    Returns:
        Boolean drainage network mask.
    """
    raise NotImplementedError


def compute_all_dem_features(dem: np.ndarray, resolution_m: float = 30.0) -> Dict[str, np.ndarray]:
    """
    Compute all 8 DEM-derived features in one call.

    Returns:
        Dict with keys: elevation, slope, twi, flow_accumulation,
                        aspect, curvature, distance_to_wadi, hand
    """
    raise NotImplementedError
