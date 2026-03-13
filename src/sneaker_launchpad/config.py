from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from sneaker_launchpad.models import StoreName


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class StoreAutomationConfig:
    profile_dir: Path | None
    headless: bool


@dataclass(frozen=True, slots=True)
class AppSettings:
    project_name: str
    recommended_repo_name: str
    database_path: Path
    http_timeout_seconds: float
    automation_timeout_seconds: float
    finalize_purchase: bool
    automation: dict[StoreName, StoreAutomationConfig]


def load_settings(base_dir: Path | None = None) -> AppSettings:
    working_dir = Path.cwd() if base_dir is None else base_dir
    data_dir = working_dir / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    default_headless = _env_flag("SNEAKER_LAUNCHPAD_HEADLESS", True)
    return AppSettings(
        project_name="Sneaker Launchpad",
        recommended_repo_name="sneaker-launchpad",
        database_path=Path(
            os.getenv(
                "SNEAKER_LAUNCHPAD_DB",
                str(data_dir / "sneaker_launchpad.sqlite3"),
            )
        ),
        http_timeout_seconds=float(os.getenv("SNEAKER_LAUNCHPAD_HTTP_TIMEOUT", "20")),
        automation_timeout_seconds=float(
            os.getenv("SNEAKER_LAUNCHPAD_AUTOMATION_TIMEOUT", "15000")
        ),
        finalize_purchase=_env_flag("SNEAKER_LAUNCHPAD_FINALIZE_PURCHASE", False),
        automation={
            StoreName.NIKE: StoreAutomationConfig(
                profile_dir=_env_path("SNEAKER_LAUNCHPAD_NIKE_PROFILE_DIR"),
                headless=default_headless,
            ),
            StoreName.ADIDAS: StoreAutomationConfig(
                profile_dir=_env_path("SNEAKER_LAUNCHPAD_ADIDAS_PROFILE_DIR"),
                headless=default_headless,
            ),
        },
    )


def _env_path(name: str) -> Path | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return Path(value).expanduser()
