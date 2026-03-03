# Level 2 — MLOps Transformation

## From Notebooks to Production Pipelines

Level 2 converts each validated Level 1 notebook into an automated, versioned, monitored ML pipeline. No more manual re-runs — every model retrains on schedule, gets registered, serves predictions via API, and triggers alerts on drift.

**Duration:** 3-4 weeks
**Prerequisite:** All Level 1 notebooks pass their exit criteria

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LEVEL 2 — MLOps Layer                           │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   Airflow     │    │   MLflow     │    │    FastAPI Model Server   │  │
│  │              │    │              │    │                          │  │
│  │  ┌─────────┐ │    │ Experiment   │    │  /predict/urban-sprawl   │  │
│  │  │ DAG:    │ │    │ Tracking     │    │  /predict/green-riyadh   │  │
│  │  │ ingest  │─┼───►│              │    │  /predict/crop-mapping   │  │
│  │  │ train   │ │    │ Model        │    │  /predict/groundwater    │  │
│  │  │ eval    │ │    │ Registry     │◄──►│  /predict/desertification│  │
│  │  │ deploy  │ │    │              │    │  /predict/neom           │  │
│  │  │ monitor │ │    │ Artifact     │    │  /predict/flood-risk     │  │
│  │  └─────────┘ │    │ Store        │    │  /predict/oil-spill      │  │
│  └──────┬───────┘    └──────────────┘    │  /predict/dune-migration │  │
│         │                                 └────────────┬─────────────┘  │
│         │                                              │                │
│  ┌──────▼──────────────────────────────────────────────▼──────────────┐ │
│  │                    Shared Infrastructure                            │ │
│  │  PostgreSQL+PostGIS │ MinIO │ Redis │ Prometheus │ Grafana         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Notebook → Production Conversion

Each notebook becomes **4 production components:**

| Notebook Component | Production Component | Location |
|-------------------|---------------------|----------|
| Data loading cells | **Airflow ingestion DAG task** | `mlops/dags/` |
| Training cells | **Training script** (argparse CLI) | `mlops/training/` |
| Evaluation cells | **Evaluation script** + MLflow logging | `mlops/evaluation/` |
| Inference cells | **FastAPI endpoint** + ONNX runtime | `mlops/serving/` |

### Conversion Checklist (Per Project)

```
For each of the 9 projects:
  □ Extract data loading into standalone Python module
  □ Extract preprocessing into reusable functions (shared/)
  □ Convert training notebook to CLI script with argparse/hydra config
  □ Add MLflow experiment tracking (log params, metrics, artifacts)
  □ Export trained model to ONNX format
  □ Register model in MLflow Model Registry
  □ Create FastAPI endpoint that loads ONNX model and serves predictions
  □ Create Airflow DAG that orchestrates: ingest → train → eval → deploy
  □ Add data validation checks (Great Expectations or custom)
  □ Add model performance monitoring (drift detection)
```

---

## Airflow DAGs

### DAG per Project

Each project has one Airflow DAG with this structure:

```python
# Example: dags/urban_sprawl_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'saudi-sentinel-ai',
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'urban_sprawl_pipeline',
    default_args=default_args,
    schedule_interval='0 6 */5 * *',  # Every 5 days (Sentinel-2 revisit)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['green-light', 'sentinel-2', 'urban'],
) as dag:

    check_new_data = PythonOperator(
        task_id='check_new_tiles',
        python_callable=check_new_sentinel2_tiles,
        op_kwargs={'aoi': 'riyadh-metro', 'sensor': 's2'},
    )

    preprocess = PythonOperator(
        task_id='preprocess_tiles',
        python_callable=preprocess_for_urban_sprawl,
    )

    run_inference = PythonOperator(
        task_id='run_inference',
        python_callable=run_model_inference,
        op_kwargs={'model_name': 'urban-sprawl-siamese-unet', 'stage': 'Production'},
    )

    validate_output = PythonOperator(
        task_id='validate_predictions',
        python_callable=validate_prediction_quality,
    )

    store_results = PythonOperator(
        task_id='store_results',
        python_callable=store_predictions_postgis,
    )

    notify = PythonOperator(
        task_id='send_alerts',
        python_callable=check_and_alert,  # Alert if significant change detected
    )

    check_new_data >> preprocess >> run_inference >> validate_output >> store_results >> notify
```

