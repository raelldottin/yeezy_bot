from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from sneaker_launchpad.config import AppSettings
from sneaker_launchpad.models import (
    AutomationResult,
    PurchaseRequest,
    PurchaseStatus,
    SneakerRelease,
    StoreName,
)

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page


class PurchaseAutomator(Protocol):
    @property
    def store(self) -> StoreName: ...

    def submit_purchase(
        self,
        *,
        release: SneakerRelease,
        request: PurchaseRequest,
    ) -> AutomationResult: ...


@dataclass(frozen=True, slots=True)
class PlaywrightPurchaseAutomator:
    store: StoreName
    settings: AppSettings

    def submit_purchase(
        self,
        *,
        release: SneakerRelease,
        request: PurchaseRequest,
    ) -> AutomationResult:
        config = self.settings.automation[self.store]
        if config.profile_dir is None:
            return AutomationResult(
                status=PurchaseStatus.FAILED,
                message=(
                    f"No persistent browser profile configured for {self.store.value}. "
                    "Set the matching SNEAKER_LAUNCHPAD_*_PROFILE_DIR env var first."
                ),
            )

        try:
            from playwright.sync_api import Error, sync_playwright
        except ImportError as exc:
            return AutomationResult(
                status=PurchaseStatus.FAILED,
                message=f"Playwright is not installed correctly: {exc}",
            )

        profile_dir = Path(config.profile_dir).expanduser()
        profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=config.headless,
                )
                try:
                    page = _first_page(context)
                    page.goto(
                        release.product_url,
                        timeout=self.settings.automation_timeout_seconds,
                        wait_until="domcontentloaded",
                    )
                    self._dismiss_common_popups(page)
                    if request.size.strip():
                        _click_matching_text(page, [re.escape(request.size.strip())])
                    clicked_purchase = _click_matching_text(page, _purchase_labels(self.store))
                    if not clicked_purchase:
                        return AutomationResult(
                            status=PurchaseStatus.FAILED,
                            message=(
                                "The automation opened the store page but could not find a "
                                "purchase button. Review the browser profile and tune selectors "
                                "if the site layout has changed."
                            ),
                        )
                    page.wait_for_timeout(1000)
                    _click_matching_text(page, _checkout_labels(self.store))
                    if self.settings.finalize_purchase:
                        _click_matching_text(page, _finalize_labels())
                    return AutomationResult(
                        status=PurchaseStatus.COMPLETED,
                        message=(
                            "Automation executed with the configured browser profile. "
                            "If you have saved sessions and payment methods, the order flow should "
                            "now be in cart or checkout."
                        ),
                    )
                finally:
                    context.close()
        except Error as exc:
            return AutomationResult(
                status=PurchaseStatus.FAILED,
                message=f"Browser automation failed: {exc}",
            )

    def _dismiss_common_popups(self, page: Page) -> None:
        _click_matching_text(
            page,
            [
                "Accept",
                "Accept All",
                "I Agree",
                "Got It",
                "Close",
                "Continue",
            ],
        )


def _first_page(context: BrowserContext) -> Page:
    if context.pages:
        return context.pages[0]
    return context.new_page()


def _click_matching_text(page: Any, labels: list[str]) -> bool:
    for label in labels:
        pattern = re.compile(label, re.IGNORECASE)
        selectors = [
            page.get_by_role("button", name=pattern).first,
            page.get_by_role("link", name=pattern).first,
        ]
        for locator in selectors:
            try:
                if locator.count() < 1:
                    continue
                locator.click(timeout=2000)
                return True
            except Exception:
                continue
    return False


def _purchase_labels(store: StoreName) -> list[str]:
    if store == StoreName.NIKE:
        return [
            "Add to Bag",
            "Buy",
            "Enter Draw",
            "Join Draw",
            "Get",
        ]
    return [
        "Add to Bag",
        "Add To Bag",
        "Purchase",
        "Buy Now",
    ]


def _checkout_labels(store: StoreName) -> list[str]:
    if store == StoreName.NIKE:
        return [
            "Checkout",
            "View Bag",
            "Go to Bag",
        ]
    return [
        "Checkout",
        "Go to Checkout",
        "View Bag",
    ]


def _finalize_labels() -> list[str]:
    return [
        "Place Order",
        "Submit Order",
        "Pay Now",
        "Complete Purchase",
    ]
