# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Docker Setup" → environment vars
"""
Environment-based configuration for the data pipeline service.

All values are read from environment variables (set via .env or docker-compose).
Never hard-code credentials here.

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — docker-compose.level0.yml environment section
See: .env.example in project root for full list of required variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # --- PostgreSQL / PostGIS ---
    database_url: str

    # --- MinIO (S3-compatible object storage) ---
    minio_endpoint: str       # host:port, no scheme — e.g. "localhost:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool        # True for HTTPS in production

    # --- Redis ---
    redis_url: str            # e.g. "redis://localhost:6379"

    # --- Copernicus CDSE credentials ---
    cdse_client_id: str
    cdse_client_secret: str

    # --- Ingestion defaults ---
    chip_size_px: int         # 256
    default_max_cloud_pct: int  # 20

    # --- API server ---
    api_host: str             # "0.0.0.0"
    api_port: int             # 8100


def get_settings() -> Settings:
    """
    Load all settings from environment variables.

    Raises:
        KeyError if a required variable is missing.

    Usage:
        from data_pipeline.config.settings import get_settings
        cfg = get_settings()
        engine = create_engine(cfg.database_url)
    """
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        minio_endpoint=os.environ["MINIO_ENDPOINT"],
        minio_access_key=os.environ["MINIO_ACCESS_KEY"],
        minio_secret_key=os.environ["MINIO_SECRET_KEY"],
        minio_secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        redis_url=os.environ["REDIS_URL"],
        cdse_client_id=os.environ["CDSE_CLIENT_ID"],
        cdse_client_secret=os.environ["CDSE_CLIENT_SECRET"],
        chip_size_px=int(os.getenv("CHIP_SIZE_PX", "256")),
        default_max_cloud_pct=int(os.getenv("DEFAULT_MAX_CLOUD_PCT", "20")),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8100")),
    )
