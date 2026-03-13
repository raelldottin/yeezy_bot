from datetime import UTC, datetime

from support import sample_snapshot

from sneaker_launchpad.models import CatalogSnapshot, StoreName
from sneaker_launchpad.providers.nike import CatalogFetchError
from sneaker_launchpad.repositories import InMemoryRepository
from sneaker_launchpad.services import CatalogService


class FailingProvider:
    store = StoreName.ADIDAS

    def fetch_snapshot(self, now: datetime) -> CatalogSnapshot:
        _ = now
        raise CatalogFetchError("adidas.com blocked refresh")


def test_catalog_service_preserves_existing_snapshot_on_refresh_failure() -> None:
    repository = InMemoryRepository()
    existing = sample_snapshot(StoreName.ADIDAS)
    repository.save_snapshot(existing)
    service = CatalogService(
        repository,
        [FailingProvider()],
        clock=lambda: datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    snapshots = service.refresh()

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.live_fetch_succeeded is False
    assert snapshot.releases == existing.releases
    assert "blocked refresh" in snapshot.status_message