### DAG Schedule Summary

| Project | Schedule | Trigger |
|---------|----------|---------|
| Urban Sprawl | Every 5 days | New S2 tiles available |
| Green Riyadh | Monthly | Monthly composite ready |
| Crop Mapping | Seasonal (4×/year) | Full quarter of data accumulated |
| Groundwater | Annual | Peak-season composite (Feb–Apr) |
| Desertification | Quarterly | Updated feature vectors |
| NEOM Tracker | Every 5 days | New S1+S2 tiles |
| Sand Dune | Quarterly | Quarterly SAR composite |
| Flash Flood | On-demand + annual | SAR scene with reported rainfall; annual risk update |
| Oil Spill | Every 6 days | Every new S1 scene over Arabian Gulf |

### Retraining DAGs (Separate)

Monthly or quarterly retraining DAGs that:
1. Pull latest labeled data (including any new manual annotations)
2. Retrain model with updated data
3. Evaluate against held-out test set
4. If metrics improve → promote to MLflow "Staging"
5. Run shadow inference alongside production model
6. If shadow model outperforms for 2 weeks → promote to "Production"

---

## MLflow Integration

### Experiment Structure

```
MLflow Experiments:
├── urban-sprawl-detector/
│   ├── run-2024-03-15-baseline-rf        # Random Forest baseline
│   ├── run-2024-03-18-siamese-unet-v1    # First U-Net attempt
│   ├── run-2024-03-22-siamese-unet-v2    # Tuned hyperparameters
│   └── run-2024-04-01-siamese-unet-v3    # New training data
├── green-riyadh-monitor/
│   └── ...
├── crop-type-mapping/
│   └── ...
└── ... (9 experiments total)
```

### What Gets Logged Per Run

```python
import mlflow

with mlflow.start_run(experiment_id="urban-sprawl-detector"):
    # Parameters
    mlflow.log_params({
        "model": "siamese-unet",
        "backbone": "resnet34",
        "lr": 1e-4,
        "batch_size": 16,
        "epochs": 50,
        "loss": "bce+dice",
        "train_chips": 1400,
        "val_chips": 300,
        "aois": "riyadh,jeddah,dammam",
    })
    
    # Metrics
    mlflow.log_metrics({
        "val_iou": 0.68,
        "val_f1": 0.72,
        "val_precision": 0.76,
        "val_recall": 0.68,
        "val_far": 0.12,
        "inference_time_ms": 45,
    })
    
    # Artifacts
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.log_artifact("sample_predictions.png")
    mlflow.log_artifact("training_curves.png")
    
    # Model
    mlflow.pytorch.log_model(model, "model")
    mlflow.onnx.log_model(onnx_model, "model-onnx")
```

### Model Registry Stages

```
None → Staging → Production → Archived

Promotion rules:
  Staging → Production:
    - val_iou > 0.65 (project-specific threshold)
    - Inference time < 100ms per chip
    - Shadow deployment for 2 weeks shows no regression
    - Human approval (for yellow-light projects)
```

---

## FastAPI Model Serving

### Unified Serving Architecture

One FastAPI application serves all 9 models. Each model is loaded as an ONNX runtime session.

```python
# mlops/serving/main.py

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
import onnxruntime as ort

app = FastAPI(title="Saudi Sentinel AI - Model Server", version="2.0")

# Model registry - loaded at startup
models = {}

@app.on_event("startup")
async def load_models():
    """Load production models from MLflow registry."""
    model_names = [
        "urban-sprawl", "green-riyadh", "crop-mapping", "groundwater",
        "desertification", "neom-tracker", "dune-migration", 
        "flash-flood", "oil-spill"
    ]
    for name in model_names:
        model_path = get_production_model_path(name)  # From MLflow
        if model_path:
            models[name] = ort.InferenceSession(model_path)

@app.post("/predict/{project_name}")
async def predict(project_name: str, request: PredictionRequest):
    """
    Run inference for a specific project.
    
    Input: GeoTIFF chip (as bytes) or chip_id (from catalog)
    Output: Prediction GeoTIFF + metadata
    """
    session = models.get(project_name)
    if not session:
        raise HTTPException(404, f"Model '{project_name}' not loaded")
    
    chip = load_chip(request.chip_id)  # From MinIO
    prediction = session.run(None, {"input": chip})[0]
    
    result_key = store_prediction(project_name, request.chip_id, prediction)
    
    return {
        "project": project_name,
        "chip_id": request.chip_id,
        "prediction_key": result_key,
        "metadata": extract_metadata(prediction, project_name),
    }

@app.get("/predict/{project_name}/latest/{aoi_id}")
async def get_latest_prediction(project_name: str, aoi_id: str):
    """Get the most recent prediction results for an AOI."""
    return query_latest_prediction(project_name, aoi_id)

@app.get("/models")
async def list_models():
    """List all loaded models with their versions and metrics."""
    return {name: get_model_info(name) for name in models}

@app.get("/health")
async def health():
    return {"status": "healthy", "models_loaded": len(models)}
```

