# Level 0 — Shared Data Pipeline

## Why This Exists

Every notebook and every model needs the same raw material: Sentinel satellite tiles over Saudi Arabian areas of interest. Without a centralized data layer, each project will independently re-implement data fetching, tiling, cloud masking, and storage — creating inconsistency, duplication, and bugs.

Level 0 solves this by providing a **single data ingestion service** that all downstream projects consume from.

---

## Architecture

```
                        ┌─────────────────────┐
                        │  Copernicus CDSE API │
                        │  (or Planetary Comp) │
                        └──────────┬──────────┘
                                   │ Scheduled fetch
                        ┌──────────▼──────────┐
                        │   Ingestion Service  │
                        │   (Python + CLI)     │
                        │   - AOI management   │
                        │   - Cloud filtering  │
                        │   - Band selection   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
            ┌──────────┐  ┌──────────────┐  ┌──────────┐
            │  MinIO   │  │  PostGIS     │  │  Redis   │
            │  (tiles) │  │  (catalog)   │  │  (cache) │
            └──────────┘  └──────────────┘  └──────────┘
                    │              │               │
                    └──────────────┼───────────────┘
                                   ▼
                        ┌──────────────────┐
                        │  Tile API (Fast)  │
                        │  GET /tiles/{aoi} │
                        │  GET /timeseries  │
                        └──────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
              Notebook 1     Notebook 2      Notebook N
```

---

## Areas of Interest (AOIs)

Define all Saudi AOIs once, reuse everywhere. Store as GeoJSON in PostGIS.

| AOI Name | Coordinates (approx center) | Size | Used By Projects |
|----------|-----------------------------|------|-----------------|
| `riyadh-metro` | 24.7136°N, 46.6753°E | 80×80 km | Urban Sprawl, Green Riyadh |
| `jeddah-metro` | 21.4858°N, 39.1925°E | 50×50 km | Urban Sprawl |
| `dammam-metro` | 26.3927°N, 49.9777°E | 40×40 km | Urban Sprawl |
| `aljouf-farms` | 29.8°N, 40.1°E | 100×100 km | Crop Mapping, Groundwater |
| `tabuk-farms` | 28.3°N, 36.5°E | 80×80 km | Crop Mapping, NEOM |
| `hail-farms` | 27.5°N, 41.7°E | 80×80 km | Crop Mapping, Groundwater |
| `neom-line` | 28.0°N, 35.2°E | 170×20 km strip | NEOM Tracker |
| `rub-al-khali-north` | 21.0°N, 49.0°E | 200×200 km | Sand Dune Migration |
| `arabian-gulf-coast` | 26.5°N, 50.5°E | 300 km coastline | Oil Spill Detection |
| `jeddah-wadis` | 21.5°N, 39.5°E | 60×60 km | Flash Flood Risk |
| `qassim-agri-edge` | 26.3°N, 43.8°E | 100×100 km | Desertification |

---

## Sentinel Products to Fetch

### Sentinel-2 L2A (Surface Reflectance)
- **Used by:** Projects 1-6
- **Bands:** B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR1), B12 (SWIR2), SCL (Scene Classification)
- **Resolution:** 10m (B02-B04, B08), 20m (B11, B12, SCL)
- **Cloud mask:** SCL band values 4 (vegetation), 5 (bare soil), 6 (water) = valid; rest = masked
- **Frequency:** Every 5 days per AOI
- **Date range:** 2019-01-01 to present (gives ~5 years of history)

### Sentinel-1 GRD (Ground Range Detected)
- **Used by:** Projects 5-9
- **Polarization:** VV + VH (dual-pol)
- **Resolution:** 10m
- **Mode:** IW (Interferometric Wide)
- **Frequency:** Every 6-12 days per AOI
- **Date range:** 2019-01-01 to present

---

## Data Ingestion Service

### Core Module: `sentinel_client.py`

