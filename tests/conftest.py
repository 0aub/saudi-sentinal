# Implementation guide: see docs/plans/LEVEL-3-SYSTEM.md — "Testing Strategy"
"""
Pytest configuration and shared fixtures for Saudi Sentinel AI test suite.

Testing strategy (from docs/plans/LEVEL-3-SYSTEM.md):
  Unit:        pytest — data processing functions, feature engineering, colormap rendering
  Integration: pytest + testcontainers — API ↔ PostGIS, API ↔ MinIO, API ↔ Model Server
  E2E:         Playwright — full user flows (login → view map → toggle layers → download report)
  Load:        Locust — 100 concurrent users, tile server < 200ms p95
  Model:       Custom — prediction quality on held-out test set after every retraining
"""

import numpy as np
import pytest


# --- Synthetic data fixtures ---

@pytest.fixture
def synthetic_s2_chip():
    """
    A synthetic 6-band, 256×256 Sentinel-2 chip for unit testing.
    Bands: [B02, B03, B04, B08, B11, B12], dtype float32, range [0, 1].
    """
    np.random.seed(42)
    return np.random.rand(6, 256, 256).astype(np.float32)


@pytest.fixture
def synthetic_s1_chip():
    """A synthetic 2-band, 256×256 Sentinel-1 chip (VV, VH) in dB, dtype float32."""
    np.random.seed(42)
    # Realistic dB range: roughly -25 to -5 dB for land surfaces
    return np.random.uniform(-25, -5, size=(2, 256, 256)).astype(np.float32)


@pytest.fixture
def synthetic_scl():
    """A synthetic 256×256 SCL (Scene Classification Layer) array."""
    np.random.seed(42)
    # Mostly valid pixels (4=vegetation, 5=bare soil, 6=water)
    scl = np.random.choice([4, 5, 6, 8, 9], size=(256, 256), p=[0.4, 0.3, 0.1, 0.1, 0.1])
    return scl.astype(np.uint8)


@pytest.fixture
def synthetic_change_mask():
    """A synthetic 256×256 binary change mask (0=unchanged, 1=changed)."""
    np.random.seed(42)
    # ~10% change (realistic for urban sprawl)
    return np.random.choice([0, 1], size=(1, 256, 256), p=[0.9, 0.1]).astype(np.float32)


@pytest.fixture
def sample_aoi_geojson():
    """GeoJSON polygon for a small test AOI (5km × 5km near Riyadh)."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [46.65, 24.70],
            [46.70, 24.70],
            [46.70, 24.75],
            [46.65, 24.75],
            [46.65, 24.70],
        ]],
    }


# --- Database/service fixtures (integration tests) ---

@pytest.fixture(scope="session")
def postgres_container():
    """
    Spin up a PostGIS container for integration tests.

    Implementation: Use testcontainers-python:
        from testcontainers.postgres import PostgresContainer
        with PostgresContainer("postgis/postgis:16-3.4") as pg:
            yield pg.get_connection_url()
    """
    pytest.skip("Implement with testcontainers — see docs/plans/LEVEL-3-SYSTEM.md Testing Strategy")


@pytest.fixture(scope="session")
def minio_container():
    """
    Spin up a MinIO container for integration tests.
    """
    pytest.skip("Implement with testcontainers — see docs/plans/LEVEL-3-SYSTEM.md Testing Strategy")