### API Endpoints Summary

```
POST /predict/{project_name}              # Run inference on a chip
GET  /predict/{project_name}/latest/{aoi} # Get latest results for AOI
GET  /predict/{project_name}/history/{aoi} # Get historical results
GET  /models                               # List loaded models + versions
GET  /models/{project_name}/metrics        # Model performance metrics
GET  /health                               # Health check
```

---

## Monitoring & Drift Detection

### What to Monitor

| Category | Metric | Alert Threshold |
|----------|--------|----------------|
| **Data** | New tiles received per AOI per week | < 1 tile = data pipeline failure |
| **Data** | Cloud coverage % | > 80% for 3 consecutive acquisitions |
| **Model** | Prediction distribution shift | KL divergence > 0.1 from baseline |
| **Model** | % of high-confidence predictions | Drop > 15% from rolling average |
| **Model** | Inference latency p95 | > 200ms |
| **System** | GPU memory usage | > 90% |
| **System** | API error rate | > 5% |
| **Business** | Change detection area per run | Sudden spike (10× normal) = likely error |

### Drift Detection Strategy

```python
# For each prediction run, compare against historical distribution

class DriftDetector:
    def check_prediction_drift(self, project: str, new_predictions: np.ndarray):
        """
        Compare new prediction distribution against 
        rolling 30-day baseline using PSI (Population Stability Index).
        """
        baseline = self.get_baseline_distribution(project, days=30)
        psi = self.compute_psi(baseline, new_predictions)
        
        if psi > 0.2:  # Significant drift
            self.alert(project, "CRITICAL", f"PSI={psi:.3f}")
        elif psi > 0.1:  # Moderate drift
            self.alert(project, "WARNING", f"PSI={psi:.3f}")
```

---

## Docker Configuration

### `docker/docker-compose.level2.yml`

```yaml
version: '3.8'

services:
  # --- Inherits Level 0 services (postgres, minio, redis) ---

  airflow-webserver:
    build:
      context: ..
      dockerfile: docker/mlops.Dockerfile
    command: airflow webserver
    ports:
      - "8080:8080"
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://airflow:${AIRFLOW_DB_PASSWORD}@postgres:5432/airflow
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
    volumes:
      - ../mlops/dags:/opt/airflow/dags
      - ../mlops/training:/opt/airflow/training
      - ../shared:/opt/airflow/shared
    depends_on:
      - postgres
      - minio

  airflow-scheduler:
    build:
      context: ..
      dockerfile: docker/mlops.Dockerfile
    command: airflow scheduler
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://airflow:${AIRFLOW_DB_PASSWORD}@postgres:5432/airflow
    volumes:
      - ../mlops/dags:/opt/airflow/dags
      - ../mlops/training:/opt/airflow/training
      - ../shared:/opt/airflow/shared
    depends_on:
      - postgres

  mlflow:
    build:
      context: ..
      dockerfile: docker/mlops.Dockerfile
    command: >
      mlflow server 
      --backend-store-uri postgresql://mlflow:${MLFLOW_DB_PASSWORD}@postgres:5432/mlflow
      --default-artifact-root s3://mlflow-artifacts/
      --host 0.0.0.0 --port 5000
    ports:
      - "5000:5000"
    environment:
      AWS_ACCESS_KEY_ID: ${MINIO_USER}
      AWS_SECRET_ACCESS_KEY: ${MINIO_PASSWORD}
      MLFLOW_S3_ENDPOINT_URL: http://minio:9000
    depends_on:
      - postgres
      - minio

  model-server:
    build:
      context: ..
      dockerfile: docker/mlops.Dockerfile
    command: uvicorn mlops.serving.main:app --host 0.0.0.0 --port 8200
    ports:
      - "8200:8200"
    environment:
      MLFLOW_TRACKING_URI: http://mlflow:5000
      MINIO_ENDPOINT: minio:9000
      DATABASE_URL: postgresql://sentinel:${POSTGRES_PASSWORD}@postgres:5432/sentinel_catalog
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - mlflow
      - postgres
      - minio

  prometheus:
    image: prom/prometheus:v2.48.0
    ports:
      - "9090:9090"
    volumes:
      - ../monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - ../monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
```

