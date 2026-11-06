"""Small client for TikTok's authorized Research API."""

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
VIDEO_URL = "https://open.tiktokapis.com/v2/research/video/query/"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class TikTokClient:
    def __init__(self):
        # The .env file lives in the project root, one level above src/.
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        self.key = os.getenv("TIKTOK_CLIENT_KEY")
        self.secret = os.getenv("TIKTOK_CLIENT_SECRET")
        if not self.key or not self.secret:
            raise RuntimeError("Missing TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET in .env")

        self.session = requests.Session()
        self.token = None
        self.token_expires_at = 0

    def _post(self, url, **kwargs):
        """Retry temporary connection/server errors, not invalid API requests."""
        for attempt in range(3):
            try:
                response = self.session.post(url, timeout=30, **kwargs)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
                continue

            if response.status_code in RETRY_STATUSES and attempt < 2:
                time.sleep(2 ** attempt)
                continue

            if not response.ok:
                # Do not print request headers, bodies, credentials, or tokens.
                raise RuntimeError(f"TikTok HTTP error {response.status_code}")

            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("TikTok returned a non-JSON response") from exc

            error = data.get("error")
            if isinstance(error, dict) and error.get("code") not in (None, "ok", 0):
                # Log error codes only: response messages may contain sensitive data.
                raise RuntimeError(f"TikTok API error: {error.get('code')}")
            return data

        raise RuntimeError("TikTok request failed after retries")

    def _get_token(self):
        data = self._post(
            TOKEN_URL,
            data={
                "client_key": self.key,
                "client_secret": self.secret,
                "grant_type": "client_credentials",
            },
        )
        self.token = data.get("access_token")
        if not self.token:
            raise RuntimeError("Token request did not return an access_token")
        # Refresh slightly early. Never print or save the token.
        self.token_expires_at = time.monotonic() + max(0, data.get("expires_in", 7200) - 60)

    def query_videos(self, fields, body):
        if self.token is None or time.monotonic() >= self.token_expires_at:
            self._get_token()

        return self._post(
            VIDEO_URL,
            params={"fields": ",".join(fields)},
            headers={"Authorization": f"Bearer {self.token}"},
            json=body,
        )
