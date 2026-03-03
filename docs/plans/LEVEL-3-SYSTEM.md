# Level 3 — Full System

## Production-Grade Saudi Sentinel AI Platform

Level 3 integrates all 9 MLOps pipelines into a unified system with a React frontend, FastAPI gateway, real-time alerting, and operational monitoring. This is the customer-facing product.

**Duration:** 4-6 weeks
**Prerequisite:** Level 2 MLOps running for at least 2 weeks with stable pipelines

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USERS                                          │
│          Analysts    │    Decision Makers    │    API Consumers              │
└──────────┬──────────────────┬──────────────────────┬────────────────────────┘
           │                  │                      │
           ▼                  ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                                     │
│                                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  ┌────────────────────┐  │
│  │  Map View   │  │  Project     │  │  Alert    │  │  Admin / Settings  │  │
│  │  (Deck.gl)  │  │  Dashboards  │  │  Center   │  │                    │  │
│  │             │  │  (per model) │  │           │  │  Model versions    │  │
│  │  Layers:    │  │              │  │  Active   │  │  Pipeline status   │  │
│  │  - Urban    │  │  Charts      │  │  History  │  │  AOI management    │  │
│  │  - Veg      │  │  Trends      │  │  Filters  │  │  User management   │  │
│  │  - Crops    │  │  Comparisons │  │           │  │                    │  │
│  │  - Floods   │  │              │  │           │  │                    │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬─────┘  └────────┬───────────┘  │
└─────────┼────────────────┼────────────────┼───────────────────┼──────────────┘
          │                │                │                   │
          └────────────────┼────────────────┼───────────────────┘
                           ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY (FastAPI)                                   │
│                                                                              │
│  /api/v1/projects           → List projects, status, latest results          │
│  /api/v1/projects/{id}/map  → GeoJSON prediction layers for map              │
│  /api/v1/projects/{id}/stats → Time-series statistics                        │
│  /api/v1/alerts              → Active alerts, history, acknowledge           │
│  /api/v1/tiles/{z}/{x}/{y}  → Tile server for prediction rasters             │
│  /api/v1/compare             → Side-by-side before/after imagery             │
│  /api/v1/reports             → Generate PDF/CSV reports per AOI              │
│  /api/v1/admin/pipelines     → Pipeline status, trigger reruns               │
│  /api/v1/admin/models        → Model registry, version management            │
│  /api/v1/ws/alerts           → WebSocket for real-time alert push            │
│                                                                              │
│  Auth: JWT tokens  │  Rate limiting: Redis  │  CORS: configured              │
└──────────┬──────────────────┬──────────────────────┬─────────────────────────┘
           │                  │                      │
    ┌──────▼──────┐   ┌──────▼──────┐       ┌───────▼──────┐
    │ Model Server │   │  PostGIS   │       │   MinIO      │
    │ (Level 2)    │   │  (catalog  │       │   (tiles +   │
    │              │   │   + preds) │       │   predictions)│
    └──────────────┘   └────────────┘       └──────────────┘
