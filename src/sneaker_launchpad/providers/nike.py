from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from bs4 import BeautifulSoup

from sneaker_launchpad.models import CatalogSnapshot, ReleaseState, SneakerRelease, StoreName


class CatalogFetchError(RuntimeError):
    """Raised when a provider cannot build a usable catalog snapshot."""


class NikeCatalogProvider:
    store = StoreName.NIKE
    launch_url = "https://www.nike.com/launch"

    def __init__(self, fetch_text: Callable[[str], str]) -> None:
        self._fetch_text = fetch_text

    def fetch_snapshot(self, now: datetime) -> CatalogSnapshot:
        html = self._fetch_text(self.launch_url)
        releases = parse_nike_launch_html(html)
        return CatalogSnapshot(
            provider=self.store,
            fetched_at=now,
            releases=tuple(releases),
            live_fetch_succeeded=True,
            status_message=f"Loaded {len(releases)} release(s) from Nike SNKRS.",
        )


def parse_nike_launch_html(html: str) -> list[SneakerRelease]:
    soup = BeautifulSoup(html, "html.parser")
    next_data_node = soup.find("script", id="__NEXT_DATA__")
    if next_data_node is None or next_data_node.string is None:
        raise CatalogFetchError("Nike launch page did not include __NEXT_DATA__.")
    root_payload = json.loads(next_data_node.string)
    initial_state = json.loads(root_payload["props"]["pageProps"]["initialState"])
    thread_items = cast(
        dict[str, dict[str, Any]],
        initial_state["product"]["threads"]["data"]["items"],
    )
    product_items = cast(
        dict[str, dict[str, Any]],
        initial_state["product"]["products"]["data"]["items"],
    )
    thread_by_product_id: dict[str, dict[str, Any]] = {}
    for thread in thread_items.values():
        primary_product_id = thread.get("productId")
        if isinstance(primary_product_id, str):
            thread_by_product_id[primary_product_id] = thread
        for product_id in thread.get("productIds", []):
            if isinstance(product_id, str):
                thread_by_product_id.setdefault(product_id, thread)

    releases: list[SneakerRelease] = []
    for product_id, product in product_items.items():
        if not _looks_like_launch_product(product):
            continue
        title = str(product.get("title", "")).strip()
        if not title:
            continue
        thread = thread_by_product_id.get(product_id, {})
        releases.append(
            SneakerRelease(
                id=product_id,
                provider=StoreName.NIKE,
                name=title,
                subtitle=str(product.get("subtitle", "")).strip(),
                style_code=str(product.get("styleColor", "")).strip(),
                colorway=_derive_colorway(thread, product),
                product_url=_build_product_url(thread),
                image_url=str(
                    product.get("imageSrc")
                    or thread.get("coverCard", {}).get("defaultURL", "")
                ),
                release_at=_parse_nike_datetime(product.get("commerceStartDate")),
                price=Decimal(str(product.get("currentPrice", product.get("fullPrice", "0")))),
                currency=str(product.get("currency", "USD")),
                sizes=_collect_sizes(product),
                state=_derive_state(product),
            )
        )
    if not releases:
        raise CatalogFetchError("Nike launch page did not contain launch footwear.")
    return sorted(releases, key=lambda release: release.release_at)


def _looks_like_launch_product(product: dict[str, Any]) -> bool:
    return bool(product.get("isLaunchProduct")) and str(product.get("productType")) == "FOOTWEAR"


def _derive_colorway(thread: dict[str, Any], product: dict[str, Any]) -> str:
    cover_card = cast(dict[str, Any], thread.get("coverCard", {}))
    colorway = str(cover_card.get("title", "")).strip()
    if colorway:
        return colorway
    subtitle = str(product.get("subtitle", "")).strip()
    if subtitle:
        return subtitle
    return str(product.get("styleColor", "")).strip()


def _build_product_url(thread: dict[str, Any]) -> str:
    seo = cast(dict[str, Any], thread.get("seo", {}))
    slug = str(seo.get("slug", "")).strip()
    if slug:
        return f"https://www.nike.com/launch/t/{slug}"
    return "https://www.nike.com/launch"


def _collect_sizes(product: dict[str, Any]) -> tuple[str, ...]:
    sizes: list[str] = []
    for sku in product.get("skus", []):
        if not isinstance(sku, dict) or not sku.get("available"):
            continue
        label = str(sku.get("nike_size", "")).strip()
        if not label:
            country_specs = sku.get("country_specifications", [])
            if country_specs and isinstance(country_specs[0], dict):
                label = str(country_specs[0].get("localized_size", "")).strip()
        if label:
            sizes.append(label)
    seen = dict.fromkeys(sizes)
    return tuple(seen.keys())


def _derive_state(product: dict[str, Any]) -> ReleaseState:
    launch_status = str(product.get("launchStatus", "")).upper()
    if launch_status == "ACTIVE":
        return ReleaseState.LIVE
    if launch_status in {"UPCOMING", "COMING_SOON"}:
        return ReleaseState.UPCOMING
    return ReleaseState.UNKNOWN


def _parse_nike_datetime(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise CatalogFetchError("Nike launch payload is missing a commerceStartDate.")
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


_NEXT_DATA_PATTERN = re.compile(r"__NEXT_DATA__")
