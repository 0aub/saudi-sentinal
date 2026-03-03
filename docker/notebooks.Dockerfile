# Implementation guide: see docs/README.md — "Folder Structure → notebooks.Dockerfile"
# Level 1: JupyterLab environment with full geospatial + ML stack

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ML + geospatial dependencies for all 9 notebooks
RUN pip install --no-cache-dir \
    jupyterlab>=4.0 \
    ipywidgets \
    rasterio>=1.3 \
    shapely>=2.0 \
    geopandas>=0.14 \
    numpy>=1.26 \
    pandas>=2.0 \
    matplotlib>=3.8 \
    seaborn>=0.13 \
    scikit-learn>=1.4 \
    xgboost>=2.0 \
    torch>=2.0 \
    segmentation-models-pytorch>=0.3 \
    albumentations>=1.3 \
    pymannkendall>=1.4 \
    dtaidistance>=2.3 \
    scikit-image>=0.22 \
    mlflow>=2.10 \
    minio>=7.2 \
    psycopg2-binary>=2.9 \
    sqlalchemy>=2.0 \
    geoalchemy2>=0.14 \
    pyyaml>=6.0 \
    httpx>=0.27 \
    folium \
    keplergl

COPY shared/ /app/shared/
COPY notebooks/ /app/notebooks/

WORKDIR /app
ENV PYTHONPATH=/app

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--NotebookApp.token=''", "--NotebookApp.password=''"]
