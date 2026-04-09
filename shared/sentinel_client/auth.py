# Implementation guide: see docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps → Register on CDSE"
"""
CDSE (Copernicus Data Space Ecosystem) OAuth2 authentication.

The Copernicus Data Space Ecosystem uses Keycloak-based OAuth2.
Credentials are obtained at: https://dataspace.copernicus.eu

Authentication flow:
  1. POST to token endpoint with client_id + client_secret
  2. Receive access_token (valid 10 minutes) + refresh_token
  3. Include access_token as "Authorization: Bearer <token>" in all API requests
  4. Refresh automatically when token expires

Token endpoint:
  https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token

See: docs/plans/LEVEL-0-DATA-PIPELINE.md — "Setup Steps" → step 1
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CDSEToken:
    """OAuth2 token bundle from CDSE."""
    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp when access_token expires
    token_type: str = "Bearer"

    def is_expired(self, buffer_seconds: int = 30) -> bool:
        """Return True if token will expire within buffer_seconds."""
        return time.time() >= (self.expires_at - buffer_seconds)


class CDSEAuth:
    """
    CDSE OAuth2 client credentials authentication manager.

    Handles token lifecycle: initial auth, auto-refresh, and expiry detection.

    Usage:
        auth = CDSEAuth()
        headers = auth.get_auth_headers()  # Auto-refreshes if needed
        requests.get(url, headers=headers)
    """

    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.environ["CDSE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["CDSE_CLIENT_SECRET"]
        self._token: Optional[CDSEToken] = None

    def authenticate(self) -> CDSEToken:
        """
        Obtain a new OAuth2 access token via client credentials grant.

        Implementation:
        - POST to TOKEN_URL
        - Body: grant_type=client_credentials&client_id=...&client_secret=...
        - Parse response: access_token, refresh_token, expires_in
        - Store as CDSEToken with expires_at = now + expires_in
        """
        import httpx

        response = httpx.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()

        self._token = CDSEToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=time.time() + data["expires_in"],
            token_type=data.get("token_type", "Bearer"),
        )
        return self._token

    def refresh_token(self) -> CDSEToken:
        """
        Refresh access token using the refresh_token grant.
        Falls back to full re-authentication if refresh_token is also expired.
        """
        import httpx

        if not self._token or not self._token.refresh_token:
            return self.authenticate()

        try:
            response = httpx.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()

            self._token = CDSEToken(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", self._token.refresh_token),
                expires_at=time.time() + data["expires_in"],
                token_type=data.get("token_type", "Bearer"),
            )
            return self._token
        except httpx.HTTPStatusError:
            return self.authenticate()

    def get_auth_headers(self) -> dict:
        """
        Return Authorization headers dict, auto-refreshing token if needed.

        Usage:
            headers = auth.get_auth_headers()
            response = httpx.get(url, headers=headers)
        """
        if self._token is None or self._token.is_expired():
            if self._token and not self._token.is_expired(buffer_seconds=0):
                self._token = self.refresh_token()
            else:
                self._token = self.authenticate()
        return {"Authorization": f"Bearer {self._token.access_token}"}
