from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from bs4 import BeautifulSoup

from sneaker_launchpad.models import CatalogSnapshot, ReleaseState, SneakerRelease, StoreName
from sneaker_launchpad.providers.nike import CatalogFetchError


class AdidasCatalogProvider:
    store = StoreName.ADIDAS
    release_url = "https://www.adidas.com/us/release-dates"

    def __init__(self, fetch_text: Callable[[str], str]) -> None:
        self._fetch_text = fetch_text

    def fetch_snapshot(self, now: datetime) -> CatalogSnapshot:
        html = self._fetch_text(self.release_url)
        releases = parse_adidas_release_html(html)
        return CatalogSnapshot(
            provider=self.store,
            fetched_at=now,
            releases=tuple(releases),
            live_fetch_succeeded=True,
            status_message=f"Loaded {len(releases)} release(s) from Adidas.",
        )


def parse_adidas_release_html(html: str) -> list[SneakerRelease]:
    lowered = html.lower()
    if "unable to give you access to our site" in lowered or "403 error" in lowered:
        raise CatalogFetchError(
            "adidas.com blocked the automated catalog refresh. Keep using cached releases "
            "or add manual product URLs for purchase attempts."
        )
    if "no upcoming releases" in lowered:
        return []

    soup = BeautifulSoup(html, "html.parser")
    releases: list[SneakerRelease] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if script.string is None or not script.string.strip():
            continue
        payload = json.loads(script.string)
        releases.extend(_parse_ld_json(payload))
    return sorted(releases, key=lambda release: release.release_at)


def _parse_ld_json(payload: Any) -> list[SneakerRelease]:
    if isinstance(payload, list):
        releases: list[SneakerRelease] = []
        for item in payload:
            releases.extend(_parse_ld_json(item))
        return releases
    if not isinstance(payload, dict):
        return []
    payload_type = str(payload.get("@type", "")).lower()
    if payload_type == "itemlist":
        releases: list[SneakerRelease] = []
        for element in payload.get("itemListElement", []):
            if isinstance(element, dict):
                releases.extend(_parse_ld_json(element.get("item")))
        return releases
    if payload_type == "product":
        return [_product_from_ld_json(payload)]
    return []


def _product_from_ld_json(payload: dict[str, Any]) -> SneakerRelease:
    offers = payload.get("offers", {})
    price_raw = "0"
    currency = "USD"
    if isinstance(offers, dict):
        price_raw = str(offers.get("price", "0"))
        currency = str(offers.get("priceCurrency", "USD"))
    release_at_raw = str(payload.get("releaseDate", payload.get("datePublished", "")))
    release_at = (
        datetime.fromisoformat(release_at_raw.replace("Z", "+00:00"))
        if release_at_raw
        else datetime.now(tz=UTC)
    )
    style_code = str(payload.get("sku", "")).strip()
    name = str(payload.get("name", "Adidas Release")).strip()
    return SneakerRelease(
        id=style_code or name.lower().replace(" ", "-"),
        provider=StoreName.ADIDAS,
        name=name,
        subtitle=str(payload.get("category", "Sneaker Release")).strip(),
        style_code=style_code,
        colorway=str(payload.get("color", style_code)).strip(),
        product_url=str(payload.get("url", "https://www.adidas.com/us/release-dates")).strip(),
        image_url=str(payload.get("image", "")).strip(),
        release_at=release_at,
        price=Decimal(price_raw),
        currency=currency,
        sizes=tuple(),
        state=ReleaseState.UPCOMING,
    )
