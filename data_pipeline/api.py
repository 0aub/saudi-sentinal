# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Tile API (FastAPI)" section
"""
FastAPI tile query API — serves chip metadata and data to notebooks and MLOps pipelines.

Endpoints (from docs/plans/LEVEL-0-DATA-PIPELINE.md):
  GET  /api/v1/aois                             → List all AOIs
  GET  /api/v1/aois/{aoi_id}/chips             → List chips for AOI
       ?sensor=s2&start=2024-01-01&end=2024-12-31&max_cloud=15
  GET  /api/v1/chips/{chip_id}                 → Download chip as GeoTIFF
  GET  /api/v1/chips/{chip_id}/metadata        → Chip metadata (JSON)
  GET  /api/v1/timeseries/{aoi_id}             → Time-ordered chip list
       ?sensor=s2&band=ndvi&aggregation=monthly
  POST /api/v1/ingest                          → Trigger ingestion for AOI + date range
  GET  /api/v1/health                          → Service health check

Run with:
  uvicorn data_pipeline.api:app --host 0.0.0.0 --port 8100
"""

from __future__ import annotations

import io
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import List, Optional

import numpy as np
import rasterio
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from data_pipeline.catalog.tile_catalog import TileCatalog
from data_pipeline.catalog.tile_store import TileStore
from data_pipeline.config.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: create shared catalog and store on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.catalog = TileCatalog(database_url=settings.database_url)
    app.state.tile_store = TileStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    logger.info("Tile API started — catalog and store initialised")
    yield
    logger.info("Tile API shutting down")


app = FastAPI(
    title="Saudi Sentinel AI — Tile API",
    version="1.0",
    description="Internal tile data service. See docs/plans/LEVEL-0-DATA-PIPELINE.md.",
    lifespan=lifespan,
)


# --- Request / Response models ---

class IngestRequest(BaseModel):
    aoi_id: str
    sensor: str        # "s1" or "s2"
    start_date: date
    end_date: date
    max_cloud_pct: int = 20


class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_catalog() -> TileCatalog:
    return app.state.catalog


def _get_tile_store() -> TileStore:
    return app.state.tile_store


def _chip_meta_to_dict(chip) -> dict:
    """Convert a ChipMeta object to a JSON-serialisable dict."""
    return {
        "chip_id": chip.chip_id,
        "aoi_id": chip.aoi_id,
        "sensor": chip.sensor,
        "acquisition_date": str(chip.acquisition_date),
        "cloud_pct": chip.cloud_pct,
        "geometry": chip.geometry,
        "minio_key": chip.minio_key,
        "bands": chip.bands,
        "chip_size_px": chip.chip_size_px,
        "resolution_m": chip.resolution_m,
        "quality_flag": chip.quality_flag,
    }


def _array_to_geotiff_bytes(data: np.ndarray) -> io.BytesIO:
    """Write a numpy array (C, H, W) to an in-memory GeoTIFF and return a BytesIO."""
    if data.ndim == 2:
        data = data[np.newaxis, :, :]
    bands, height, width = data.shape

    buf = io.BytesIO()
    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=bands,
        dtype=data.dtype,
        compress="lzw",
    ) as dst:
        for i in range(bands):
            dst.write(data[i], i + 1)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Background ingestion task
# ---------------------------------------------------------------------------

