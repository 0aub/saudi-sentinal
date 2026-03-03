# Implementation guide: see docs/plans/level-1-notebooks/01-urban-sprawl-detector.md, 02-green-riyadh-monitor.md, 05-desertification-warning.md
"""
Spectral index computation for Sentinel-2 imagery.

Shared across all notebooks that use vegetation or built-up indices.
All functions use safe division (returns NaN on zero denominator).

Indices:
  NDVI:  Vegetation health — (B08 - B04) / (B08 + B04)
  SAVI:  Soil-adjusted vegetation — preferred for arid regions
  EVI:   Enhanced vegetation — better for dense canopy
  NDWI:  Water bodies — (B03 - B08) / (B03 + B08)
  NDBI:  Built-up index — (B11 - B08) / (B11 + B08)     [Urban Sprawl]
  BSI:   Bare soil index — separates soil from construction [Urban Sprawl]
  NMDI:  Moisture difference — (B08-(B11-B12))/(B08+(B11-B12)) [Desertification]

Band naming follows Sentinel-2 convention:
  B02=Blue(490nm), B03=Green(560nm), B04=Red(665nm), B08=NIR(842nm)
  B11=SWIR1(1610nm), B12=SWIR2(2190nm)

See: docs/plans/level-1-notebooks/01-urban-sprawl-detector.md — "Derived Features"
     docs/plans/level-1-notebooks/02-green-riyadh-monitor.md  — "Derived Indices"
     docs/plans/level-1-notebooks/05-desertification-warning.md — "Derived Features"
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-10  # Small epsilon to avoid division by zero


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Compute ratio, setting result to NaN where denominator ≈ 0."""
    with np.errstate(invalid="ignore", divide="ignore"):
        result = np.where(np.abs(denominator) > _EPS, numerator / denominator, np.nan)
    return result.astype(np.float32)


def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red). Range: [-1, 1]. Vegetation > 0.2."""
    return _safe_ratio(nir - red, nir + red)


def savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
    """
    SAVI = (1 + L) × (NIR - Red) / (NIR + Red + L).
    L=0.5 optimal for intermediate soil cover.
    Preferred over NDVI in arid regions (reduced soil background noise).
    """
    return _safe_ratio((1 + L) * (nir - red), nir + red + L)


def evi(blue: np.ndarray, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """EVI = 2.5 × (NIR - Red) / (NIR + 6×Red - 7.5×Blue + 1)."""
    return _safe_ratio(2.5 * (nir - red), nir + 6 * red - 7.5 * blue + 1)


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDWI = (Green - NIR) / (Green + NIR). Detects water bodies (> 0 = water)."""
    return _safe_ratio(green - nir, green + nir)


def ndbi(swir1: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDBI = (SWIR1 - NIR) / (SWIR1 + NIR). Highlights built-up areas (> 0)."""
    return _safe_ratio(swir1 - nir, swir1 + nir)


def bsi(blue: np.ndarray, red: np.ndarray, nir: np.ndarray, swir1: np.ndarray) -> np.ndarray:
    """BSI = ((SWIR1+Red) - (NIR+Blue)) / ((SWIR1+Red) + (NIR+Blue)). Bare soil > 0."""
    return _safe_ratio((swir1 + red) - (nir + blue), (swir1 + red) + (nir + blue))


def nmdi(nir: np.ndarray, swir1: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """NMDI = (NIR - (SWIR1-SWIR2)) / (NIR + (SWIR1-SWIR2)). Moisture indicator."""
    diff = swir1 - swir2
    return _safe_ratio(nir - diff, nir + diff)