```

---

## React Frontend

### Tech Stack

| Technology | Purpose |
|-----------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Deck.gl** | WebGL-powered geospatial visualization |
| **Mapbox GL JS** | Base map tiles (free tier: 50k loads/month) |
| **Recharts** | Time-series charts and statistics |
| **TanStack Query** | Server state management + caching |
| **Zustand** | Client state management |
| **Tailwind CSS** | Styling |
| **Vite** | Build tool |

### Page Structure

```
App
├── /                           → Landing / Overview Dashboard
├── /map                        → Full-screen interactive map (all projects)
├── /projects                   → Project grid with status cards
├── /projects/:id               → Individual project dashboard
│   ├── /projects/:id/map       → Project-specific map view
│   ├── /projects/:id/trends    → Time-series analysis
│   └── /projects/:id/reports   → Downloadable reports
├── /alerts                     → Alert center (active + history)
├── /compare                    → Before/after comparison tool
├── /admin                      → System administration
│   ├── /admin/pipelines        → Airflow pipeline status
│   ├── /admin/models           → MLflow model registry view
│   └── /admin/aois             → AOI management
└── /api-docs                   → Interactive API documentation
```

### Key UI Components

#### 1. Interactive Map View (Main Screen)

```
┌─────────────────────────────────────────────────┐
│  Saudi Sentinel AI          [Projects ▼] [🔔 3] │
├────────┬────────────────────────────────────────┤
│        │                                         │
│ Layer  │         ┌──────────────┐                │
│ Panel  │         │   RIYADH     │                │
│        │         │  ┌────┐      │                │
│ ☑ Urban│         │  │2024│      │                │
│ ☑ Veg  │    ┌────┘  └────┘ ─────┘                │
│ ☐ Crops│    │                                    │
│ ☐ Flood│    │     Saudi Arabia                   │
│        │    │         Map                        │
│ ──────│    │                                    │
│ Date:  │    │    ┌──────────────┐                │
│ [2024] │    │    │  AL-JOUF     │                │
│        │    │    │  Farms       │                │
│ Opacity│    │    └──────────────┘                │
│ [═══╸] │    │                                    │
│        │                                         │
├────────┴────────────────────────────────────────┤
│  Riyadh: +2.3 km² urban expansion (last 30d)    │
│  Al-Jouf: 12 farms inactive (annual)            │
└─────────────────────────────────────────────────┘
```

- **Deck.gl layers:** Each project is a toggleable GeoJSON/raster tile layer
- **Color schemes:**
  - Urban Sprawl: Red (new construction), Gray (unchanged)
  - Green Riyadh: Green gradient (SAVI intensity)
  - Crop Mapping: Color per crop type
  - Groundwater: Red (abandoned), Green (active), Yellow (at-risk)
  - Desertification: Red-Yellow-Green risk heatmap
  - NEOM: Phase-colored construction corridor
  - Flood Risk: Blue gradient (flood probability)
  - Oil Spill: Red markers for detected anomalies

#### 2. Project Dashboard

```
┌───────────────────────────────────────────────────┐
│  Urban Sprawl Detector         Model v2.3  [Live] │
├───────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────┐  ┌────────────────────┐ │
│  │ Total Change (2024)  │  │ Pipeline Status    │ │
│  │                      │  │                    │ │
│  │  +14.7 km²           │  │ Last run: 2h ago  │ │
│  │  ▲ 8% vs 2023       │  │ Status: ✅ Success │ │
│  └──────────────────────┘  └────────────────────┘ │
│                                                    │
│  Monthly Change Trend (2019–2024)                  │
│  ┌─────────────────────────────────────────────┐  │
│  │     ╱──╲        ╱──╲    ╱──╲    ╱──╲        │  │
│  │ ───╱    ╲──────╱    ╲──╱    ╲──╱    ╲───── │  │
│  │  J  F  M  A  M  J  J  A  S  O  N  D       │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  Per-City Breakdown                                │
│  ┌──────────┬──────────┬──────────┐               │
│  │ Riyadh   │ Jeddah   │ Dammam   │               │
│  │ +8.2 km² │ +3.9 km² │ +2.6 km² │               │
│  │ ▲ 12%   │ ▲ 5%    │ ▲ 3%    │               │
│  └──────────┴──────────┴──────────┘               │
│                                                    │
│  [📊 Download Report]  [🗺️ View on Map]           │
└───────────────────────────────────────────────────┘
```

#### 3. Alert Center

```
┌───────────────────────────────────────────────────┐
│  Alert Center                    [Filter ▼] [All] │
├───────────────────────────────────────────────────┤
│                                                    │
│  🔴 CRITICAL — Oil Spill Detected                 │
│     Arabian Gulf, 26.4°N 50.2°E                   │
│     Confidence: 72% │ 2 hours ago │ [View] [Ack]  │
│                                                    │
│  🟡 WARNING — Unusual Urban Change Spike           │
│     Riyadh South, 24.5°N 46.8°E                   │
│     +340% above normal │ 6 hours ago │ [View]     │
│                                                    │
│  🟢 INFO — NEOM Construction Progress Update       │
│     +2.3 km² cleared this week                    │
│     12 hours ago │ [View]                          │
│                                                    │
│  🟡 WARNING — Model Drift Detected                 │
│     Crop Mapping — PSI: 0.14                      │
│     1 day ago │ [View] [Retrigger Training]        │
│                                                    │
└───────────────────────────────────────────────────┘
```

---

## API Gateway (FastAPI)

### Core Endpoints

```python
# system/api-gateway/main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Saudi Sentinel AI", version="3.0")

