# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" section
"""
CLI entry point for historical backfill and scheduled ingestion.

Usage:
    python data-pipeline/ingest.py --aoi riyadh-metro --sensor s2 \
        --start 2019-01-01 --end 2024-12-31

    python data-pipeline/ingest.py --aoi arabian-gulf-coast --sensor s1 \
        --start 2019-01-01 --end 2024-12-31 --max-cloud 100

This script:
1. Loads AOI geometry from PostGIS catalog
2. Searches CDSE for available products in date range
3. Skips products already in the catalog (idempotent)
4. Downloads, processes, and stores new chips
5. Records ingestion run metadata in ingestion_runs table

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → "Run historical backfill"
"""

import click


@click.command()
@click.option("--aoi", required=True, help="AOI ID from aois.yaml (e.g. riyadh-metro)")
@click.option(
    "--sensor",
    required=True,
    type=click.Choice(["s1", "s2"]),
    help="Sentinel sensor to ingest",
)
@click.option("--start", required=True, help="Start date YYYY-MM-DD")
@click.option("--end", required=True, help="End date YYYY-MM-DD")
@click.option("--max-cloud", default=20, show_default=True, help="Max cloud % (S2 only)")
@click.option(
    "--config",
    default="data-pipeline/config/aois.yaml",
    show_default=True,
    help="Path to aois.yaml",
)
def main(aoi: str, sensor: str, start: str, end: str, max_cloud: int, config: str) -> None:
    """
    Ingest Sentinel tiles for a given AOI and date range.

    Implementation steps:
    1. Load settings from environment (DATABASE_URL, MINIO_ENDPOINT, etc.)
    2. Load AOI geometry from catalog (TileCatalog.get_aoi)
    3. Instantiate CDSEClient, TileProcessor, TileStore, TileCatalog
    4. Search CDSE for products: CDSEClient.search_products(...)
    5. For each product not already in catalog:
       a. CDSEClient.download_product(...)
       b. TileProcessor.process_s2(...) or .process_s1(...)
       c. TileStore.store_chip(...) for each chip
       d. TileCatalog.register_chip(...) for each chip
    6. Record ingestion run in ingestion_runs table
    7. Clean up downloaded .SAFE archives to save disk space
    """
    raise NotImplementedError(
        "Implement ingestion CLI. See docs/plans/LEVEL-0-DATA-PIPELINE.md — 'Setup Steps'."
    )


if __name__ == "__main__":
    main()