### `docker/mlops.Dockerfile`

```dockerfile
FROM python:3.11-slim

# System deps for geospatial
RUN apt-get update && apt-get install -y \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Python deps
COPY mlops/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy code
COPY shared/ /app/shared/
COPY mlops/ /app/mlops/

WORKDIR /app
ENV PYTHONPATH=/app
```

### `mlops/requirements.txt`

```
# Orchestration
apache-airflow==2.8.1
# Experiment tracking
mlflow==2.10.0
# Serving
fastapi==0.109.0
uvicorn==0.27.0
onnxruntime-gpu==1.17.0
# Geospatial
rasterio==1.3.9
geopandas==0.14.2
shapely==2.0.2
# ML
torch==2.2.0
scikit-learn==1.4.0
xgboost==2.0.3
# Data
numpy==1.26.3
pandas==2.2.0
# Storage
minio==7.2.3
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
redis==5.0.1
# Monitoring
prometheus-client==0.19.0
```

---

## PostGIS Schema Extensions (for predictions)

```sql
-- Prediction results table (one row per chip per run)
CREATE TABLE predictions (
    prediction_id   SERIAL PRIMARY KEY,
    project_name    VARCHAR(64),
    chip_id         VARCHAR(256) REFERENCES chips(chip_id),
    model_version   VARCHAR(128),
    run_timestamp   TIMESTAMP,
    prediction_key  VARCHAR(512),  -- MinIO key for prediction raster
    summary_stats   JSONB,         -- Project-specific summary (e.g., % changed, area_ha)
    confidence      FLOAT,
    geometry        GEOMETRY(Polygon, 4326),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pred_project ON predictions(project_name, run_timestamp DESC);
CREATE INDEX idx_pred_geom ON predictions USING GIST(geometry);

-- Alerts table
CREATE TABLE alerts (
    alert_id        SERIAL PRIMARY KEY,
    project_name    VARCHAR(64),
    alert_type      VARCHAR(32),  -- 'change_detected', 'drift_warning', 'data_gap', etc.
    severity        VARCHAR(16),  -- 'info', 'warning', 'critical'
    message         TEXT,
    aoi_id          VARCHAR(64),
    geometry        GEOMETRY(Point, 4326),
    acknowledged    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## Rollout Strategy

### Phase 1: Green Light Projects (Week 1-2)
Convert the 5 green-light notebooks first. These have the simplest models and most reliable data pipelines.

**Order of conversion:**
1. Groundwater Depletion (simplest — thresholding + basic AE)
2. Green Riyadh (NDVI compositing is straightforward)
3. Urban Sprawl (U-Net is well-understood)
4. Desertification Warning (XGBoost exports cleanly)
5. Crop Type Mapping (most complex of the green-lights)

### Phase 2: Yellow Light Projects (Week 3-4)
Convert with additional safeguards (human-in-the-loop, higher alert thresholds).

**Order of conversion:**
6. NEOM Tracker (add confidence-based filtering)
7. Flash Flood Risk (annual model update only, on-demand inference)
8. Sand Dune Migration (quarterly updates)
9. Oil Spill Detection (add mandatory human verification step before alert)

---

## Success Criteria

- [ ] All 9 Airflow DAGs running on schedule without manual intervention
- [ ] MLflow tracks all model versions; at least 2 versions per project registered
- [ ] FastAPI model server serves all 9 projects with < 100ms latency (p95)
- [ ] Prometheus collects metrics; Grafana dashboards show pipeline health
- [ ] Drift detection triggers alerts correctly (test with synthetic drift)
- [ ] Automated retraining promotes better model to production at least once
- [ ] Full pipeline (ingest → predict → store → alert) runs end-to-end for at least 3 projects