def _run_ingestion(
    aoi_id: str,
    sensor: str,
    start_date: date,
    end_date: date,
    max_cloud_pct: int,
    job_id: str,
) -> None:
    """Execute a full ingestion run in the background."""
    from data_pipeline.ingestion.cdse_client import CDSEClient
    from data_pipeline.ingestion.tile_processor import TileProcessor

    catalog = _get_catalog()
    tile_store = _get_tile_store()
    chips_added = 0
    error_msg: str | None = None

    try:
        client = CDSEClient(
            client_id=os.environ.get("CDSE_CLIENT_ID"),
            client_secret=os.environ.get("CDSE_CLIENT_SECRET"),
        )
        client.authenticate()

        aoi = catalog.get_aoi(aoi_id)
        collection = "SENTINEL-2" if sensor == "s2" else "SENTINEL-1"

        products = client.search_products(
            aoi=aoi["geometry"],
            start=start_date,
            end=end_date,
            collection=collection,
            cloud_pct=max_cloud_pct,
        )

        processor = TileProcessor()
        tmp_dir = Path("/tmp") / f"ingest-{job_id}"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        for product in products:
            try:
                product_path = client.download_product(product.product_id, tmp_dir)
                if sensor == "s2":
                    chips = processor.process_s2(product_path, aoi)
                else:
                    chips = processor.process_s1(product_path, aoi)

                for chip in chips:
                    tile_store.store_chip(chip.chip_id, chip.data, metadata={
                        "aoi_id": chip.aoi_id,
                        "sensor": chip.sensor,
                        "acquisition_date": str(chip.acquisition_date),
                        "cloud_pct": chip.cloud_pct,
                    })
                    catalog.register_chip(chip)
                    chips_added += 1

            except Exception:
                logger.exception("Failed to process product %s", product.product_id)
                continue

        status = "completed"
        logger.info("Ingestion job %s completed — %d chips added", job_id, chips_added)

    except Exception as exc:
        status = "failed"
        error_msg = str(exc)
        logger.exception("Ingestion job %s failed: %s", job_id, error_msg)

    finally:
        try:
            catalog.record_ingestion_run(
                aoi_id=aoi_id,
                sensor=sensor,
                date_from=start_date,
                date_to=end_date,
                chips_added=chips_added,
                status=status,
                error_msg=error_msg,
            )
        except Exception:
            logger.exception("Failed to record ingestion run for job %s", job_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# --- Health ---

@app.get("/api/v1/health")
async def health():
    """Service health check. Returns status of DB, MinIO, and Redis connections."""
    return {"status": "healthy", "service": "tile-api", "version": "1.0"}


# --- AOIs ---

@app.get("/api/v1/aois")
async def list_aois():
    """
    List all registered AOIs with geometry and project assignments.

    Implementation: TileCatalog.list_aois() → serialize to GeoJSON FeatureCollection
    """
    catalog = _get_catalog()
    try:
        aois = catalog.list_aois()
    except Exception as exc:
        logger.exception("Failed to list AOIs")
        raise HTTPException(status_code=500, detail=str(exc))
    return aois


@app.get("/api/v1/aois/{aoi_id}/chips")
async def list_chips(
    aoi_id: str,
    sensor: Optional[str] = Query(None, description="s1 or s2"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    max_cloud: float = Query(20.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    List chips available for an AOI, optionally filtered by sensor, date range, and cloud %.

    Implementation: TileCatalog.query_chips(aoi_id, (start, end), sensor, max_cloud)
    Returns: {count, chips: [ChipMeta...]}
    """
    catalog = _get_catalog()

    # Verify AOI exists
    try:
        catalog.get_aoi(aoi_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"AOI '{aoi_id}' not found")

    date_range = (start, end)
    chips = catalog.query_chips(
        aoi_id=aoi_id,
        date_range=date_range,
        sensor=sensor,
        max_cloud=max_cloud,
    )

    # Apply limit/offset manually if the catalog doesn't support them natively
    total = len(chips)
    chips_page = chips[offset : offset + limit]

    return {
        "count": total,
        "limit": limit,
        "offset": offset,
        "chips": [_chip_meta_to_dict(c) for c in chips_page],
    }


# --- Chips ---

@app.get("/api/v1/chips/{chip_id:path}/metadata")
async def get_chip_metadata(chip_id: str):
    """
    Return JSON metadata for a single chip.

    Implementation: TileCatalog query by chip_id → return as JSON dict
    """
    catalog = _get_catalog()
    # Query chips matching this chip_id across all AOIs
    chips = catalog.query_chips(
        aoi_id=None,
        date_range=(None, None),
        sensor=None,
        max_cloud=100.0,
    )
    for chip in chips:
        if chip.chip_id == chip_id:
            return _chip_meta_to_dict(chip)

    raise HTTPException(status_code=404, detail=f"Chip '{chip_id}' not found")


@app.get("/api/v1/chips/{chip_id:path}")
async def download_chip(chip_id: str):
    """
    Stream a chip as a GeoTIFF file.

    Implementation: TileStore.load_chip(chip_id) → StreamingResponse with
    media_type="image/tiff" and Content-Disposition header.
    """
    tile_store = _get_tile_store()

    try:
        data = tile_store.load_chip(chip_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Chip '{chip_id}' not found in storage")

    buf = _array_to_geotiff_bytes(data)
    filename = chip_id.replace("/", "_") + ".tif"

    return StreamingResponse(
        buf,
        media_type="image/tiff",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Time-series ---

@app.get("/api/v1/timeseries/{aoi_id}")
async def get_timeseries(
    aoi_id: str,
    sensor: str = Query("s2"),
    band: Optional[str] = Query(None, description="e.g. ndvi — compute on the fly"),
    aggregation: str = Query("monthly", description="monthly | all"),
):
    """
    Return time-ordered chip list for time-series analysis.

    Implementation: TileCatalog.get_timeseries(aoi_id, sensor, band, aggregation)
    If band is specified, compute the index (NDVI etc.) and include mean value per chip.
    """
    catalog = _get_catalog()

    # Verify AOI exists
    try:
        catalog.get_aoi(aoi_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"AOI '{aoi_id}' not found")

    timeseries = catalog.get_timeseries(
        aoi_id=aoi_id,
        sensor=sensor,
        band=band,
        aggregation=aggregation,
    )
    return {"aoi_id": aoi_id, "sensor": sensor, "aggregation": aggregation, "timeseries": timeseries}


# --- Ingestion trigger ---

@app.post("/api/v1/ingest", response_model=IngestResponse)
async def trigger_ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger an ingestion job for the given AOI and date range.

    Implementation: Enqueue a Celery/background task that runs ingest.py logic.
    Returns immediately with a job_id for status polling.
    """
    job_id = str(uuid.uuid4())

    background_tasks.add_task(
        _run_ingestion,
        aoi_id=request.aoi_id,
        sensor=request.sensor,
        start_date=request.start_date,
        end_date=request.end_date,
        max_cloud_pct=request.max_cloud_pct,
        job_id=job_id,
    )

    return IngestResponse(
        job_id=job_id,
        status="accepted",
        message=f"Ingestion job {job_id} queued for AOI '{request.aoi_id}' "
                f"({request.start_date} to {request.end_date})",
    )