```python
"""
Responsibilities:
- Authenticate with Copernicus Data Space Ecosystem (CDSE)
- Query available products for AOI + date range
- Download tiles with retry logic
- Apply cloud masking (S2) or preprocessing (S1)
- Slice into standardized chips (256×256 or 512×512 pixels)
- Store chips in MinIO with structured keys
- Register metadata in PostGIS catalog
"""

# Key classes:
class CDSEClient:
    """Handles OAuth2 auth + OData product search on CDSE."""
    def search_products(self, aoi: GeoJSON, start: date, end: date, 
                        collection: str, cloud_pct: int = 20) -> List[Product]
    def download_product(self, product_id: str, output_dir: Path) -> Path

class TileProcessor:
    """Processes raw Sentinel products into ML-ready chips."""
    def process_s2(self, product_path: Path, aoi: GeoJSON) -> List[Chip]
    def process_s1(self, product_path: Path, aoi: GeoJSON) -> List[Chip]
    def cloud_mask_s2(self, bands: dict, scl: np.ndarray) -> np.ndarray

class TileCatalog:
    """PostGIS-backed catalog of all processed chips."""
    def register_chip(self, chip: Chip) -> None
    def query_chips(self, aoi: str, date_range: tuple, 
                    sensor: str, max_cloud: float) -> List[ChipMeta]

class TileStore:
    """MinIO-backed storage for chip arrays."""
    def store_chip(self, chip_id: str, data: np.ndarray) -> str  # returns MinIO key
    def load_chip(self, chip_id: str) -> np.ndarray
```

### Chip Naming Convention

```
{sensor}/{aoi}/{year}/{month}/{day}/{chip_id}.tif

Examples:
s2/riyadh-metro/2024/03/15/chip_0024_0031.tif
s1/arabian-gulf-coast/2024/03/18/chip_0102_0005.tif
```

### Chip Specification

| Property | Sentinel-2 | Sentinel-1 |
|----------|-----------|-----------|
| Size | 256×256 px (2.56km) | 256×256 px (2.56km) |
| Bands | 6 (B02,B03,B04,B08,B11,B12) | 2 (VV, VH) |
| Dtype | Float32 (0.0–1.0 reflectance) | Float32 (dB backscatter) |
| Format | GeoTIFF with CRS metadata | GeoTIFF with CRS metadata |
| Cloud mask | Separate boolean mask channel | N/A (SAR penetrates clouds) |
| NoData | NaN | NaN |

---

## PostGIS Catalog Schema

```sql
CREATE EXTENSION postgis;

CREATE TABLE aois (
    aoi_id      VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(256),
    geometry    GEOMETRY(Polygon, 4326),
    projects    TEXT[],  -- which projects use this AOI
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chips (
    chip_id         VARCHAR(256) PRIMARY KEY,
    aoi_id          VARCHAR(64) REFERENCES aois(aoi_id),
    sensor          VARCHAR(10),  -- 's1' or 's2'
    acquisition_date DATE,
    cloud_pct       FLOAT,  -- NULL for S1
    geometry        GEOMETRY(Polygon, 4326),
    minio_key       VARCHAR(512),
    bands           TEXT[],
    chip_size_px    INTEGER,
    resolution_m    FLOAT,
    processed_at    TIMESTAMP DEFAULT NOW(),
    quality_flag    VARCHAR(20) DEFAULT 'valid'  -- 'valid', 'cloudy', 'partial', 'corrupt'
);

CREATE INDEX idx_chips_aoi_date ON chips(aoi_id, acquisition_date);
CREATE INDEX idx_chips_sensor ON chips(sensor);
CREATE INDEX idx_chips_geom ON chips USING GIST(geometry);

CREATE TABLE ingestion_runs (
    run_id      SERIAL PRIMARY KEY,
    aoi_id      VARCHAR(64),
    sensor      VARCHAR(10),
    date_from   DATE,
    date_to     DATE,
    chips_added INTEGER,
    status      VARCHAR(20),  -- 'success', 'partial', 'failed'
    error_msg   TEXT,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP
);
```

---

## Tile API (FastAPI)

Lightweight internal API that notebooks and MLOps pipelines call to get data.

