# Implementation guide: see docs/LEVEL-0-DATA-PIPELINE.md — "Docker Setup"
# Level 0: Data pipeline service (Tile API + ingestion CLI)

FROM python:3.11-slim

# System dependencies for geospatial libraries (rasterio, GDAL, shapely)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY data-pipeline/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Application code
COPY shared/ /app/shared/
COPY data-pipeline/ /app/data-pipeline/

WORKDIR /app
ENV PYTHONPATH=/app

EXPOSE 8100

# Default: run the Tile API server
CMD ["uvicorn", "data_pipeline.api:app", "--host", "0.0.0.0", "--port", "8100"]