# --- Project Endpoints ---

@app.get("/api/v1/projects")
async def list_projects():
    """All 9 projects with status, latest metrics, last run time."""
    
@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Detailed project info: model version, pipeline status, AOIs."""

@app.get("/api/v1/projects/{project_id}/map")
async def get_project_map_layer(
    project_id: str,
    aoi_id: str = None,
    date_from: str = None,
    date_to: str = None,
):
    """GeoJSON FeatureCollection for map rendering."""

@app.get("/api/v1/projects/{project_id}/stats")
async def get_project_stats(project_id: str, aoi_id: str = None):
    """Time-series statistics for charts."""

@app.get("/api/v1/projects/{project_id}/reports")
async def generate_report(project_id: str, format: str = "pdf"):
    """Generate downloadable report."""

# --- Map Tile Endpoints ---

@app.get("/api/v1/tiles/{project_id}/{z}/{x}/{y}.png")
async def get_map_tile(project_id: str, z: int, x: int, y: int):
    """Raster tile server for prediction overlays (XYZ tile scheme)."""

# --- Alert Endpoints ---

@app.get("/api/v1/alerts")
async def list_alerts(
    severity: str = None,
    project_id: str = None,
    acknowledged: bool = None,
):
    """List alerts with optional filters."""

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Mark alert as acknowledged."""

@app.websocket("/api/v1/ws/alerts")
async def alert_websocket(websocket: WebSocket):
    """Real-time alert push via WebSocket."""

# --- Compare Endpoints ---

@app.get("/api/v1/compare/{aoi_id}")
async def get_comparison(aoi_id: str, date_a: str, date_b: str):
    """Side-by-side satellite imagery + predictions for two dates."""

# --- Admin Endpoints ---

@app.get("/api/v1/admin/pipelines")
async def list_pipelines():
    """Proxy to Airflow: DAG status, last runs, next scheduled."""

@app.post("/api/v1/admin/pipelines/{dag_id}/trigger")
async def trigger_pipeline(dag_id: str):
    """Manually trigger an Airflow DAG."""

@app.get("/api/v1/admin/models")
async def list_models():
    """Proxy to MLflow: registered models, versions, stages."""

@app.post("/api/v1/admin/models/{model_name}/promote")
async def promote_model(model_name: str, from_stage: str, to_stage: str):
    """Promote model version in MLflow registry."""
```

### Tile Server Implementation

For serving prediction rasters as map tiles, use a dynamic tile renderer:

```python
# system/api-gateway/tile_server.py

import rasterio
from rasterio.warp import transform_bounds
from PIL import Image
import mercantile

async def render_tile(project_id: str, z: int, x: int, y: int) -> bytes:
    """
    Render a PNG map tile from prediction raster in MinIO.
    
    1. Convert XYZ tile coords to geographic bounds
    2. Find prediction rasters that intersect these bounds (from PostGIS)
    3. Read relevant portion of raster from MinIO
    4. Apply project-specific colormap
    5. Return as PNG bytes
    """
    bounds = mercantile.bounds(x, y, z)
    
    # Query PostGIS for prediction rasters intersecting tile bounds
    rasters = query_predictions_for_bounds(project_id, bounds)
    
    # Read and mosaic raster data
    tile_data = read_and_mosaic(rasters, bounds, tile_size=256)
    
    # Apply colormap
    colormap = COLORMAPS[project_id]
    colored = colormap(tile_data)
    
    # Encode as PNG
    return encode_png(colored)

