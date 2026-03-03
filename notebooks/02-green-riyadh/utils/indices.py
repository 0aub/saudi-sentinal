# Implementation guide: see docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Derived Indices"
"""
Vegetation and water index computation for Green Riyadh monitoring.

Indices (from plan doc):
  NDVI  = (B08 - B04) / (B08 + B04)
  NDWI  = (B03 - B08) / (B03 + B08)   — water body detection
  EVI   = 2.5 × (B08-B04) / (B08 + 6×B04 - 7.5×B02 + 1)
  SAVI  = 1.5 × (B08-B04) / (B08 + B04 + 0.5)  ← preferred for arid regions

Note: SAVI and EVI are preferred over NDVI in desert cities because they correct
for soil background reflectance which dominates in Riyadh.

SAVI classification thresholds:
  < 0.05:      Bare / Built-up
  0.05–0.15:   Sparse vegetation
  0.15–0.30:   Moderate vegetation
  > 0.30:      Dense vegetation

See: docs/plans/level-1-notebooks/02-green-riyadh-monitor.md — "Derived Indices" and "Labeling Strategy"
"""

from __future__ import annotations

import numpy as np


def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red). Safe division — returns NaN on zero denominator."""
    raise NotImplementedError


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDWI = (Green - NIR) / (Green + NIR). Detects water bodies (irrigated parks)."""
    raise NotImplementedError


def evi(blue: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """EVI = 2.5 × (NIR - Red) / (NIR + 6×Red - 7.5×Blue + 1). Enhanced for arid regions."""
    raise NotImplementedError


def savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
    """
    SAVI = (1 + L) × (NIR - Red) / (NIR + Red + L).
    L=0.5 is standard for intermediate soil cover.
    Preferred over NDVI for desert cities (reduces soil noise).
    """
    raise NotImplementedError


def classify_vegetation(savi_array: np.ndarray) -> np.ndarray:
    """
    Classify SAVI values into 4 vegetation density classes.

    Returns uint8 array:
      0 = Bare / Built-up     (SAVI < 0.05)
      1 = Sparse vegetation    (0.05 ≤ SAVI < 0.15)
      2 = Moderate vegetation  (0.15 ≤ SAVI < 0.30)
      3 = Dense vegetation     (SAVI ≥ 0.30)
    """
    raise NotImplementedError
