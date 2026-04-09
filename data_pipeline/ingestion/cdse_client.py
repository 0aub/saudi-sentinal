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

import logging
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List

import httpx
from shapely.geometry import shape

logger = logging.getLogger(__name__)

# Maximum number of retry attempts for HTTP requests
_MAX_RETRIES = 3
# Base delay (seconds) for exponential backoff
_BACKOFF_BASE = 2.0
# Buffer (seconds) before token expiry to trigger refresh
_TOKEN_EXPIRY_BUFFER = 30


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
    CDSE_DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ["CDSE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["CDSE_CLIENT_SECRET"]
        self._access_token: str | None = None
        self._token_expiry: float = 0.0  # Unix timestamp when token expires
        self._http = httpx.Client(timeout=60.0)

    def authenticate(self) -> None:
        """Obtain OAuth2 access token from CDSE identity server."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._http.post(self.CDSE_TOKEN_URL, data=data)
                resp.raise_for_status()
                token_data = resp.json()
                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 600)
                self._token_expiry = time.time() + expires_in
                logger.info("CDSE authentication successful, token expires in %ds", expires_in)
                return
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "CDSE auth attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_BACKOFF_BASE ** attempt)
                else:
                    raise RuntimeError(
                        f"Failed to authenticate with CDSE after {_MAX_RETRIES} attempts"
                    ) from exc

    def _refresh_token_if_needed(self) -> None:
        """Re-authenticate if token is expired (tokens last 10 minutes on CDSE)."""
        if self._access_token is None or time.time() >= (self._token_expiry - _TOKEN_EXPIRY_BUFFER):
            logger.debug("Token expired or missing, refreshing...")
            self.authenticate()

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header, refreshing token if needed."""
        self._refresh_token_if_needed()
        return {"Authorization": f"Bearer {self._access_token}"}

    @staticmethod
    def _geojson_to_wkt(geojson: dict) -> str:
        """Convert a GeoJSON geometry dict to WKT string."""
        geom = shape(geojson)
        return geom.wkt

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
        self._refresh_token_if_needed()

        wkt = self._geojson_to_wkt(aoi)
        start_str = f"{start.isoformat()}T00:00:00.000Z"
        end_str = f"{end.isoformat()}T23:59:59.999Z"

        # Build OData filter
        filters = [
            f"Collection/Name eq '{collection}'",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')",
            f"ContentDate/Start gt {start_str}",
            f"ContentDate/Start lt {end_str}",
        ]
        if collection == "SENTINEL-2":
            filters.append(
                f"Attributes/OData.CSC.DoubleAttribute/any("
                f"att:att/Name eq 'cloudCover' and "
                f"att/OData.CSC.DoubleAttribute/Value lt {cloud_pct})"
            )

        filter_str = " and ".join(filters)
        url = f"{self.CDSE_ODATA_URL}/Products"
        params = {
            "$filter": filter_str,
            "$orderby": "ContentDate/Start asc",
            "$top": 1000,
        }

        products: List[Product] = []
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = self._http.get(
                    url, params=params, headers=self._auth_headers()
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "CDSE search attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_BACKOFF_BASE ** attempt)
                else:
                    raise RuntimeError(
                        f"CDSE product search failed after {_MAX_RETRIES} attempts"
                    ) from exc

        for item in data.get("value", []):
            acq_date_str = item.get("ContentDate", {}).get("Start", "")
            try:
                acq_date = datetime.fromisoformat(
                    acq_date_str.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                acq_date = start  # fallback

            # Extract cloud cover from attributes if available
            item_cloud_pct = None
            if collection == "SENTINEL-2":
                for attr in item.get("Attributes", []):
                    if attr.get("Name") == "cloudCover":
                        item_cloud_pct = float(attr.get("Value", 0))
                        break

            size_bytes = item.get("ContentLength", 0)
            size_mb = size_bytes / (1024 * 1024)

            footprint = item.get("GeoFootprint", {})
            product_id = item["Id"]

            products.append(
                Product(
                    product_id=product_id,
                    name=item.get("Name", ""),
                    collection=collection,
                    acquisition_date=acq_date,
                    cloud_pct=item_cloud_pct,
                    size_mb=round(size_mb, 2),
                    geometry=footprint,
                    download_url=f"{self.CDSE_DOWNLOAD_URL}({product_id})/$value",
                )
            )

        logger.info("Found %d products for %s in [%s, %s]", len(products), collection, start, end)
        return products

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
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        download_url = f"{self.CDSE_DOWNLOAD_URL}({product_id})/$value"

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                self._refresh_token_if_needed()
                with self._http.stream(
                    "GET", download_url, headers=self._auth_headers(), follow_redirects=True
                ) as resp:
                    resp.raise_for_status()

                    # Determine filename from Content-Disposition or use product_id
                    content_disp = resp.headers.get("content-disposition", "")
                    if "filename=" in content_disp:
                        filename = content_disp.split("filename=")[-1].strip('" ')
                    else:
                        filename = f"{product_id}.zip"

                    output_path = output_dir / filename
                    expected_size = int(resp.headers.get("content-length", 0))
                    downloaded = 0

                    with open(output_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                    # Verify download integrity
                    if expected_size > 0 and downloaded != expected_size:
                        logger.warning(
                            "Size mismatch: expected %d, got %d bytes", expected_size, downloaded
                        )
                        output_path.unlink(missing_ok=True)
                        raise IOError(
                            f"Incomplete download: {downloaded}/{expected_size} bytes"
                        )

                    logger.info(
                        "Downloaded product %s (%.1f MB) to %s",
                        product_id,
                        downloaded / (1024 * 1024),
                        output_path,
                    )
                    return output_path

            except (httpx.HTTPStatusError, httpx.RequestError, IOError) as exc:
                logger.warning(
                    "Download attempt %d/%d for %s failed: %s",
                    attempt, _MAX_RETRIES, product_id, exc,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_BACKOFF_BASE ** attempt)
                else:
                    raise RuntimeError(
                        f"Failed to download product {product_id} after {_MAX_RETRIES} attempts"
                    ) from exc

        # Should not reach here, but satisfy type checker
        raise RuntimeError(f"Failed to download product {product_id}")
