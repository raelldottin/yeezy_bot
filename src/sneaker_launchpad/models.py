from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class StoreName(StrEnum):
    NIKE = "nike"
    ADIDAS = "adidas"


class ReleaseState(StrEnum):
    UPCOMING = "upcoming"
    LIVE = "live"
    UNKNOWN = "unknown"


class PurchaseStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SAVED = "saved"


@dataclass(frozen=True, slots=True)
class SneakerRelease:
    id: str
    provider: StoreName
    name: str
    subtitle: str
    style_code: str
    colorway: str
    product_url: str
    image_url: str
    release_at: datetime
    price: Decimal
    currency: str
    sizes: tuple[str, ...]
    state: ReleaseState

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider.value,
            "name": self.name,
            "subtitle": self.subtitle,
            "style_code": self.style_code,
            "colorway": self.colorway,
            "product_url": self.product_url,
            "image_url": self.image_url,
            "release_at": self.release_at.isoformat(),
            "price": str(self.price),
            "currency": self.currency,
            "sizes": list(self.sizes),
            "state": self.state.value,
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> SneakerRelease:
        return cls(
            id=str(payload["id"]),
            provider=StoreName(str(payload["provider"])),
            name=str(payload["name"]),
            subtitle=str(payload["subtitle"]),
            style_code=str(payload["style_code"]),
            colorway=str(payload["colorway"]),
            product_url=str(payload["product_url"]),
            image_url=str(payload["image_url"]),
            release_at=parse_datetime(str(payload["release_at"])),
            price=Decimal(str(payload["price"])),
            currency=str(payload["currency"]),
            sizes=tuple(str(size) for size in payload["sizes"]),
            state=ReleaseState(str(payload["state"])),
        )

    @property
    def display_price(self) -> str:
        return f"{self.currency} {self.price:.2f}"

    @property
    def release_label(self) -> str:
        return self.release_at.astimezone().strftime("%b %d, %Y %I:%M %p %Z")


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    provider: StoreName
    fetched_at: datetime
    releases: tuple[SneakerRelease, ...]
    live_fetch_succeeded: bool
    status_message: str

    def to_record(self) -> dict[str, Any]:
        return {
            "provider": self.provider.value,
            "fetched_at": self.fetched_at.isoformat(),
            "releases": [release.to_record() for release in self.releases],
            "live_fetch_succeeded": self.live_fetch_succeeded,
            "status_message": self.status_message,
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> CatalogSnapshot:
        return cls(
            provider=StoreName(str(payload["provider"])),
            fetched_at=parse_datetime(str(payload["fetched_at"])),
            releases=tuple(
                SneakerRelease.from_record(release_payload)
                for release_payload in payload["releases"]
            ),
            live_fetch_succeeded=bool(payload["live_fetch_succeeded"]),
            status_message=str(payload["status_message"]),
        )

    @property
    def fetched_label(self) -> str:
        return self.fetched_at.astimezone().strftime("%b %d, %Y %I:%M %p %Z")


@dataclass(frozen=True, slots=True)
class PurchaseRequest:
    id: str
    provider: StoreName
    release_id: str
    release_name: str
    product_url: str
    size: str
    auto_submit: bool
    status: PurchaseStatus
    submitted_at: datetime
    completed_at: datetime | None
    result_message: str

    def evolve(
        self,
        *,
        status: PurchaseStatus,
        result_message: str,
        completed_at: datetime | None,
    ) -> PurchaseRequest:
        return PurchaseRequest(
            id=self.id,
            provider=self.provider,
            release_id=self.release_id,
            release_name=self.release_name,
            product_url=self.product_url,
            size=self.size,
            auto_submit=self.auto_submit,
            status=status,
            submitted_at=self.submitted_at,
            completed_at=completed_at,
            result_message=result_message,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider.value,
            "release_id": self.release_id,
            "release_name": self.release_name,
            "product_url": self.product_url,
            "size": self.size,
            "auto_submit": self.auto_submit,
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "completed_at": None if self.completed_at is None else self.completed_at.isoformat(),
            "result_message": self.result_message,
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> PurchaseRequest:
        completed_at_raw = payload["completed_at"]
        completed_at = None
        if completed_at_raw is not None:
            completed_at = parse_datetime(str(completed_at_raw))
        return cls(
            id=str(payload["id"]),
            provider=StoreName(str(payload["provider"])),
            release_id=str(payload["release_id"]),
            release_name=str(payload["release_name"]),
            product_url=str(payload["product_url"]),
            size=str(payload["size"]),
            auto_submit=bool(payload["auto_submit"]),
            status=PurchaseStatus(str(payload["status"])),
            submitted_at=parse_datetime(str(payload["submitted_at"])),
            completed_at=completed_at,
            result_message=str(payload["result_message"]),
        )

    @property
    def submitted_label(self) -> str:
        return self.submitted_at.astimezone().strftime("%b %d, %Y %I:%M %p %Z")


@dataclass(frozen=True, slots=True)
class AutomationResult:
    status: PurchaseStatus
    message: str
