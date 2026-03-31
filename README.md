# Saudi Sentinel

> Production-grade Earth Observation AI platform for Saudi Arabia, built on free Copernicus/Sentinel satellite data.

---

## Table of Contents

1. [What This Project Is](#what-this-project-is)
2. [Project Map](#project-map)
3. [Prerequisites](#prerequisites)
4. [First-Time Setup](#first-time-setup)
5. [Level 0 — Start Here (Data Pipeline)](#level-0--start-here-data-pipeline)
6. [Level 1 — Notebooks (Your Main Focus)](#level-1--notebooks-your-main-focus)
7. [Level 2 — MLOps (After Notebooks)](#level-2--mlops-after-notebooks)
8. [Level 3 — Full System (Final Stage)](#level-3--full-system-final-stage)
9. [Services & Ports Reference](#services--ports-reference)
10. [Day-to-Day Development Workflow](#day-to-day-development-workflow)
11. [Exit Criteria — How You Know You're Done](#exit-criteria--how-you-know-youre-done)
12. [Repository Layout](#repository-layout)
13. [Plan Documents](#plan-documents)

---

## What This Project Is

Saudi Sentinel is a four-level AI system that monitors Saudi Arabia using satellite imagery:

| Level | Name | What gets built |
|-------|------|-----------------|
| **0** | Data Pipeline | Downloads Sentinel-1/2 tiles, slices them into 256×256 chips, stores them in PostGIS + MinIO |
| **1** | Notebooks | 9 AI projects — each explored and prototyped in Jupyter notebooks |
| **2** | MLOps | Every notebook model is converted into an Airflow pipeline + MLflow-registered ONNX endpoint |
| **3** | Full System | React dashboard + unified API gateway + alerting + Grafana monitoring |

The progression is strict: each level depends on the one below it. **Start at Level 0.**

---

## Project Map

### Green Light (production-ready targets)

| # | Project | What it detects | AOI |
|---|---------|----------------|-----|
| 01 | Urban Sprawl Detector | City boundary growth | Riyadh, Jeddah, Dammam |
| 02 | Green Riyadh Monitor | Vegetation health & NDVI trends | Riyadh metro |
| 03 | Crop Type Mapping | Pivot irrigation, crop classification | Al-Jouf, Tabuk, Hail |
| 04 | Groundwater Depletion Tracker | Farm disappearance = aquifer stress | Central Saudi |
| 05 | Desertification Early Warning | Soil degradation risk scoring | Agricultural margins |

### Yellow Light (feasible with caveats)

| # | Project | What it detects | Caveat |
|---|---------|----------------|--------|
| 06 | NEOM Construction Tracker | Construction change detection | 10m resolution only |
| 07 | Sand Dune Migration | Dune movement velocity | Self-supervised labels |
| 08 | Flash Flood Risk | Flood-prone zone mapping | Post-event, not real-time |
| 09 | Oil Spill Detection | Marine oil slicks | High false-positive rate |

---

## Prerequisites

Install all of these before starting anything:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker Desktop / Docker Engine | 24+ | With Compose v2 (`docker compose`) |
| Git | any | |
| Make | any | Optional — convenience wrapper for `docker compose` commands |
| 30 GB free disk | — | Sentinel tiles are large |
| CDSE Account | — | Free at [dataspace.copernicus.eu](https://dataspace.copernicus.eu) — needed for tile download |
| Mapbox token | — | Free tier at [mapbox.com](https://mapbox.com) — needed only for Level 3 frontend |

**Verify Docker is working:**
```bash
docker compose version   # must show Compose v2
docker run hello-world
```

---

## First-Time Setup

```bash
# 1. Clone the repo and enter the directory
git clone https://github.com/0aub/saudi-sentinal.git
cd saudi-sentinal

# 2. Copy the environment file and fill in your credentials
cp .env.example .env
# Open .env — fill in everything marked <CHANGE_ME>
# Minimum required to start: CDSE_CLIENT_ID, CDSE_CLIENT_SECRET, all passwords
# MAPBOX_TOKEN is only needed for Level 3 (frontend)

# 3. Confirm everything loads
make help
```

You should see the full list of `make` targets. That confirms the environment is ready.

---

## Level 0 — Start Here (Data Pipeline)

Level 0 is the foundation. Every other level reads data that Level 0 produces.

### What it runs

| Service | Purpose | Port |
|---------|---------|------|
| PostgreSQL + PostGIS | Spatial catalog (chips, AOIs, predictions, alerts) | 5432 |
| MinIO | Object storage for chip `.tif` files | 9000 / 9001 |
| Redis | Cache + pub/sub | 6379 |
| Tile API | FastAPI service to query chips | 8100 |

### Start it

```bash
make level0-up
```

Launches all four services. Credentials are read from `.env` in the project root.

### Seed the AOI definitions

```bash
make seed-aois
```

This loads the 11 Saudi AOI polygons (Riyadh, Jeddah, NEOM, etc.) into PostGIS. **Run this once after first boot.**

### Verify it's working

```bash
# Check the Tile API health
curl http://localhost:8100/api/v1/health

# List seeded AOIs
curl http://localhost:8100/api/v1/aois

# MinIO console (login: minioadmin / minioadmin)
open http://localhost:9001
```

### Ingest your first tiles

```bash
# Ingest Sentinel-2 for Riyadh metro, last 30 days
curl -X POST http://localhost:8100/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"aoi_id": "riyadh-metro", "start_date": "2024-11-01", "end_date": "2024-11-30", "collection": "sentinel-2"}'
```

Watch the Tile API logs with:
```bash
docker compose -f docker/docker-compose.level0.yml logs -f tile-api
```

### Key files to understand

| File | What it does |
|------|-------------|
| [data_pipeline/ingestion/cdse_client.py](data_pipeline/ingestion/cdse_client.py) | Downloads tiles from Copernicus |
| [data_pipeline/ingestion/tile_processor.py](data_pipeline/ingestion/tile_processor.py) | Slices products into 256×256 chips |
| [data_pipeline/catalog/tile_catalog.py](data_pipeline/catalog/tile_catalog.py) | PostGIS interface |
| [data_pipeline/catalog/tile_store.py](data_pipeline/catalog/tile_store.py) | MinIO interface |
| [data_pipeline/config/aois.yaml](data_pipeline/config/aois.yaml) | All 11 AOI definitions |
| [docs/plans/LEVEL-0-DATA-PIPELINE.md](docs/plans/LEVEL-0-DATA-PIPELINE.md) | Full spec and schema |

### Stop it

```bash
make level0-down
```

---

## Level 1 — Notebooks (Your Main Focus)

This is where the AI models are built. There are 9 projects, each living in its own folder under `notebooks/`.

### Start JupyterLab

```bash
make notebooks
# Opens on http://localhost:8888
```

JupyterLab mounts the `notebooks/` folder. All your work is saved to disk automatically.

### How the notebooks folder is organized

```
notebooks/
├── 01-urban-sprawl/
│   ├── README.md                    ← read this first for the project
│   ├── utils/                       ← Python helper stubs you will implement
│   │   ├── dataset.py
│   │   ├── transforms.py
│   │   └── metrics.py
│   └── urban_sprawl.ipynb           ← single notebook with all sections inside
├── 02-green-riyadh/
│   └── green_riyadh.ipynb
├── 03-crop-mapping/
│   └── crop_mapping.ipynb
└── ...                              ← same structure for every project
```

### How to work on a project

1. **Read the plan doc first.** Every project has a plan doc in `docs/plans/level-1-notebooks/`. Read it before opening any notebook.
2. **Open the project README.** `notebooks/0N-project/README.md` has a quick summary.
3. **Open the single project notebook.** Each project has one `.ipynb` file. All sections are inside it in order — work through them top to bottom.
4. **Implement the utils stubs as you go.** The `utils/` files have stub functions with `raise NotImplementedError`. Fill them in when a section calls them — that keeps the notebook cells clean.
5. **Don't skip the final section.** The last section in every notebook is the ONNX export. It is required for Level 2.

### Project order recommendation

Start with the green-light projects, easiest data first:

| Order | Project | Why start here |
|-------|---------|---------------|
| 1st | **02 — Green Riyadh** | Pure NDVI time-series. Straightforward data, no labeling needed. |
| 2nd | **04 — Groundwater** | Binary NDVI threshold. Very clear signal. |
| 3rd | **01 — Urban Sprawl** | Bi-temporal change detection. Well-defined labels. |
| 4th | **05 — Desertification** | Multi-feature XGBoost. Good for understanding fusion. |
| 5th | **03 — Crop Mapping** | Temporal CNN. More complex, but great after the above. |
| Then | **06–09** | Yellow-light projects. Tackle after green-light confidence. |

### Shared utilities

The `shared/` folder has utilities usable across all projects. Import them in your notebooks:

```python
import sys
sys.path.insert(0, '/app')  # already set in notebook kernel

from shared.preprocessing.indices import ndvi, savi, evi
from shared.preprocessing.cloud_mask import apply_cloud_mask
from shared.evaluation.metrics import iou, f1_score
from shared.sentinel_client.auth import CDSEAuth
```

| Module | What's in it |
|--------|-------------|
| [shared/preprocessing/indices.py](shared/preprocessing/indices.py) | NDVI, SAVI, EVI, NDWI, NDBI, BSI, NMDI |
| [shared/preprocessing/cloud_mask.py](shared/preprocessing/cloud_mask.py) | SCL-based cloud masking |
| [shared/preprocessing/compositing.py](shared/preprocessing/compositing.py) | Monthly/annual median composites |
| [shared/evaluation/metrics.py](shared/evaluation/metrics.py) | IoU, F1, AUC-ROC, false alarm rate |
| [shared/geo_utils/crs.py](shared/geo_utils/crs.py) | CRS conversion, bbox utilities |

### Per-project plan docs

| Project | Plan doc |
|---------|---------|
| 01 Urban Sprawl | [docs/plans/level-1-notebooks/01-urban-sprawl-detector.md](docs/plans/level-1-notebooks/01-urban-sprawl-detector.md) |
| 02 Green Riyadh | [docs/plans/level-1-notebooks/02-green-riyadh-monitor.md](docs/plans/level-1-notebooks/02-green-riyadh-monitor.md) |
| 03 Crop Mapping | [docs/plans/level-1-notebooks/03-crop-type-mapping.md](docs/plans/level-1-notebooks/03-crop-type-mapping.md) |
| 04 Groundwater | [docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md](docs/plans/level-1-notebooks/04-groundwater-depletion-tracker.md) |
| 05 Desertification | [docs/plans/level-1-notebooks/05-desertification-warning.md](docs/plans/level-1-notebooks/05-desertification-warning.md) |
| 06 NEOM Tracker | [docs/plans/level-1-notebooks/06-neom-construction-tracker.md](docs/plans/level-1-notebooks/06-neom-construction-tracker.md) |
| 07 Dune Migration | [docs/plans/level-1-notebooks/07-sand-dune-migration.md](docs/plans/level-1-notebooks/07-sand-dune-migration.md) |
| 08 Flash Flood | [docs/plans/level-1-notebooks/08-flash-flood-risk.md](docs/plans/level-1-notebooks/08-flash-flood-risk.md) |
| 09 Oil Spill | [docs/plans/level-1-notebooks/09-oil-spill-detection.md](docs/plans/level-1-notebooks/09-oil-spill-detection.md) |

### Definition of done for each project

A notebook project is complete when:
- [ ] The notebook runs top-to-bottom without errors (Kernel → Restart & Run All)
- [ ] The model meets its exit criteria metrics (see plan doc)
- [ ] The final ONNX export section produces a `.onnx` file in `mlops/models/`
- [ ] All `utils/` stubs are implemented (no `NotImplementedError` remaining)

---

## Level 2 — MLOps (After Notebooks)

Start Level 2 only after at least one notebook project is fully done and has an ONNX export.

### What it adds

| Service | Purpose | Port |
|---------|---------|------|
| Apache Airflow | Schedules ingestion + inference pipelines | 8080 |
| MLflow | Tracks experiments, stores models | 5000 |
| Model Server | FastAPI serving all ONNX models | 8200 |
| Prometheus | Metrics scraping | 9090 |
| Grafana | Dashboards | 3000 |

### Start it

```bash
make level2-up
# This also starts Level 0 if not already running
```

### Register your first model

1. Open MLflow at `http://localhost:5000`
2. Find the experiment for your project (e.g., `urban-sprawl-detector`)
3. Promote the best run's model to **Staging**, then **Production**

Or use the registry helper:
```python
from mlops.registry.mlflow_config import promote_model
promote_model("urban-sprawl-detector", version=1, stage="Production")
```

### Enable the Airflow DAG

1. Open Airflow at `http://localhost:8080` (user: `airflow`, pass: `airflow`)
2. Find the DAG for your project (e.g., `urban_sprawl_pipeline`)
3. Toggle it **ON**
4. Trigger a manual run to verify the pipeline

### Verify inference is working

```bash
curl -X POST http://localhost:8200/predict/urban-sprawl \
  -H "Content-Type: application/json" \
  -d '{"aoi_id": "riyadh-metro", "date": "2024-11-15"}'
```

### Key files

| File | What it does |
|------|-------------|
| [mlops/dags/urban_sprawl_dag.py](mlops/dags/urban_sprawl_dag.py) | Airflow DAG (and 8 others) |
| [mlops/serving/main.py](mlops/serving/main.py) | FastAPI model server |
| [mlops/registry/mlflow_config.py](mlops/registry/mlflow_config.py) | MLflow setup + model promotion |
| [mlops/monitoring/drift_detector.py](mlops/monitoring/drift_detector.py) | PSI drift detection |
| [docs/plans/LEVEL-2-MLOPS.md](docs/plans/LEVEL-2-MLOPS.md) | Full spec |

---

## Level 3 — Full System (Final Stage)

Start Level 3 only after all 9 projects are in MLflow Production and their Airflow DAGs are running.

### What it adds

| Service | Purpose | Port |
|---------|---------|------|
| API Gateway | Unified REST API for frontend | 8300 |
| Frontend | React dashboard | 3001 |
| Alert Worker | Evaluates alert rules, pushes notifications | — |

### Start it

```bash
make level3-up
# Also starts Level 0 + Level 2
```

### Frontend development

```bash
cd system/frontend
npm install
npm run dev         # Vite dev server on http://localhost:5173
```

Set `VITE_API_URL=http://localhost:8300` in `system/frontend/.env.local`.

### Key files

| File | What it does |
|------|-------------|
| [system/api_gateway/main.py](system/api_gateway/main.py) | Unified FastAPI gateway |
| [system/api_gateway/tile_server.py](system/api_gateway/tile_server.py) | XYZ tile renderer |
| [system/alerts/rules.py](system/alerts/rules.py) | Alert thresholds per project |
| [system/alerts/worker.py](system/alerts/worker.py) | Alert evaluation loop |
| [system/frontend/src/App.jsx](system/frontend/src/App.jsx) | React route structure |
| [docs/plans/LEVEL-3-SYSTEM.md](docs/plans/LEVEL-3-SYSTEM.md) | Full spec |

---

## Services & Ports Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| Tile API | http://localhost:8100 | — |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| JupyterLab | http://localhost:8888 | — (token in docker logs) |
| Airflow | http://localhost:8080 | airflow / airflow |
| MLflow | http://localhost:5000 | — |
| Model Server | http://localhost:8200 | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| API Gateway | http://localhost:8300 | — |
| Frontend (prod) | http://localhost:3001 | — |
| Frontend (dev) | http://localhost:5173 | — |

---

## Day-to-Day Development Workflow

### Notebook developer (daily loop)

```bash
# 1. Make sure Level 0 is running (data available)
make level0-up

# 2. Start JupyterLab
make notebooks

# 3. Open the single project notebook (e.g. urban_sprawl.ipynb)
# 4. Work through sections top to bottom
# 5. Implement utils/ stubs as each section calls them
# 6. When all sections are done, run clean: Kernel → Restart & Run All
# 7. Confirm the final ONNX export section produces a .onnx file
```

### Check data is available before starting a project

```bash
# Query available chips for your AOI
curl "http://localhost:8100/api/v1/aois/riyadh-metro/chips?sensor=sentinel-2&limit=10"
```

If no chips exist yet, run an ingestion job first (see Level 0 above).

### Running tests

```bash
make test                            # runs pytest in Docker
```

### Linting

```bash
make lint
```

### Stopping everything

```bash
make all-down
```

---

## Exit Criteria — How You Know You're Done

### Level 0 complete when:
- [ ] `make level0-up` starts cleanly with no errors
- [ ] `make seed-aois` loads all 11 AOIs into PostGIS
- [ ] At least one Sentinel-2 ingestion run completes for one AOI
- [ ] Chips are visible in MinIO at `http://localhost:9001`

### Each Level 1 project complete when:
- [ ] The project notebook runs end-to-end without errors
- [ ] Model meets the metric thresholds in its plan doc
- [ ] ONNX file is exported and loadable with `onnxruntime`
- [ ] All `utils/` stubs are implemented

### Level 2 complete when:
- [ ] All 9 model ONNX files registered in MLflow as **Production**
- [ ] All 9 Airflow DAGs run without failures
- [ ] `http://localhost:8200/models` lists all 9 active models
- [ ] Drift detection is logging PSI scores in Grafana

### Level 3 complete when:
- [ ] React dashboard loads at `http://localhost:3001`
- [ ] All 9 project map layers render on the map page
- [ ] Alert worker sends at least one test alert
- [ ] Grafana dashboard shows all pipeline health metrics

---

## Repository Layout

```
saudi-sentinel/
├── data_pipeline/          # Level 0 — ingestion, tiling, catalog, API
│   ├── ingestion/          # CDSE client + tile processor
│   ├── tiling/             # 256×256 chip slicing
│   ├── catalog/            # PostGIS + MinIO interfaces
│   ├── config/             # aois.yaml + settings.py
│   ├── api.py              # FastAPI Tile API
│   └── seed_aois.py        # One-time AOI seeder
│
├── notebooks/              # Level 1 — 9 AI projects
│   ├── 01-urban-sprawl/    # 1 notebook (all sections) + utils/
│   ├── 02-green-riyadh/
│   ├── 03-crop-mapping/
│   ├── 04-groundwater/
│   ├── 05-desertification/
│   ├── 06-neom-tracker/
│   ├── 07-dune-migration/
│   ├── 08-flash-flood/
│   └── 09-oil-spill/
│
├── mlops/                  # Level 2 — pipelines, serving, registry
│   ├── dags/               # Airflow DAGs (one per project)
│   ├── training/           # Training scripts (extracted from notebooks)
│   ├── serving/            # FastAPI ONNX model server
│   ├── registry/           # MLflow experiment + model management
│   └── monitoring/         # PSI drift detection
│
├── system/                 # Level 3 — full production system
│   ├── api_gateway/        # Unified FastAPI + tile renderer
│   ├── alerts/             # Alert rules + worker
│   ├── frontend/           # React 18 + Deck.gl + Mapbox
│   └── monitoring/         # Prometheus + Grafana config
│
├── shared/                 # Shared Python utilities (all levels use this)
│   ├── preprocessing/      # Cloud mask, spectral indices, compositing
│   ├── evaluation/         # Metrics (IoU, F1, AUC, etc.)
│   ├── geo_utils/          # CRS, bbox, pixel conversion
│   └── sentinel_client/    # CDSE auth
│
├── docker/                 # All Docker files
│   ├── docker-compose.level0.yml
│   ├── docker-compose.level2.yml
│   ├── docker-compose.level3.yml
│   ├── docker-compose.yml      # Full stack
│   ├── data_pipeline.Dockerfile
│   ├── mlops.Dockerfile
│   ├── notebooks.Dockerfile
│   ├── system.Dockerfile
│   ├── frontend.Dockerfile
│   └── init.sql                # PostGIS extension setup (auto-run by postgres on first boot)
│
├── tests/                  # pytest suite
├── docs/plans/             # All original plan documents (reference only)
├── Makefile                # All common commands
├── pyproject.toml
├── .env.example            # Copy to .env and fill in credentials
└── .gitignore
```

---

## Plan Documents

These are the original design documents. Read them when you need the full specification for a level.

| Document | What it covers |
|----------|---------------|
| [docs/plans/README.md](docs/plans/README.md) | Master architecture overview |
| [docs/plans/LEVEL-0-DATA-PIPELINE.md](docs/plans/LEVEL-0-DATA-PIPELINE.md) | PostGIS schema, chip spec, Tile API endpoints |
| [docs/plans/LEVEL-2-MLOPS.md](docs/plans/LEVEL-2-MLOPS.md) | Airflow DAG structure, MLflow setup, serving API |
| [docs/plans/LEVEL-3-SYSTEM.md](docs/plans/LEVEL-3-SYSTEM.md) | React pages, API gateway, alerting rules |
| [docs/plans/level-1-notebooks/](docs/plans/level-1-notebooks/) | Per-project specs (data, model, metrics, exit criteria) |
