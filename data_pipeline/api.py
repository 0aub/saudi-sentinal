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

from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="Saudi Sentinel AI — Tile API",
    version="1.0",
    description="Internal tile data service. See docs/plans/LEVEL-0-DATA-PIPELINE.md.",
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
    raise NotImplementedError("Implement: TileCatalog.list_aois()")


@app.get("/api/v1/aois/{aoi_id}/chips")
async def list_chips(
    aoi_id: str,
    sensor: Optional[str] = Query(None, description="s1 or s2"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    max_cloud: float = Query(20.0),
):
    """
    List chips available for an AOI, optionally filtered by sensor, date range, and cloud %.

    Implementation: TileCatalog.query_chips(aoi_id, (start, end), sensor, max_cloud)
    Returns: {count, chips: [ChipMeta...]}
    """
    raise NotImplementedError("Implement: TileCatalog.query_chips(...)")


# --- Chips ---

@app.get("/api/v1/chips/{chip_id}/metadata")
async def get_chip_metadata(chip_id: str):
    """
    Return JSON metadata for a single chip.

    Implementation: TileCatalog query by chip_id → return as JSON dict
    """
    raise NotImplementedError("Implement: TileCatalog chip metadata lookup")


@app.get("/api/v1/chips/{chip_id}")
async def download_chip(chip_id: str):
    """
    Stream a chip as a GeoTIFF file.

    Implementation: TileStore.load_chip(chip_id) → StreamingResponse with
    media_type="image/tiff" and Content-Disposition header.
    """
    raise NotImplementedError("Implement: TileStore.load_chip → StreamingResponse")


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
    raise NotImplementedError("Implement: TileCatalog.get_timeseries(...)")


# --- Ingestion trigger ---

@app.post("/api/v1/ingest", response_model=IngestResponse)
async def trigger_ingest(request: IngestRequest):
    """
    Trigger an ingestion job for the given AOI and date range.

    Implementation: Enqueue a Celery/background task that runs ingest.py logic.
    Returns immediately with a job_id for status polling.
    """
    raise NotImplementedError("Implement: enqueue ingestion background task")
