from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from urllib.parse import urlparse
from uuid import uuid4

from sneaker_launchpad.automation import PurchaseAutomator
from sneaker_launchpad.models import (
    CatalogSnapshot,
    PurchaseRequest,
    PurchaseStatus,
    ReleaseState,
    SneakerRelease,
    StoreName,
    utc_now,
)
from sneaker_launchpad.providers.nike import CatalogFetchError
from sneaker_launchpad.repositories import AppRepository


class CatalogProvider(Protocol):
    store: StoreName

    def fetch_snapshot(self, now: datetime) -> CatalogSnapshot: ...


@dataclass(frozen=True, slots=True)
class PurchaseSubmission:
    provider: StoreName
    release_id: str | None
    size: str
    auto_submit: bool
    manual_name: str | None
    manual_url: str | None


class CatalogService:
    def __init__(
        self,
        repository: AppRepository,
        providers: Sequence[CatalogProvider],
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._providers = list(providers)
        self._clock = clock

    def refresh(self) -> list[CatalogSnapshot]:
        fetched_at = self._clock()
        snapshots: list[CatalogSnapshot] = []
        for provider in self._providers:
            try:
                snapshot = provider.fetch_snapshot(fetched_at)
            except CatalogFetchError as exc:
                previous = self._repository.get_snapshot(provider.store)
                releases = tuple() if previous is None else previous.releases
                snapshot = CatalogSnapshot(
                    provider=provider.store,
                    fetched_at=fetched_at,
                    releases=releases,
                    live_fetch_succeeded=False,
                    status_message=str(exc),
                )
            self._repository.save_snapshot(snapshot)
            snapshots.append(snapshot)
        return snapshots

    def snapshots(self) -> list[CatalogSnapshot]:
        return self._repository.list_snapshots()

    def releases(self) -> list[SneakerRelease]:
        return self._repository.list_releases()


class PurchaseService:
    def __init__(
        self,
        repository: AppRepository,
        automators: Mapping[StoreName, PurchaseAutomator],
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._automators = dict(automators)
        self._clock = clock

    def submit(self, submission: PurchaseSubmission) -> PurchaseRequest:
        release = self._resolve_release(submission)
        now = self._clock()
        purchase = PurchaseRequest(
            id=str(uuid4()),
            provider=release.provider,
            release_id=release.id,
            release_name=release.name,
            product_url=release.product_url,
            size=submission.size.strip(),
            auto_submit=submission.auto_submit,
            status=PurchaseStatus.QUEUED,
            submitted_at=now,
            completed_at=None,
            result_message="Queued for automation.",
        )
        self._repository.save_purchase(purchase)

        if not submission.auto_submit:
            saved = purchase.evolve(
                status=PurchaseStatus.SAVED,
                result_message=(
                    "Saved to purchase history only. Re-submit with automation enabled "
                    "to drive a browser profile."
                ),
                completed_at=now,
            )
            self._repository.save_purchase(saved)
            return saved

        running = purchase.evolve(
            status=PurchaseStatus.RUNNING,
            result_message="Starting browser automation.",
            completed_at=None,
        )
        self._repository.save_purchase(running)
        automator = self._automators.get(submission.provider)
        if automator is None:
            failed = running.evolve(
                status=PurchaseStatus.FAILED,
                result_message=f"No automator configured for {submission.provider.value}.",
                completed_at=self._clock(),
            )
            self._repository.save_purchase(failed)
            return failed
        result = automator.submit_purchase(release=release, request=running)
        completed = running.evolve(
            status=result.status,
            result_message=result.message,
            completed_at=self._clock(),
        )
        self._repository.save_purchase(completed)
        return completed

    def history(self) -> list[PurchaseRequest]:
        return self._repository.list_purchases()

    def _resolve_release(self, submission: PurchaseSubmission) -> SneakerRelease:
        if submission.release_id:
            release = self._repository.get_release(submission.provider, submission.release_id)
            if release is None:
                raise ValueError("Selected release no longer exists in the catalog.")
            return release
        if not submission.manual_name or not submission.manual_url:
            raise ValueError("A manual purchase needs both a product name and a product URL.")
        _validate_provider_url(submission.provider, submission.manual_url)
        return SneakerRelease(
            id=f"manual-{uuid4()}",
            provider=submission.provider,
            name=submission.manual_name.strip(),
            subtitle="Manual target",
            style_code="manual-target",
            colorway="Manual target",
            product_url=submission.manual_url.strip(),
            image_url="",
            release_at=self._clock(),
            price=Decimal("0"),
            currency="USD",
            sizes=tuple(filter(None, [submission.size.strip()])),
            state=ReleaseState.UNKNOWN,
        )


def _validate_provider_url(provider: StoreName, url: str) -> None:
    hostname = urlparse(url).hostname or ""
    if provider == StoreName.NIKE and "nike.com" not in hostname:
        raise ValueError("Nike purchases must use a nike.com product URL.")
    if provider == StoreName.ADIDAS and "adidas.com" not in hostname:
        raise ValueError("Adidas purchases must use an adidas.com product URL.")
