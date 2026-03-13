from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from sneaker_launchpad.models import CatalogSnapshot, PurchaseRequest, SneakerRelease, StoreName


class AppRepository(Protocol):
    def initialize(self) -> None: ...

    def save_snapshot(self, snapshot: CatalogSnapshot) -> None: ...

    def get_snapshot(self, provider: StoreName) -> CatalogSnapshot | None: ...

    def list_snapshots(self) -> list[CatalogSnapshot]: ...

    def list_releases(self) -> list[SneakerRelease]: ...

    def get_release(self, provider: StoreName, release_id: str) -> SneakerRelease | None: ...

    def save_purchase(self, purchase: PurchaseRequest) -> None: ...

    def list_purchases(self) -> list[PurchaseRequest]: ...


class SQLiteRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog_snapshots (
                    provider TEXT PRIMARY KEY,
                    fetched_at TEXT NOT NULL,
                    live_fetch_succeeded INTEGER NOT NULL,
                    status_message TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS purchases (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    release_id TEXT NOT NULL,
                    release_name TEXT NOT NULL,
                    product_url TEXT NOT NULL,
                    size TEXT NOT NULL,
                    auto_submit INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    completed_at TEXT,
                    result_message TEXT NOT NULL
                )
                """
            )

    def save_snapshot(self, snapshot: CatalogSnapshot) -> None:
        payload = json.dumps(snapshot.to_record())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO catalog_snapshots (
                    provider,
                    fetched_at,
                    live_fetch_succeeded,
                    status_message,
                    payload
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    fetched_at = excluded.fetched_at,
                    live_fetch_succeeded = excluded.live_fetch_succeeded,
                    status_message = excluded.status_message,
                    payload = excluded.payload
                """,
                (
                    snapshot.provider.value,
                    snapshot.fetched_at.isoformat(),
                    int(snapshot.live_fetch_succeeded),
                    snapshot.status_message,
                    payload,
                ),
            )

    def get_snapshot(self, provider: StoreName) -> CatalogSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM catalog_snapshots WHERE provider = ?",
                (provider.value,),
            ).fetchone()
        if row is None:
            return None
        return CatalogSnapshot.from_record(json.loads(cast(str, row["payload"])))

    def list_snapshots(self) -> list[CatalogSnapshot]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM catalog_snapshots ORDER BY provider ASC"
            ).fetchall()
        snapshots = [
            CatalogSnapshot.from_record(json.loads(cast(str, row["payload"]))) for row in rows
        ]
        return sorted(snapshots, key=lambda snapshot: snapshot.provider.value)

    def list_releases(self) -> list[SneakerRelease]:
        releases: list[SneakerRelease] = []
        for snapshot in self.list_snapshots():
            releases.extend(snapshot.releases)
        return sorted(releases, key=lambda release: release.release_at)

    def get_release(self, provider: StoreName, release_id: str) -> SneakerRelease | None:
        snapshot = self.get_snapshot(provider)
        if snapshot is None:
            return None
        for release in snapshot.releases:
            if release.id == release_id:
                return release
        return None

    def save_purchase(self, purchase: PurchaseRequest) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO purchases (
                    id,
                    provider,
                    release_id,
                    release_name,
                    product_url,
                    size,
                    auto_submit,
                    status,
                    submitted_at,
                    completed_at,
                    result_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    release_id = excluded.release_id,
                    release_name = excluded.release_name,
                    product_url = excluded.product_url,
                    size = excluded.size,
                    auto_submit = excluded.auto_submit,
                    status = excluded.status,
                    submitted_at = excluded.submitted_at,
                    completed_at = excluded.completed_at,
                    result_message = excluded.result_message
                """,
                (
                    purchase.id,
                    purchase.provider.value,
                    purchase.release_id,
                    purchase.release_name,
                    purchase.product_url,
                    purchase.size,
                    int(purchase.auto_submit),
                    purchase.status.value,
                    purchase.submitted_at.isoformat(),
                    None if purchase.completed_at is None else purchase.completed_at.isoformat(),
                    purchase.result_message,
                ),
            )

    def list_purchases(self) -> list[PurchaseRequest]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    provider,
                    release_id,
                    release_name,
                    product_url,
                    size,
                    auto_submit,
                    status,
                    submitted_at,
                    completed_at,
                    result_message
                FROM purchases
                ORDER BY submitted_at DESC
                """
            ).fetchall()
        return [
            PurchaseRequest.from_record(
                {
                    "id": cast(str, row["id"]),
                    "provider": cast(str, row["provider"]),
                    "release_id": cast(str, row["release_id"]),
                    "release_name": cast(str, row["release_name"]),
                    "product_url": cast(str, row["product_url"]),
                    "size": cast(str, row["size"]),
                    "auto_submit": bool(row["auto_submit"]),
                    "status": cast(str, row["status"]),
                    "submitted_at": cast(str, row["submitted_at"]),
                    "completed_at": cast(str | None, row["completed_at"]),
                    "result_message": cast(str, row["result_message"]),
                }
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection


@dataclass
class InMemoryRepository:
    snapshots: dict[StoreName, CatalogSnapshot]
    purchases: dict[str, PurchaseRequest]

    def __init__(self) -> None:
        self.snapshots = {}
        self.purchases = {}

    def initialize(self) -> None:
        return None

    def save_snapshot(self, snapshot: CatalogSnapshot) -> None:
        self.snapshots[snapshot.provider] = snapshot

    def get_snapshot(self, provider: StoreName) -> CatalogSnapshot | None:
        return self.snapshots.get(provider)

    def list_snapshots(self) -> list[CatalogSnapshot]:
        return sorted(self.snapshots.values(), key=lambda snapshot: snapshot.provider.value)

    def list_releases(self) -> list[SneakerRelease]:
        releases: list[SneakerRelease] = []
        for snapshot in self.list_snapshots():
            releases.extend(snapshot.releases)
        return sorted(releases, key=lambda release: release.release_at)

    def get_release(self, provider: StoreName, release_id: str) -> SneakerRelease | None:
        snapshot = self.snapshots.get(provider)
        if snapshot is None:
            return None
        for release in snapshot.releases:
            if release.id == release_id:
                return release
        return None

    def save_purchase(self, purchase: PurchaseRequest) -> None:
        self.purchases[purchase.id] = purchase

    def list_purchases(self) -> list[PurchaseRequest]:
        return sorted(
            self.purchases.values(),
            key=lambda purchase: purchase.submitted_at,
            reverse=True,
        )
