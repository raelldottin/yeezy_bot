from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

from sneaker_launchpad.models import StoreName
from sneaker_launchpad.services import PurchaseSubmission
from sneaker_launchpad.web.app import build_container, create_app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sneaker-launchpad",
        description="Sneaker Launchpad dashboard and automation CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI dashboard.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    subparsers.add_parser("refresh", help="Refresh Nike and Adidas catalog data.")

    buy_parser = subparsers.add_parser("buy", help="Create a purchase from the CLI.")
    buy_parser.add_argument(
        "--provider",
        choices=[store.value for store in StoreName],
        required=True,
    )
    buy_parser.add_argument("--size", required=True)
    buy_parser.add_argument("--release-id")
    buy_parser.add_argument("--manual-name")
    buy_parser.add_argument("--manual-url")
    buy_parser.add_argument(
        "--run",
        action="store_true",
        help="Run browser automation immediately instead of only saving history.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    container = build_container()
    container.repository.initialize()

    if args.command == "serve":
        app = create_app(container)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    if args.command == "refresh":
        snapshots = container.catalog_service.refresh()
        for snapshot in snapshots:
            print(
                f"{snapshot.provider.value}: {len(snapshot.releases)} release(s) | "
                f"{snapshot.status_message}"
            )
        return 0

    result = container.purchase_service.submit(
        PurchaseSubmission(
            provider=StoreName(args.provider),
            release_id=args.release_id,
            size=args.size,
            auto_submit=args.run,
            manual_name=args.manual_name,
            manual_url=args.manual_url,
        )
    )
    print(f"{result.status.value}: {result.result_message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
