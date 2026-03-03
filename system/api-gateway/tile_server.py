# Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Tile Server Implementation"
"""
XYZ tile rendering for prediction raster overlays in the React map.

Converts prediction GeoTIFFs stored in MinIO into standard PNG map tiles
consumable by Deck.gl or Mapbox GL JS.

Rendering pipeline for each tile request:
  1. Convert XYZ tile coords to geographic bounds (using mercantile)
  2. Find prediction rasters intersecting bounds (query PostGIS)
  3. Read and mosaic relevant portions from MinIO
  4. Apply project-specific colormap
  5. Return 256×256 PNG bytes

Project colormaps (from docs/plans/LEVEL-3-SYSTEM.md):
  urban-sprawl:    Red (new construction), Gray (unchanged)
  green-riyadh:    Green gradient (SAVI intensity)
  crop-mapping:    Categorical (one color per crop type)
  groundwater:     Traffic light (red=abandoned, green=active, yellow=at-risk)
  desertification: Risk heatmap (red-yellow-green)
  neom-tracker:    Phase colors (construction corridor)
  flash-flood:     Blue gradient (flood probability)
  oil-spill:       Binary red (detected anomaly)
  dune-migration:  Arrow field colormap (direction vectors)

See: docs/plans/LEVEL-3-SYSTEM.md — "Tile Server Implementation"
"""

from __future__ import annotations

from typing import Dict

import numpy as np


# --- Color maps ---

def red_gray_colormap(data: np.ndarray) -> np.ndarray:
    """Urban sprawl: red=changed, gray=unchanged. Input: binary float32."""
    raise NotImplementedError


def green_gradient(data: np.ndarray) -> np.ndarray:
    """Green Riyadh: dark→light green gradient for SAVI intensity [0,1]."""
    raise NotImplementedError


def categorical_colormap(data: np.ndarray, class_colors: Dict[int, tuple]) -> np.ndarray:
    """Crop mapping: one RGBA color per integer class."""
    raise NotImplementedError


def traffic_light_colormap(data: np.ndarray) -> np.ndarray:
    """Groundwater: 0=never_farmed(white), 1=persisted(green), 2=disappeared(red), 3=appeared(blue)."""
    raise NotImplementedError


def risk_heatmap(data: np.ndarray) -> np.ndarray:
    """Desertification/flood: green(0) → yellow(0.5) → red(1.0) risk gradient."""
    raise NotImplementedError


COLORMAPS: Dict[str, object] = {
    "urban-sprawl":    red_gray_colormap,
    "green-riyadh":    green_gradient,
    "crop-mapping":    lambda d: categorical_colormap(d, CROP_COLORS),
    "groundwater":     traffic_light_colormap,
    "desertification": risk_heatmap,
    "neom-tracker":    lambda d: categorical_colormap(d, NEOM_PHASE_COLORS),
    "flash-flood":     lambda d: risk_heatmap(d),
    "oil-spill":       lambda d: risk_heatmap(d),
    "dune-migration":  lambda d: np.zeros((*d.shape[:2], 4), dtype=np.uint8),  # stub
}

CROP_COLORS = {0: (255,215,0,200), 1: (34,139,34,200), 2: (139,90,43,200),
               3: (154,205,50,200), 4: (210,180,140,128), 5: (64,224,208,200)}
NEOM_PHASE_COLORS = {0: (200,200,200,100), 1: (255,165,0,200),
                     2: (255,0,0,220), 3: (0,0,255,200)}


async def render_tile(project_id: str, z: int, x: int, y: int) -> bytes:
    """
    Render a 256×256 PNG tile from prediction rasters in MinIO.

    Args:
        project_id: One of the 9 project names
        z, x, y:   XYZ tile coordinates (Web Mercator / EPSG:3857)

    Returns:
        PNG image bytes ready to send as HTTP response.

    Implementation steps:
    1. bounds = mercantile.bounds(x, y, z)
    2. rasters = query_predictions_for_bounds(project_id, bounds)  # PostGIS query
    3. tile_data = read_and_mosaic(rasters, bounds, size=256)      # rasterio read
    4. colormap = COLORMAPS[project_id]
    5. colored = colormap(tile_data)                               # (256, 256, 4) RGBA
    6. return encode_png(colored)                                   # PIL → bytes

    See: docs/plans/LEVEL-3-SYSTEM.md — "Tile Server Implementation"
    """
    if project_id not in COLORMAPS:
        raise ValueError(f"Unknown project_id: {project_id}")
    raise NotImplementedError(
        "Implement tile rendering pipeline. See docs/plans/LEVEL-3-SYSTEM.md."
    )
