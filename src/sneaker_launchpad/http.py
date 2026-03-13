from __future__ import annotations

from typing import Final

import httpx

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    )
}


class HttpTextFetcher:
    def __init__(self, timeout_seconds: float) -> None:
        self._client = httpx.Client(
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds,
        )

    def fetch(self, url: str) -> str:
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    def close(self) -> None:
        self._client.close()
