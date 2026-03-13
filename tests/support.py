from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sneaker_launchpad.models import CatalogSnapshot, ReleaseState, SneakerRelease, StoreName


def build_nike_launch_html() -> str:
    state = {
        "product": {
            "threads": {
                "data": {
                    "items": {
                        "thread-1": {
                            "productId": "nike-1",
                            "productIds": ["nike-1"],
                            "seo": {"slug": "air-max-test-pair"},
                            "coverCard": {
                                "title": "Infrared",
                                "defaultURL": "https://images.example.com/nike-1.jpg",
                            },
                        }
                    }
                }
            },
            "products": {
                "data": {
                    "items": {
                        "nike-1": {
                            "commerceStartDate": "2026-03-21T14:00:00.000Z",
                            "currency": "USD",
                            "currentPrice": 150,
                            "fullPrice": 150,
                            "id": "nike-1",
                            "isLaunchProduct": True,
                            "imageSrc": "https://images.example.com/nike-1.jpg",
                            "launchStatus": "UPCOMING",
                            "productType": "FOOTWEAR",
                            "styleColor": "HM1234-001",
                            "subtitle": "Men's Shoes",
                            "title": "Air Max Test Pair",
                            "skus": [
                                {"available": True, "nike_size": "10"},
                                {"available": True, "nike_size": "10.5"},
                                {"available": False, "nike_size": "11"},
                            ],
                        }
                    }
                }
            },
        }
    }
    payload = {"props": {"pageProps": {"initialState": json.dumps(state)}}}
    return (
        "<html><body><script id=\"__NEXT_DATA__\" type=\"application/json\">"
        + json.dumps(payload)
        + "</script></body></html>"
    )


def build_adidas_release_html() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "item": {
                    "@type": "Product",
                    "name": "Adizero Prime Test",
                    "category": "Running Shoes",
                    "sku": "JR9999",
                    "color": "Chalk White",
                    "url": "https://www.adidas.com/us/adizero-prime-test/JR9999.html",
                    "image": "https://images.example.com/adidas-1.jpg",
                    "releaseDate": "2026-04-05T15:00:00+00:00",
                    "offers": {"price": "180", "priceCurrency": "USD"},
                },
            }
        ],
    }
    return (
        "<html><head><script type=\"application/ld+json\">"
        + json.dumps(payload)
        + "</script></head><body>release dates</body></html>"
    )


def sample_release(provider: StoreName = StoreName.NIKE) -> SneakerRelease:
    name = "Air Max Test Pair" if provider == StoreName.NIKE else "Adizero Prime Test"
    return SneakerRelease(
        id=f"{provider.value}-1",
        provider=provider,
        name=name,
        subtitle="Test sneaker",
        style_code="TEST-001",
        colorway="Test Red",
        product_url=f"https://www.{provider.value}.com/test-shoe",
        image_url="https://images.example.com/test.jpg",
        release_at=datetime(2026, 3, 21, 14, 0, tzinfo=UTC),
        price=Decimal("150.00"),
        currency="USD",
        sizes=("10", "10.5"),
        state=ReleaseState.UPCOMING,
    )


def sample_snapshot(provider: StoreName = StoreName.NIKE) -> CatalogSnapshot:
    return CatalogSnapshot(
        provider=provider,
        fetched_at=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
        releases=(sample_release(provider),),
        live_fetch_succeeded=True,
        status_message="Loaded test fixture data.",
    )
