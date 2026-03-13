from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sneaker_launchpad.automation import PlaywrightPurchaseAutomator
from sneaker_launchpad.config import AppSettings, load_settings
from sneaker_launchpad.http import HttpTextFetcher
from sneaker_launchpad.models import (
    CatalogSnapshot,
    PurchaseRequest,
    PurchaseStatus,
    SneakerRelease,
    StoreName,
)
from sneaker_launchpad.providers import AdidasCatalogProvider, NikeCatalogProvider
from sneaker_launchpad.repositories import AppRepository, SQLiteRepository
from sneaker_launchpad.services import CatalogService, PurchaseService, PurchaseSubmission

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@dataclass(slots=True)
class AppContainer:
    settings: AppSettings
    repository: AppRepository
    catalog_service: CatalogService
    purchase_service: PurchaseService
    fetcher: HttpTextFetcher | None


def build_container(settings: AppSettings | None = None) -> AppContainer:
    resolved_settings = load_settings() if settings is None else settings
    repository = SQLiteRepository(resolved_settings.database_path)
    fetcher = HttpTextFetcher(resolved_settings.http_timeout_seconds)
    providers = [
        NikeCatalogProvider(fetcher.fetch),
        AdidasCatalogProvider(fetcher.fetch),
    ]
    automators = {
        StoreName.NIKE: PlaywrightPurchaseAutomator(StoreName.NIKE, resolved_settings),
        StoreName.ADIDAS: PlaywrightPurchaseAutomator(StoreName.ADIDAS, resolved_settings),
    }
    return AppContainer(
        settings=resolved_settings,
        repository=repository,
        catalog_service=CatalogService(repository, providers),
        purchase_service=PurchaseService(repository, automators),
        fetcher=fetcher,
    )


def create_app(
    container: AppContainer | None = None,
    *,
    auto_refresh: bool = True,
) -> FastAPI:
    resolved_container = build_container() if container is None else container

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        resolved_container.repository.initialize()
        if auto_refresh and not resolved_container.repository.list_releases():
            resolved_container.catalog_service.refresh()
        yield
        if resolved_container.fetcher is not None:
            resolved_container.fetcher.close()

    app = FastAPI(title=resolved_container.settings.project_name, lifespan=lifespan)
    app.state.container = resolved_container
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        context = {
            "request": request,
            "settings": resolved_container.settings,
            "releases": _serialize_releases(resolved_container.catalog_service.releases()),
            "snapshots": _serialize_snapshots(resolved_container.catalog_service.snapshots()),
            "purchases": _serialize_purchases(resolved_container.purchase_service.history()),
            "notice": request.query_params.get("notice"),
            "notice_level": request.query_params.get("notice_level", "info"),
        }
        return TEMPLATES.TemplateResponse(request, "dashboard.html", context)

    @app.post("/refresh")
    def refresh_catalog() -> RedirectResponse:
        snapshots = resolved_container.catalog_service.refresh()
        success_count = sum(1 for snapshot in snapshots if snapshot.live_fetch_succeeded)
        return _redirect_with_notice(
            f"Catalog refresh finished. {success_count} provider(s) refreshed live data.",
            "info",
        )

    @app.post("/purchases")
    def create_purchase(
        provider: Annotated[str, Form(...)],
        size: Annotated[str, Form(...)],
        release_id: Annotated[str | None, Form()] = None,
        manual_name: Annotated[str | None, Form()] = None,
        manual_url: Annotated[str | None, Form()] = None,
        auto_submit: Annotated[bool, Form()] = False,
    ) -> RedirectResponse:
        try:
            result = resolved_container.purchase_service.submit(
                PurchaseSubmission(
                    provider=StoreName(provider),
                    release_id=(release_id or "").strip() or None,
                    size=size,
                    auto_submit=auto_submit,
                    manual_name=(manual_name or "").strip() or None,
                    manual_url=(manual_url or "").strip() or None,
                )
            )
        except ValueError as exc:
            return _redirect_with_notice(str(exc), "error")
        level = "success" if result.status != PurchaseStatus.FAILED else "error"
        return _redirect_with_notice(result.result_message, level)

    @app.get("/api/releases")
    def api_releases() -> JSONResponse:
        return JSONResponse(
            {"releases": _serialize_releases(resolved_container.catalog_service.releases())}
        )

    @app.get("/api/purchases")
    def api_purchases() -> JSONResponse:
        return JSONResponse(
            {"purchases": _serialize_purchases(resolved_container.purchase_service.history())}
        )

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


def _redirect_with_notice(message: str, level: str) -> RedirectResponse:
    encoded = quote_plus(message)
    return RedirectResponse(
        url=f"/?notice={encoded}&notice_level={quote_plus(level)}",
        status_code=303,
    )


def _serialize_releases(releases: list[SneakerRelease]) -> list[dict[str, str]]:
    return [
        {
            "id": release.id,
            "provider": release.provider.value,
            "name": release.name,
            "subtitle": release.subtitle,
            "style_code": release.style_code,
            "colorway": release.colorway,
            "product_url": release.product_url,
            "image_url": release.image_url,
            "release_at": release.release_label,
            "price": release.display_price,
            "state": release.state.value,
            "sizes": ", ".join(release.sizes) if release.sizes else "Unknown",
        }
        for release in releases
    ]


def _serialize_snapshots(snapshots: list[CatalogSnapshot]) -> list[dict[str, str | bool | int]]:
    return [
        {
            "provider": snapshot.provider.value,
            "fetched_at": snapshot.fetched_label,
            "count": len(snapshot.releases),
            "live_fetch_succeeded": snapshot.live_fetch_succeeded,
            "status_message": snapshot.status_message,
        }
        for snapshot in snapshots
    ]


def _serialize_purchases(purchases: list[PurchaseRequest]) -> list[dict[str, str | bool]]:
    return [
        {
            "id": purchase.id,
            "provider": purchase.provider.value,
            "release_name": purchase.release_name,
            "product_url": purchase.product_url,
            "size": purchase.size,
            "auto_submit": purchase.auto_submit,
            "status": purchase.status.value,
            "submitted_at": purchase.submitted_label,
            "result_message": purchase.result_message,
        }
        for purchase in purchases
    ]


app = create_app()
