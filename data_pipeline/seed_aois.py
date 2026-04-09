# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → step 3
"""
AOI seeding script — loads aois.yaml and inserts all AOIs into PostGIS catalog.

Usage:
    python data_pipeline/seed_aois.py --config data_pipeline/config/aois.yaml

This is a one-time setup step run before any data ingestion.
After seeding, AOIs are queryable via the Tile API at /api/v1/aois.

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → "Run initial AOI seeding"
"""

import math
import os
import logging

import yaml
import click
from pathlib import Path

from data_pipeline.catalog.tile_catalog import TileCatalog

logger = logging.getLogger(__name__)


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
    width_km, height_km = size_km[0], size_km[1]

    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat))

    half_lat = (height_km / 2.0) / km_per_deg_lat
    half_lon = (width_km / 2.0) / km_per_deg_lon

    min_lat = lat - half_lat
    max_lat = lat + half_lat
    min_lon = lon - half_lon
    max_lon = lon + half_lon

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


@click.command()
@click.option(
    "--config",
    default="data_pipeline/config/aois.yaml",
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
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Error: config file not found: {config_path}", err=True)
        raise SystemExit(1)

    with open(config_path) as f:
        data = yaml.safe_load(f)

    aois = data.get("aois", {})
    if not aois:
        click.echo("No AOIs found in config file.")
        return

    catalog = None
    if not dry_run:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            click.echo("Error: DATABASE_URL environment variable is not set.", err=True)
            raise SystemExit(1)
        catalog = TileCatalog(database_url=database_url)

    count = 0
    for aoi_id, aoi_cfg in aois.items():
        center = aoi_cfg["center"]  # [lat, lon]
        size_km = aoi_cfg["size_km"]  # [width_km, height_km]
        projects = aoi_cfg.get("projects", [])

        lat, lon = center[0], center[1]
        geometry = bbox_from_center_and_size(lat, lon, size_km)

        if dry_run:
            click.echo(
                f"[DRY RUN] AOI: {aoi_id} | center=({lat}, {lon}) | "
                f"size_km={size_km} | projects={projects}"
            )
            click.echo(f"  geometry: {geometry}")
        else:
            try:
                catalog.register_aoi(
                    aoi_id=aoi_id,
                    name=aoi_id,
                    geometry=geometry,
                    projects=projects,
                )
                click.echo(f"Registered AOI: {aoi_id}")
            except Exception as exc:
                click.echo(f"Error registering AOI {aoi_id}: {exc}", err=True)
                continue

        count += 1

    click.echo(f"\n{'[DRY RUN] ' if dry_run else ''}{count} AOIs seeded successfully.")


if __name__ == "__main__":
    main()
