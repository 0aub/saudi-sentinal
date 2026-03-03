# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "PostGIS Catalog Schema" and "Chip Specification"
"""
CRS (Coordinate Reference System) conversion and bounding box utilities.

Used across all levels to:
- Convert between WGS84 (EPSG:4326) and UTM zones (EPSG:32637 for Saudi Arabia)
- Compute geographic bounds from AOI center + size
- Generate GeoJSON polygon from bounding box
- Convert pixel coordinates to geographic coordinates using rasterio transforms

Saudi Arabia spans UTM zones 37N-38N (EPSG:32637, EPSG:32638).
For simplicity, EPSG:32637 (37N) is used for the western region,
EPSG:32638 (38N) for the eastern/Gulf region.

All stored geometries use EPSG:4326 (WGS84 geographic).
Processing uses local UTM for accurate distance/area calculations.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


def bbox_from_center_size(
    lat: float,
    lon: float,
    width_km: float,
    height_km: float,
) -> Tuple[float, float, float, float]:
    """
    Compute bounding box from center coordinates and size.

    Args:
        lat, lon:    Center in decimal degrees (WGS84)
        width_km:    East-west extent in kilometers
        height_km:   North-south extent in kilometers

    Returns:
        (min_lon, min_lat, max_lon, max_lat) in decimal degrees

    Formula:
        1 degree latitude  ≈ 111.32 km
        1 degree longitude ≈ 111.32 × cos(lat_radians) km
    """
    raise NotImplementedError


def bbox_to_geojson_polygon(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> dict:
    """Convert a bounding box to a GeoJSON Polygon dict (EPSG:4326)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]],
    }


def wgs84_to_utm(lat: float, lon: float) -> Tuple[float, float, int]:
    """
    Convert WGS84 geographic coordinates to UTM.

    Returns:
        (easting_m, northing_m, epsg_code)

    Uses pyproj.Transformer for conversion.
    Auto-selects UTM zone from longitude.
    """
    raise NotImplementedError


def compute_area_km2(geometry_wgs84: dict) -> float:
    """
    Compute area of a GeoJSON polygon in km².

    Reprojects to appropriate UTM zone for accurate area calculation.
    Uses shapely + pyproj.
    """
    raise NotImplementedError


def pixel_to_lonlat(
    row: int,
    col: int,
    transform: object,
) -> Tuple[float, float]:
    """
    Convert pixel (row, col) to (longitude, latitude) using rasterio affine transform.

    Args:
        row, col:  Zero-indexed pixel coordinates
        transform: Rasterio affine transform object

    Returns:
        (lon, lat) in the CRS of the transform (usually EPSG:4326 or UTM)
    """
    raise NotImplementedError
