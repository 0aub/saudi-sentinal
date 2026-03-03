# Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "API Gateway (FastAPI) → Core Endpoints"
"""
Unified FastAPI API Gateway for the Saudi Sentinel AI platform.

This is the single entry point for the React frontend and external API consumers.
It proxies to the Level 2 model server, MLflow, Airflow, and queries PostGIS/MinIO directly.

All endpoints from docs/plans/LEVEL-3-SYSTEM.md:

Project endpoints:
  GET  /api/v1/projects                        → All 9 projects, status, latest metrics
  GET  /api/v1/projects/{id}                   → Detailed project info
  GET  /api/v1/projects/{id}/map               → GeoJSON layer for map rendering
  GET  /api/v1/projects/{id}/stats             → Time-series statistics for charts
  GET  /api/v1/projects/{id}/reports           → Generate PDF/CSV report

Map tile endpoint:
  GET  /api/v1/tiles/{project_id}/{z}/{x}/{y}.png → XYZ raster tile server

Alert endpoints:
  GET  /api/v1/alerts                          → List alerts (filter: severity, project, ack'd)
  POST /api/v1/alerts/{id}/acknowledge         → Mark alert acknowledged
  WS   /api/v1/ws/alerts                       → WebSocket real-time alert push

Compare endpoint:
  GET  /api/v1/compare/{aoi_id}               → Before/after imagery + predictions

Admin endpoints:
  GET  /api/v1/admin/pipelines                 → Airflow DAG status
  POST /api/v1/admin/pipelines/{dag_id}/trigger → Trigger a DAG run
  GET  /api/v1/admin/models                    → MLflow registered models
  POST /api/v1/admin/models/{name}/promote     → Promote model version

Auth: JWT tokens (see docs/plans/LEVEL-3-SYSTEM.md — "Auth: JWT tokens")

Run with:
  uvicorn system.api_gateway.main:app --host 0.0.0.0 --port 8300
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Saudi Sentinel AI",
    version="3.0",
    description="Unified API gateway. See docs/plans/LEVEL-3-SYSTEM.md.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict in production to frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Project Endpoints ---

@app.get("/api/v1/projects")
async def list_projects():
    """
    All 9 projects with status, latest metrics, and last run time.

    Implementation:
    - Query predictions table for latest run per project
    - Query MLflow for current Production model version + metrics
    - Query Airflow API for last DAG run status
    - Return combined summary for all 9 projects
    """
    raise NotImplementedError("See docs/plans/LEVEL-3-SYSTEM.md — list_projects endpoint")


@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Detailed project info: model version, pipeline status, AOIs, recent predictions."""
    raise NotImplementedError


@app.get("/api/v1/projects/{project_id}/map")
async def get_project_map_layer(
    project_id: str,
    aoi_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """
    GeoJSON FeatureCollection for map rendering in Deck.gl.

    Implementation:
    - Query predictions table with PostGIS spatial query
    - Return GeoJSON with prediction raster bounds + colormap metadata
    """
    raise NotImplementedError


@app.get("/api/v1/projects/{project_id}/stats")
async def get_project_stats(project_id: str, aoi_id: Optional[str] = None):
    """Time-series statistics for Recharts visualization."""
    raise NotImplementedError


@app.get("/api/v1/projects/{project_id}/reports")
async def generate_report(project_id: str, format: str = "pdf"):
    """Generate downloadable PDF or CSV report for a project."""
    raise NotImplementedError


# --- Map Tile Server ---

@app.get("/api/v1/tiles/{project_id}/{z}/{x}/{y}.png")
async def get_map_tile(project_id: str, z: int, x: int, y: int):
    """
    XYZ raster tile server for prediction overlays.

    Implementation: tile_server.render_tile(project_id, z, x, y)
    See: system/api-gateway/tile_server.py for rendering logic.
    See: docs/plans/LEVEL-3-SYSTEM.md — "Tile Server Implementation"
    """
    raise NotImplementedError("Implement: tile_server.render_tile(project_id, z, x, y)")


# --- Alert Endpoints ---

@app.get("/api/v1/alerts")
async def list_alerts(
    severity: Optional[str] = None,
    project_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
):
    """List alerts with optional filters. Returns newest first."""
    raise NotImplementedError


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged."""
    raise NotImplementedError


@app.websocket("/api/v1/ws/alerts")
async def alert_websocket(websocket: WebSocket):
    """
    WebSocket connection for real-time alert push.

    Implementation:
    - Accept WebSocket connection
    - Subscribe to Redis pub/sub channel "alerts"
    - Forward new alert messages to connected clients
    - Handle disconnection gracefully

    See: docs/plans/LEVEL-3-SYSTEM.md — "WebSocket alerts"
    """
    raise NotImplementedError


# --- Compare Endpoint ---

@app.get("/api/v1/compare/{aoi_id}")
async def get_comparison(aoi_id: str, date_a: str, date_b: str):
    """Side-by-side satellite imagery + predictions for two dates."""
    raise NotImplementedError


# --- Admin Endpoints ---

@app.get("/api/v1/admin/pipelines")
async def list_pipelines():
    """Proxy to Airflow REST API — DAG status, last runs, next scheduled."""
    raise NotImplementedError("Implement: GET Airflow /api/v1/dags")


@app.post("/api/v1/admin/pipelines/{dag_id}/trigger")
async def trigger_pipeline(dag_id: str):
    """Manually trigger an Airflow DAG run."""
    raise NotImplementedError("Implement: POST Airflow /api/v1/dags/{dag_id}/dagRuns")


@app.get("/api/v1/admin/models")
async def list_models():
    """Proxy to MLflow — registered models, versions, stages."""
    raise NotImplementedError("Implement: MLflow client.search_registered_models()")


@app.post("/api/v1/admin/models/{model_name}/promote")
async def promote_model(model_name: str, from_stage: str, to_stage: str):
    """Promote a model version in MLflow registry."""
    raise NotImplementedError("Implement: mlflow_config.promote_model(...)")
