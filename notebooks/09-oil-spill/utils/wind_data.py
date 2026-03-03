# Implementation guide: see docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Why Wind Speed Matters"
"""
ERA5 wind speed retrieval for oil spill scene filtering.

Wind speed is critical for oil spill detection quality:
  < 3 m/s:  Entire sea is calm (dark) → cannot detect oil → DISCARD SCENE
  3–10 m/s: Normal sea clutter → optimal detection window
  > 10 m/s: Very rough sea → oil mixed into water, reduced detectability

Data source: Copernicus Climate Data Store (CDS), ERA5 reanalysis
  URL: cds.climate.copernicus.eu (free account required)
  API: cdsapi Python package

Variables needed:
  10m_u_component_of_wind (u10)
  10m_v_component_of_wind (v10)
  Wind speed = sqrt(u10² + v10²)

See: docs/plans/level-1-notebooks/09-oil-spill-detection.md — "Why Wind Speed Matters"
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import numpy as np


OPTIMAL_WIND_MIN = 3.0   # m/s
OPTIMAL_WIND_MAX = 10.0  # m/s


def fetch_era5_wind(
    lat: float,
    lon: float,
    datetime_utc: datetime,
    buffer_hours: int = 1,
) -> Optional[Tuple[float, float]]:
    """
    Fetch ERA5 wind speed at a given location and time.

    Args:
        lat, lon:     Center of SAR scene
        datetime_utc: Acquisition time of SAR scene
        buffer_hours: Temporal interpolation window

    Returns:
        (wind_speed_ms, wind_direction_deg) or None if data unavailable.

    Implementation:
    - Use cdsapi to download ERA5 hourly wind data
    - Interpolate to exact scene time and location
    - Cache downloaded ERA5 data locally (large files, avoid re-downloading)

    Note: First-time setup requires CDSE account and ~/.cdsapirc credentials file.
    """
    raise NotImplementedError


def is_scene_valid_for_detection(wind_speed_ms: float) -> bool:
    """
    Return True if wind speed is in the optimal range for oil spill detection.
    Scenes outside [3, 10] m/s should be discarded.
    """
    return OPTIMAL_WIND_MIN <= wind_speed_ms <= OPTIMAL_WIND_MAX
