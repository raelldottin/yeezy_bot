from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from support import sample_snapshot

from sneaker_launchpad.config import AppSettings, StoreAutomationConfig
from sneaker_launchpad.models import AutomationResult, CatalogSnapshot, PurchaseStatus, StoreName
from sneaker_launchpad.repositories import SQLiteRepository
from sneaker_launchpad.services import CatalogService, PurchaseService
from sneaker_launchpad.web.app import AppContainer, create_app


class StaticProvider:
    def __init__(self, snapshot: CatalogSnapshot) -> None:
        self.store = snapshot.provider
        self._snapshot = snapshot

    def fetch_snapshot(self, now: datetime) -> CatalogSnapshot:
        return CatalogSnapshot(
            provider=self._snapshot.provider,
            fetched_at=now,
            releases=self._snapshot.releases,
            live_fetch_succeeded=True,
            status_message=self._snapshot.status_message,
        )


class StaticAutomator:
    def __init__(self, store: StoreName) -> None:
        self.store = store

    def submit_purchase(self, *, release, request):  # type: ignore[no-untyped-def]
        return AutomationResult(
            status=PurchaseStatus.COMPLETED,
            message=f"Automation completed for {release.name} size {request.size}.",
        )


def _settings(database_path: Path) -> AppSettings:
    return AppSettings(
        project_name="Sneaker Launchpad",
        repository_name="sneaker-launchpad",
        database_path=database_path,
        http_timeout_seconds=10,
        automation_timeout_seconds=5000,
        finalize_purchase=False,
        automation={
            StoreName.NIKE: StoreAutomationConfig(profile_dir=None, headless=True),
            StoreName.ADIDAS: StoreAutomationConfig(profile_dir=None, headless=True),
        },
    )


def test_dashboard_lists_releases_and_purchase_history(tmp_path: Path) -> None:
    database_path = tmp_path / "launchpad.sqlite3"
    repository = SQLiteRepository(database_path)
    settings = _settings(database_path)
    snapshots = [sample_snapshot(StoreName.NIKE), sample_snapshot(StoreName.ADIDAS)]
    providers = [StaticProvider(snapshot) for snapshot in snapshots]
    automators = {
        StoreName.NIKE: StaticAutomator(StoreName.NIKE),
        StoreName.ADIDAS: StaticAutomator(StoreName.ADIDAS),
    }
    container = AppContainer(
        settings=settings,
        repository=repository,
        catalog_service=CatalogService(
            repository,
            providers,
            clock=lambda: datetime(2026, 3, 13, 14, 0, tzinfo=UTC),
        ),
        purchase_service=PurchaseService(
            repository,
            automators,
            clock=lambda: datetime(2026, 3, 13, 14, 5, tzinfo=UTC),
        ),
        fetcher=None,
    )
    app = create_app(container, auto_refresh=True)

    with TestClient(app) as client:
        releases_response = client.get("/api/releases")
        assert releases_response.status_code == 200
        releases_payload = releases_response.json()["releases"]
        assert len(releases_payload) == 2

        create_response = client.post(
            "/purchases",
            data={
                "provider": "nike",
                "release_id": "nike-1",
                "size": "10.5",
                "auto_submit": "true",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303

        purchases_response = client.get("/api/purchases")
        assert purchases_response.status_code == 200
        purchases_payload = purchases_response.json()["purchases"]
        assert len(purchases_payload) == 1
        assert purchases_payload[0]["status"] == "completed"

        dashboard_response = client.get("/")
        assert dashboard_response.status_code == 200
        assert "Air Max Test Pair" in dashboard_response.text
        assert "Purchase History" in dashboard_response.text
