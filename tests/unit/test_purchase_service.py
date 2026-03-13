from datetime import UTC, datetime

import pytest
from support import sample_snapshot

from sneaker_launchpad.models import AutomationResult, PurchaseStatus, StoreName
from sneaker_launchpad.repositories import InMemoryRepository
from sneaker_launchpad.services import PurchaseService, PurchaseSubmission


class FakeAutomator:
    store = StoreName.NIKE

    def submit_purchase(self, *, release, request) -> AutomationResult:  # type: ignore[no-untyped-def]
        return AutomationResult(
            status=PurchaseStatus.COMPLETED,
            message=f"Submitted {release.name} in size {request.size}.",
        )


def test_purchase_service_runs_automator_for_catalog_release() -> None:
    repository = InMemoryRepository()
    repository.save_snapshot(sample_snapshot(StoreName.NIKE))
    service = PurchaseService(
        repository,
        {StoreName.NIKE: FakeAutomator()},
        clock=lambda: datetime(2026, 3, 13, 13, 30, tzinfo=UTC),
    )

    purchase = service.submit(
        PurchaseSubmission(
            provider=StoreName.NIKE,
            release_id="nike-1",
            size="10.5",
            auto_submit=True,
            manual_name=None,
            manual_url=None,
        )
    )

    assert purchase.status == PurchaseStatus.COMPLETED
    assert "Submitted Air Max Test Pair" in purchase.result_message


def test_purchase_service_rejects_cross_store_manual_urls() -> None:
    repository = InMemoryRepository()
    service = PurchaseService(
        repository,
        {},
        clock=lambda: datetime(2026, 3, 13, 13, 30, tzinfo=UTC),
    )

    with pytest.raises(ValueError):
        service.submit(
            PurchaseSubmission(
                provider=StoreName.NIKE,
                release_id=None,
                size="10",
                auto_submit=False,
                manual_name="Wrong Store",
                manual_url="https://www.adidas.com/us/wrong-store",
            )
        )
