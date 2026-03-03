# Implementation guide: see docs/LEVEL-2-MLOPS.md — "Docker Configuration → mlops.Dockerfile"
# Level 2: Airflow + MLflow + Model Server
# Verbatim from plan doc.

FROM python:3.11-slim

# System dependencies for geospatial
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY mlops/requirements.txt /tmp/mlops-requirements.txt
RUN pip install --no-cache-dir -r /tmp/mlops-requirements.txt

# Code
COPY shared/ /app/shared/
COPY mlops/ /app/mlops/

WORKDIR /app
ENV PYTHONPATH=/app

# Default command is overridden per service in docker-compose.level2.yml:
#   airflow-webserver: airflow webserver
#   airflow-scheduler: airflow scheduler
#   mlflow:            mlflow server ...
#   model-server:      uvicorn mlops.serving.main:app --port 8200
