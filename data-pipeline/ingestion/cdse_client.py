# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "CDSEClient" section
"""
CDSE (Copernicus Data Space Ecosystem) client.

Responsibilities:
- Authenticate with CDSE via OAuth2 (client credentials flow)
- Query available Sentinel products for an AOI + date range via OData API
- Download product archives with retry/resume logic
- Return local paths for downstream processing

Environment variables required:
  CDSE_CLIENT_ID      — OAuth2 client ID from dataspace.copernicus.eu
  CDSE_CLIENT_SECRET  — OAuth2 client secret
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List


@dataclass
class Product:
    """Metadata for a single Sentinel product returned by CDSE search."""
    product_id: str
    name: str
    collection: str          # e.g. "SENTINEL-2", "SENTINEL-1"
    acquisition_date: date
    cloud_pct: float | None  # None for S1 (SAR)
    size_mb: float
    geometry: dict           # GeoJSON polygon of product footprint
    download_url: str


class CDSEClient:
    """
    Handles OAuth2 authentication and OData product search on CDSE.

    Implementation guide: docs/plans/LEVEL-0-DATA-PIPELINE.md — "CDSEClient" section

    Usage:
        client = CDSEClient()
        products = client.search_products(
            aoi=geojson_polygon,
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
            collection="SENTINEL-2",
            cloud_pct=20,
        )
        local_path = client.download_product(products[0].product_id, Path("/tmp"))
    """

    CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    CDSE_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ["CDSE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["CDSE_CLIENT_SECRET"]
        self._access_token: str | None = None

    def authenticate(self) -> None:
        """Obtain OAuth2 access token from CDSE identity server."""
        raise NotImplementedError(
            "Implement OAuth2 client-credentials flow. "
            "POST to CDSE_TOKEN_URL with grant_type=client_credentials. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def search_products(
        self,
        aoi: dict,
        start: date,
        end: date,
        collection: str,
        cloud_pct: int = 20,
    ) -> List[Product]:
        """
        Query CDSE OData API for available products.

        Args:
            aoi:        GeoJSON polygon defining the area of interest.
            start:      Start date (inclusive).
            end:        End date (inclusive).
            collection: "SENTINEL-2" or "SENTINEL-1".
            cloud_pct:  Maximum cloud coverage % (S2 only; ignored for S1).

        Returns:
            List of Product objects, sorted by acquisition_date ascending.
        """
        raise NotImplementedError(
            "Implement OData $filter query. "
            "Filter by Collection/Name, ContentDate, OData.CSC.Intersects(geometry), "
            "and Attributes/OData.CSC.DoubleAttribute for cloud cover. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def download_product(self, product_id: str, output_dir: Path) -> Path:
        """
        Download a product archive to output_dir.

        Returns:
            Path to the downloaded .zip or .SAFE directory.

        Implementation notes:
        - Stream download in chunks (avoid loading full file in memory)
        - Implement exponential back-off retry (up to 3 attempts)
        - Verify download integrity via Content-Length or checksum
        """
        raise NotImplementedError(
            "Implement streaming download with retry logic. "
            "See docs/plans/LEVEL-0-DATA-PIPELINE.md."
        )

    def _refresh_token_if_needed(self) -> None:
        """Re-authenticate if token is expired (tokens last 10 minutes on CDSE)."""
        raise NotImplementedError
