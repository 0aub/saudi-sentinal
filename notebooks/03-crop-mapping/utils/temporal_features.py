# Implementation guide: see docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Model Architecture"
"""
Phenology feature extraction from NDVI time-series for crop type classification.

Each pivot farm is characterized by its NDVI temporal profile (phenological curve).
These features are used by both the Random Forest baseline and as input to DTW matching.

Key phenological features per farm:
  - Peak NDVI value and timing (month of max NDVI)
  - Number of peaks per year (single-crop vs alfalfa with multiple cuts)
  - Peak amplitude (NDVI_max - NDVI_min)
  - Season start and end (green-up and senescence dates)
  - Growing season length in months

See: docs/plans/level-1-notebooks/03-crop-type-mapping.md — "Model Architecture → Random Forest baseline"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class PhenologyFeatures:
    """Extracted phenological features for a single farm's annual NDVI series."""
    ndvi_mean: float
    ndvi_max: float
    ndvi_min: float
    ndvi_std: float
    peak_month: int           # 1–12
    peak_amplitude: float     # ndvi_max - ndvi_min
    n_peaks: int              # Number of NDVI peaks per year
    season_length_months: int # Months above NDVI=0.15
    green_up_month: int       # Month NDVI first exceeds 0.15
    senescence_month: int     # Month NDVI last exceeds 0.15


def extract_phenology_features(ndvi_series: np.ndarray) -> PhenologyFeatures:
    """
    Extract phenological features from a 1D NDVI time-series (12 monthly values).

    Args:
        ndvi_series: 1D array of 12 monthly NDVI values (one full year)

    Returns:
        PhenologyFeatures dataclass

    Implementation notes:
    - Use scipy.signal.find_peaks to detect NDVI peaks
    - Handle NaN values (cloud gaps) by linear interpolation
    - For alfalfa (multiple cuts), n_peaks will be 4–7
    """
    raise NotImplementedError


def build_feature_matrix(
    farm_ndvi_profiles: List[np.ndarray],
) -> np.ndarray:
    """
    Build feature matrix for all farms (used by Random Forest baseline).

    Args:
        farm_ndvi_profiles: List of 1D arrays of length 12 (monthly NDVI)

    Returns:
        Feature matrix of shape (N_farms, N_features) float32
    """
    raise NotImplementedError
