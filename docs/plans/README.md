# Saudi Sentinel AI — Master Plan

## Production-Grade Earth Observation AI Platform for Saudi Arabia

A multi-project AI system built on **free Copernicus/Sentinel satellite data**, designed to monitor environmental, urban, and agricultural changes across Saudi Arabia. The platform progresses through four levels, from exploratory notebooks to a fully integrated production system.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEVEL 3 — FULL SYSTEM                        │
│  React Dashboard + FastAPI Gateway + Unified Monitoring          │
│  All models served, all outputs visualized, all pipelines tracked│
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    LEVEL 2 — MLOps                               │
│  Airflow Orchestration + MLflow Registry + FastAPI Serving       │
│  Automated retraining, versioned models, inference endpoints     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    LEVEL 1 — NOTEBOOKS                           │
│  9 Jupyter notebooks (5 green + 4 yellow)                        │
│  Exploration, prototyping, baseline model training               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    LEVEL 0 — DATA PIPELINE                       │
│  Shared Sentinel data ingestion, tiling, storage, catalog        │
│  Single source of truth for all projects                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Inventory

### ✅ Green Light — Production Ready

| # | Project | Sentinel Source | AI Technique | Saudi AOI |
|---|---------|----------------|--------------|-----------|
| 1 | Urban Sprawl Detector | S2 (10m optical) | U-Net change detection | Riyadh, Jeddah, Dammam |
| 2 | Green Riyadh Vegetation Monitor | S2 (10m optical) | NDVI time-series + LSTM | Riyadh metro |
| 3 | Crop Type Mapping | S2 (10m optical) | Temporal CNN classifier | Al-Jouf, Tabuk, Hail |
| 4 | Groundwater Depletion Tracker | S2 (10m optical) | Binary change detection | Central Saudi pivot farms |
| 5 | Desertification Early Warning | S1 + S2 fusion | XGBoost / RF risk scoring | Agricultural margins |

### ⚠️ Yellow Light — Feasible with Caveats

| # | Project | Sentinel Source | AI Technique | Caveat |
|---|---------|----------------|--------------|--------|
| 6 | NEOM Construction Tracker | S1 + S2 | Change detection CNN | Coarse-grained only (10m) |
| 7 | Sand Dune Migration Predictor | S1 SAR | ConvLSTM | Self-generated labels needed |
| 8 | Flash Flood Risk Mapping | S1 SAR | Segmentation + risk model | Post-event only, not real-time |
| 9 | Oil Spill Detection | S1 SAR | DeepLabV3+ segmentation | High false-positive rate |

---

## Recommended Tech Stack

### Why This Stack (for production)

| Layer | Tool | Why |
|-------|------|-----|
| **Orchestration** | Apache Airflow | Industry standard for scheduled data pipelines; Sentinel data is inherently time-scheduled (5-day revisit) |
| **Experiment Tracking** | MLflow | Model versioning, metric logging, artifact storage; integrates with any framework |
| **Model Registry** | MLflow Model Registry | Stage transitions (staging → production), model lineage |
| **Model Serving** | FastAPI + ONNX Runtime | Low-latency inference, async support, GeoJSON input/output |
| **Object Storage** | MinIO (S3-compatible) | Store satellite tiles, model artifacts, inference outputs locally or cloud |
| **Database** | PostgreSQL + PostGIS | Geospatial queries on AOIs, prediction results, metadata catalog |
| **Cache** | Redis | Cache recent inference results, tile lookups |
| **Monitoring** | Prometheus + Grafana | Infrastructure metrics, model performance drift detection |
| **Frontend** | React + Deck.gl + Mapbox | Geospatial visualization, project dashboards |
| **API Gateway** | FastAPI | Unified REST API connecting React frontend to all model services |
| **Containerization** | Docker + Docker Compose | Dev environment; production-ready for K8s migration |
| **CI/CD** | GitHub Actions | Automated testing, Docker builds, deployment |

---

## Level Progression

### Level 0 — Shared Data Pipeline
**Duration:** 1-2 weeks
**Deliverable:** Dockerized data ingestion service + tile catalog in PostGIS
**Doc:** [LEVEL-0-DATA-PIPELINE.md](./LEVEL-0-DATA-PIPELINE.md)