COLORMAPS = {
    "urban-sprawl": lambda d: red_gray_colormap(d),
    "green-riyadh": lambda d: green_gradient(d),
    "crop-mapping": lambda d: categorical_colormap(d, CROP_COLORS),
    "groundwater": lambda d: traffic_light_colormap(d),
    "desertification": lambda d: risk_heatmap(d),
    "neom-tracker": lambda d: construction_phase_colormap(d),
    "flash-flood": lambda d: blue_gradient(d),
    "oil-spill": lambda d: binary_red_colormap(d),
    "dune-migration": lambda d: arrow_field_colormap(d),
}
```

---

## Docker Configuration

### `docker/docker-compose.level3.yml`

```yaml
version: '3.8'

services:
  # --- Inherits all Level 0 + Level 2 services ---

  api-gateway:
    build:
      context: ..
      dockerfile: docker/system.Dockerfile
    command: uvicorn system.api_gateway.main:app --host 0.0.0.0 --port 8300
    ports:
      - "8300:8300"
    environment:
      DATABASE_URL: postgresql://sentinel:${POSTGRES_PASSWORD}@postgres:5432/sentinel_catalog
      MINIO_ENDPOINT: minio:9000
      MODEL_SERVER_URL: http://model-server:8200
      MLFLOW_TRACKING_URI: http://mlflow:5000
      AIRFLOW_API_URL: http://airflow-webserver:8080
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - postgres
      - minio
      - redis
      - model-server

  frontend:
    build:
      context: ../system/frontend
      dockerfile: Dockerfile
    ports:
      - "3001:80"
    environment:
      REACT_APP_API_URL: http://localhost:8300
      REACT_APP_MAPBOX_TOKEN: ${MAPBOX_TOKEN}
    depends_on:
      - api-gateway

  # Real-time alert worker
  alert-worker:
    build:
      context: ..
      dockerfile: docker/system.Dockerfile
    command: python system/alerts/worker.py
    environment:
      DATABASE_URL: postgresql://sentinel:${POSTGRES_PASSWORD}@postgres:5432/sentinel_catalog
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
```

---

## Alerting System

### Alert Types & Rules

```python
# system/alerts/rules.py

ALERT_RULES = {
    "urban-sprawl": {
        "significant_change": {
            "condition": "change_area_km2 > 0.5",  # 0.5 km² in one pass
            "severity": "info",
            "message": "New urban expansion detected: {change_area_km2:.1f} km²"
        },
        "abnormal_spike": {
            "condition": "change_area_km2 > (rolling_avg_30d * 3)",
            "severity": "warning",
            "message": "Unusual urban change spike: {ratio:.1f}× above normal"
        },
    },
    "green-riyadh": {
        "vegetation_loss": {
            "condition": "ndvi_change < -0.05 over 3 months",
            "severity": "warning",
            "message": "Vegetation decline detected in {district}: ΔNDVI = {change:.3f}"
        },
        "greening_milestone": {
            "condition": "green_area_km2 crosses threshold",
            "severity": "info",
            "message": "Green cover milestone: {green_area_km2:.1f} km² (target: X)"
        },
    },
    "groundwater": {
        "farm_abandoned": {
            "condition": "farm inactive for 2+ consecutive years",
            "severity": "warning",
            "message": "{count} farms appear abandoned in {region}"
        },
    },
    "oil-spill": {
        "spill_detected": {
            "condition": "confidence > 0.65 AND wind_speed > 3",
            "severity": "critical",
            "message": "Potential oil spill at {lat:.4f}°N {lon:.4f}°E (confidence: {conf:.0%})"
        },
    },
    "desertification": {
        "high_risk_expansion": {
            "condition": "high_risk_area_km2 increased > 10% quarterly",
            "severity": "warning",
            "message": "Desertification risk expanding in {region}: +{pct:.0%} high-risk area"
        },
    },
}
```

### Alert Worker

```python
# system/alerts/worker.py

