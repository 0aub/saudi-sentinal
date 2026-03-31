# Implementation guide: see docs/LEVEL-3-SYSTEM.md — "Docker Configuration"
# Level 3: API Gateway + Alert Worker

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install system-level Python deps (superset of Level 0 + Level 2)
COPY mlops/requirements.txt /tmp/mlops-req.txt
COPY data_pipeline/requirements.txt /tmp/pipeline-req.txt
RUN pip install --no-cache-dir \
    -r /tmp/mlops-req.txt \
    -r /tmp/pipeline-req.txt \
    mercantile \
    Pillow \
    websockets \
    python-multipart \
    python-jose[cryptography]

COPY shared/ /app/shared/
COPY system/ /app/system/
COPY mlops/ /app/mlops/
COPY data_pipeline/ /app/data_pipeline/

WORKDIR /app
ENV PYTHONPATH=/app

EXPOSE 8300

# Default overridden per service in docker-compose.level3.yml
CMD ["uvicorn", "system.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8300"]