### Level 1 — Notebooks
**Duration:** 6-10 weeks (can parallelize)
**Deliverable:** 9 validated notebooks with trained baseline models
**Docs:**
- [01-urban-sprawl-detector.md](./level-1-notebooks/01-urban-sprawl-detector.md)
- [02-green-riyadh-monitor.md](./level-1-notebooks/02-green-riyadh-monitor.md)
- [03-crop-type-mapping.md](./level-1-notebooks/03-crop-type-mapping.md)
- [04-groundwater-depletion-tracker.md](./level-1-notebooks/04-groundwater-depletion-tracker.md)
- [05-desertification-warning.md](./level-1-notebooks/05-desertification-warning.md)
- [06-neom-construction-tracker.md](./level-1-notebooks/06-neom-construction-tracker.md)
- [07-sand-dune-migration.md](./level-1-notebooks/07-sand-dune-migration.md)
- [08-flash-flood-risk.md](./level-1-notebooks/08-flash-flood-risk.md)
- [09-oil-spill-detection.md](./level-1-notebooks/09-oil-spill-detection.md)

### Level 2 — MLOps
**Duration:** 3-4 weeks
**Deliverable:** All models in Airflow pipelines, MLflow registry, FastAPI endpoints
**Doc:** [LEVEL-2-MLOPS.md](./LEVEL-2-MLOPS.md)

### Level 3 — Full System
**Duration:** 4-6 weeks
**Deliverable:** React dashboard, unified API, monitoring, alerting
**Doc:** [LEVEL-3-SYSTEM.md](./LEVEL-3-SYSTEM.md)

---

## Folder Structure (Final State)

```
saudi-sentinel-ai/
├── docker/
│   ├── notebooks.Dockerfile        # Level 1: JupyterLab + geospatial deps
│   ├── mlops.Dockerfile             # Level 2: Airflow + MLflow + serving
│   ├── system.Dockerfile            # Level 3: React + FastAPI + monitoring
│   └── docker-compose.yml           # Full stack compose
├── data-pipeline/                   # Level 0
│   ├── ingestion/
│   ├── tiling/
│   ├── catalog/
│   └── config/
├── notebooks/                       # Level 1
│   ├── 01-urban-sprawl/
│   ├── 02-green-riyadh/
│   ├── 03-crop-mapping/
│   ├── 04-groundwater/
│   ├── 05-desertification/
│   ├── 06-neom-tracker/
│   ├── 07-dune-migration/
│   ├── 08-flash-flood/
│   └── 09-oil-spill/
├── mlops/                           # Level 2
│   ├── dags/                        # Airflow DAGs
│   ├── training/                    # Training scripts (from notebooks)
│   ├── serving/                     # FastAPI model servers
│   ├── registry/                    # MLflow config
│   └── monitoring/                  # Drift detection
├── system/                          # Level 3
│   ├── frontend/                    # React app
│   ├── api-gateway/                 # Unified FastAPI
│   ├── alerts/                      # Alerting service
│   └── monitoring/                  # Prometheus + Grafana
├── shared/                          # Shared utilities
│   ├── geo_utils/
│   ├── sentinel_client/
│   ├── preprocessing/
│   └── evaluation/
├── tests/
├── docs/
└── README.md
```

---

## Data Access (Zero Cost)

| Source | URL | What You Get |
|--------|-----|-------------|
| Copernicus Data Space | dataspace.copernicus.eu | Sentinel-1, 2, 3, 5P download + API |
| Copernicus Browser | browser.dataspace.copernicus.eu | Visual exploration before download |
| sentinelhub-py | PyPI | Python SDK for programmatic access |
| Google Earth Engine | earthengine.google.com | Free for research; alternative access to Sentinel |
| Microsoft Planetary Computer | planetarycomputer.microsoft.com | Free STAC API access to Sentinel archive |

**Recommended primary source:** Copernicus Data Space (official, no quotas for Sentinel data).
**Recommended secondary source:** Microsoft Planetary Computer (faster API, STAC-compliant, great for bulk jobs).

---

## Team Allocation Recommendation

| Role | Focus |
|------|-------|
| **ML Engineer (1-2)** | Level 1 notebooks → Level 2 model training pipelines |
| **Data Engineer (1)** | Level 0 data pipeline → Level 2 Airflow DAGs |
| **Backend Engineer (1)** | Level 2 FastAPI serving → Level 3 API gateway |
| **Frontend Engineer (1)** | Level 3 React dashboard |
| **DevOps / Platform (1)** | Docker, CI/CD, monitoring, infrastructure |

**Solo developer?** Follow levels sequentially. Expect 4-6 months for full system.
**Team of 3-5?** Parallelize: one person on Level 0+2 infra, others on Level 1 notebooks, converge at Level 3. Expect 2-3 months.