"""
Runs continuously. Polls prediction results from PostGIS.
Evaluates alert rules. Pushes alerts to WebSocket subscribers + stores in DB.
"""

import asyncio
from datetime import datetime, timedelta

class AlertWorker:
    async def run(self):
        while True:
            for project in ALERT_RULES:
                new_predictions = await self.get_unprocessed_predictions(project)
                for pred in new_predictions:
                    alerts = self.evaluate_rules(project, pred)
                    for alert in alerts:
                        await self.store_alert(alert)
                        await self.push_to_websocket(alert)
                        if alert.severity == "critical":
                            await self.send_email(alert)
            
            await asyncio.sleep(60)  # Check every minute
```

---

## Deployment Topology

### Development (Single Machine)

```
Docker Compose with all services on one machine.
Minimum specs: 32GB RAM, GPU (RTX 3080+), 500GB SSD
```

### Production (Recommended)

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│ Frontend (CDN)  │────►│ API Gateway  │────►│ Model Server │
│ Vercel/CF Pages │     │ 2× instances │     │ 1× GPU       │
└─────────────────┘     │ behind LB    │     │ instance     │
                        └──────┬───────┘     └──────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌──────────┐ ┌──────────┐ ┌──────────────┐
          │ PostGIS  │ │ MinIO/S3 │ │ Airflow      │
          │ (managed │ │ (or AWS  │ │ (single node │
          │  RDS)    │ │  S3)     │ │  or managed) │
          └──────────┘ └──────────┘ └──────────────┘
```

### Cloud Cost Estimate (AWS)

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| EC2 (GPU, model serving) | g4dn.xlarge | ~$150 |
| EC2 (API + Airflow) | t3.xlarge | ~$120 |
| RDS PostgreSQL | db.t3.medium | ~$60 |
| S3 (tile storage) | ~500 GB | ~$12 |
| CloudFront (frontend CDN) | — | ~$5 |
| **Total** | | **~$350/month** |

---

## Testing Strategy

| Layer | Tool | What to Test |
|-------|------|-------------|
| **Unit** | pytest | Data processing functions, feature engineering, colormap rendering |
| **Integration** | pytest + testcontainers | API ↔ PostGIS, API ↔ MinIO, API ↔ Model Server |
| **E2E** | Playwright | Full user flows: login → view map → toggle layers → download report |
| **Load** | Locust | API gateway handles 100 concurrent users; tile server < 200ms p95 |
| **Model** | Custom | Prediction quality on held-out test set after every retraining |

---

## Success Criteria (Full System)

- [ ] React frontend loads in < 3 seconds
- [ ] Map renders 9 project layers simultaneously without lag
- [ ] Tile server returns tiles in < 200ms (p95)
- [ ] API gateway handles 100 concurrent requests
- [ ] WebSocket alerts arrive within 60 seconds of prediction completion
- [ ] Reports generate as PDF in < 10 seconds
- [ ] All 9 projects show data on dashboard with latest predictions
- [ ] Admin panel shows real-time Airflow pipeline status
- [ ] User authentication works (JWT-based)
- [ ] System runs unattended for 30 days without manual intervention
- [ ] Documentation covers deployment, configuration, and troubleshooting

---

## Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Review alerts and acknowledge | Daily | Analyst |
| Check pipeline health in Grafana | Daily | DevOps |
| Review model drift reports | Weekly | ML Engineer |
| Update AOI definitions if needed | Monthly | GIS Analyst |
| Retrain models with new annotations | Quarterly | ML Engineer |
| Dependency updates (security) | Monthly | DevOps |
| Full system backup test | Quarterly | DevOps |
| Performance benchmarking | Quarterly | Backend Engineer |