```
GET  /api/v1/aois                          → List all AOIs
GET  /api/v1/aois/{aoi_id}/chips           → List chips for AOI
     ?sensor=s2&start=2024-01-01&end=2024-12-31&max_cloud=15
GET  /api/v1/chips/{chip_id}               → Download chip as GeoTIFF
GET  /api/v1/chips/{chip_id}/metadata      → Chip metadata (JSON)
GET  /api/v1/timeseries/{aoi_id}           → Get time-ordered chip list
     ?sensor=s2&band=ndvi&aggregation=monthly
POST /api/v1/ingest                        → Trigger ingestion for AOI + date range
GET  /api/v1/health                        → Service health check
```

---

## Docker Setup

### `docker/docker-compose.level0.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: sentinel_catalog
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  tile-api:
    build:
      context: ..
      dockerfile: docker/data-pipeline.Dockerfile
    ports:
      - "8100:8100"
    environment:
      DATABASE_URL: postgresql://sentinel:${POSTGRES_PASSWORD}@postgres:5432/sentinel_catalog
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_USER}
      MINIO_SECRET_KEY: ${MINIO_PASSWORD}
      REDIS_URL: redis://redis:6379
      CDSE_CLIENT_ID: ${CDSE_CLIENT_ID}
      CDSE_CLIENT_SECRET: ${CDSE_CLIENT_SECRET}
    depends_on:
      - postgres
      - minio
      - redis

volumes:
  pgdata:
  miniodata:
```

---

## Configuration

### `config/aois.yaml`

```yaml
# All Saudi AOIs for the platform
aois:
  riyadh-metro:
    center: [24.7136, 46.6753]
    size_km: [80, 80]
    sensors: [s2]
    fetch_frequency_days: 5
    max_cloud_pct: 20
    projects: [urban-sprawl, green-riyadh]

  aljouf-farms:
    center: [29.8, 40.1]
    size_km: [100, 100]
    sensors: [s2]
    fetch_frequency_days: 5
    max_cloud_pct: 15
    projects: [crop-mapping, groundwater]

  neom-line:
    center: [28.0, 35.2]
    size_km: [170, 20]
    sensors: [s1, s2]
    fetch_frequency_days: 5
    max_cloud_pct: 20
    projects: [neom-tracker]

  # ... (repeat for all AOIs listed above)
```

---

## Setup Steps

1. **Register on Copernicus Data Space Ecosystem**
   - Go to `https://dataspace.copernicus.eu`
   - Create a free account
   - Generate OAuth client credentials (Client ID + Secret)
   - Store in `.env` file

2. **Start Level 0 infrastructure**
   ```bash
   cd docker/
   cp .env.example .env  # fill in credentials
   docker compose -f docker-compose.level0.yml up -d
   ```

3. **Run initial AOI seeding**
   ```bash
   python data-pipeline/seed_aois.py --config config/aois.yaml
   ```

4. **Run historical backfill**
   ```bash
   # Fetch all Sentinel-2 tiles for Riyadh from 2019-2024
   python data-pipeline/ingest.py \
       --aoi riyadh-metro \
       --sensor s2 \
       --start 2019-01-01 \
       --end 2024-12-31
   ```

5. **Verify**
   ```bash
   # Check catalog
   curl http://localhost:8100/api/v1/aois/riyadh-metro/chips?sensor=s2 | jq '.count'
   
   # Check MinIO console
   open http://localhost:9001  # login with MINIO_USER/PASSWORD
   ```

---

## Dependencies

```
# data-pipeline/requirements.txt
sentinelhub>=3.10
rasterio>=1.3
shapely>=2.0
geopandas>=0.14
psycopg2-binary>=2.9
sqlalchemy>=2.0
geoalchemy2>=0.14
minio>=7.2
fastapi>=0.109
uvicorn>=0.27
redis>=5.0
pyyaml>=6.0
click>=8.1
httpx>=0.27
pydantic>=2.5
numpy>=1.26
```

---

## Success Criteria

Before moving to Level 1:

- [ ] PostGIS catalog has at least 12 months of S2 chips for `riyadh-metro`
- [ ] PostGIS catalog has at least 12 months of S2 chips for `aljouf-farms`
- [ ] Tile API returns chips in < 500ms
- [ ] Cloud masking filters out > 90% of unusable pixels
- [ ] MinIO stores chips in the defined naming convention
- [ ] At least one S1 AOI (`arabian-gulf-coast`) has 12 months of data
- [ ] Ingestion service can run unattended on a cron schedule
