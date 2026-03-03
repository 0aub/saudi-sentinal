# Implementation guide: see docs/plans/LEVEL-2-MLOPS.md — "FastAPI Model Serving" section
"""
Unified FastAPI model server — serves all 9 Saudi Sentinel AI models.

Each model is loaded at startup as an ONNX Runtime InferenceSession from
the MLflow Model Registry ("Production" stage).

Endpoints (from docs/plans/LEVEL-2-MLOPS.md):
  POST /predict/{project_name}               — Run inference on a chip
  GET  /predict/{project_name}/latest/{aoi}  — Get latest results for AOI
  GET  /predict/{project_name}/history/{aoi} — Get historical results
  GET  /models                               — List loaded models + versions
  GET  /models/{project_name}/metrics        — Model performance metrics
  GET  /health                               — Health check

Run with:
  uvicorn mlops.serving.main:app --host 0.0.0.0 --port 8200

See: docs/plans/LEVEL-2-MLOPS.md — "Unified Serving Architecture"
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Saudi Sentinel AI — Model Server",
    version="2.0",
    description="Unified ONNX inference server for all 9 projects. See docs/plans/LEVEL-2-MLOPS.md.",
)

# Model sessions loaded at startup — key: project_name, value: ort.InferenceSession
models: Dict[str, Any] = {}

PROJECT_NAMES = [
    "urban-sprawl",
    "green-riyadh",
    "crop-mapping",
    "groundwater",
    "desertification",
    "neom-tracker",
    "dune-migration",
    "flash-flood",
    "oil-spill",
]


class PredictionRequest(BaseModel):
    chip_id: str                      # Chip ID from Level 0 catalog
    aoi_id: Optional[str] = None
    model_stage: str = "Production"   # "Production" or "Staging"
    return_geotiff: bool = False      # If True, return raw prediction raster


@app.on_event("startup")
async def load_models():
    """
    Load all production ONNX models from MLflow registry at server startup.

    Implementation:
    1. Connect to MLflow tracking server (MLFLOW_TRACKING_URI env var)
    2. For each project in PROJECT_NAMES:
       a. Query MLflow registry for "Production" stage model
       b. Download ONNX artifact to local cache
       c. Create ort.InferenceSession(onnx_path)
       d. Store in models dict
    3. Log which models loaded successfully, which are missing (not yet trained)

    See: docs/plans/LEVEL-2-MLOPS.md — "FastAPI Model Serving → load_models"
    """
    raise NotImplementedError(
        "Implement MLflow model loading. See docs/plans/LEVEL-2-MLOPS.md."
    )


@app.post("/predict/{project_name}")
async def predict(project_name: str, request: PredictionRequest):
    """
    Run inference for a specific project.

    Input:  chip_id from Level 0 catalog (fetches data from MinIO)
    Output: Prediction metadata + MinIO key for prediction raster

    Implementation:
    1. Validate project_name exists in models dict
    2. Load chip from MinIO via TileStore.load_chip(request.chip_id)
    3. Preprocess chip for this project (project-specific normalization)
    4. Run: session.run(None, {"input": chip_array})[0]
    5. Store prediction raster: TileStore.store_chip(prediction_key, prediction)
    6. Insert row into predictions table (PostGIS)
    7. Return prediction metadata

    See: docs/plans/LEVEL-2-MLOPS.md — "predict endpoint"
    """
    if project_name not in PROJECT_NAMES:
        raise HTTPException(404, f"Unknown project '{project_name}'. Valid: {PROJECT_NAMES}")
    session = models.get(project_name)
    if not session:
        raise HTTPException(503, f"Model '{project_name}' not loaded (not yet trained?)")
    raise NotImplementedError("Implement inference pipeline. See docs/plans/LEVEL-2-MLOPS.md.")


@app.get("/predict/{project_name}/latest/{aoi_id}")
async def get_latest_prediction(project_name: str, aoi_id: str):
    """Get the most recent prediction results for an AOI."""
    raise NotImplementedError("Implement: query predictions table ORDER BY run_timestamp DESC LIMIT 1")


@app.get("/predict/{project_name}/history/{aoi_id}")
async def get_prediction_history(project_name: str, aoi_id: str, limit: int = 12):
    """Get historical prediction results for time-series charts."""
    raise NotImplementedError("Implement: query predictions table ORDER BY run_timestamp DESC LIMIT n")


@app.get("/models")
async def list_models():
    """List all loaded models with versions and metrics from MLflow."""
    raise NotImplementedError("Implement: MLflow client.get_latest_versions per project")


@app.get("/models/{project_name}/metrics")
async def get_model_metrics(project_name: str):
    """Return latest evaluation metrics for a project's production model."""
    raise NotImplementedError("Implement: query MLflow run metrics for production model version")


@app.get("/health")
async def health():
    """Health check — reports number of loaded models."""
    return {
        "status": "healthy",
        "models_loaded": len(models),
        "models": list(models.keys()),
    }
