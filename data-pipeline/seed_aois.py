# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → step 3
"""
AOI seeding script — loads aois.yaml and inserts all AOIs into PostGIS catalog.

Usage:
    python data-pipeline/seed_aois.py --config data-pipeline/config/aois.yaml

This is a one-time setup step run before any data ingestion.
After seeding, AOIs are queryable via the Tile API at /api/v1/aois.

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → "Run initial AOI seeding"
"""

import yaml
import click
from pathlib import Path


def bbox_from_center_and_size(lat: float, lon: float, size_km: list) -> dict:
    """
    Convert center + size_km to a GeoJSON Polygon.

    Args:
        lat, lon:  Center coordinates in decimal degrees.
        size_km:   [width_km, height_km] of the bounding box.

    Returns:
        GeoJSON Polygon dict (EPSG:4326).

    Implementation note:
    - 1 degree latitude  ≈ 111.32 km (constant)
    - 1 degree longitude ≈ 111.32 * cos(lat_radians) km
    """
    raise NotImplementedError(
        "Convert center/size to bbox polygon. "
        "See docs/plans/LEVEL-0-DATA-PIPELINE.md — AOI definitions."
    )


@click.command()
@click.option(
    "--config",
    default="data-pipeline/config/aois.yaml",
    show_default=True,
    help="Path to aois.yaml",
)
@click.option("--dry-run", is_flag=True, help="Print AOIs without writing to DB")
def main(config: str, dry_run: bool) -> None:
    """
    Seed all AOIs from aois.yaml into the PostGIS catalog.

    Implementation steps:
    1. Load aois.yaml with PyYAML
    2. For each AOI entry:
       a. Compute GeoJSON polygon from center + size_km using bbox_from_center_and_size()
       b. Call TileCatalog.register_aoi(aoi_id, name, geometry, projects)
    3. Print summary: N AOIs seeded successfully
    """
    raise NotImplementedError(
        "Implement AOI seeding. See docs/plans/LEVEL-0-DATA-PIPELINE.md — Setup Steps."
    )


if __name__ == "__main__":
    main()
