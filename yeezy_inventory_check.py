from __future__ import annotations

import argparse

from sneaker_launchpad.web.app import build_container


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deprecated compatibility wrapper for the original yeezy_bot entrypoint."
    )
    parser.add_argument("-e", "--email", nargs="?", default=None)
    parser.add_argument("-p", "--password", nargs="?", default=None)
    parser.add_argument("-r", "--recipient", nargs="?", default=None)
    parser.parse_args()

    container = build_container()
    container.repository.initialize()
    snapshots = container.catalog_service.refresh()
    print("yeezy_inventory_check.py is deprecated. Use `sneaker-launchpad refresh` instead.")
    for snapshot in snapshots:
        print(
            f"{snapshot.provider.value}: {len(snapshot.releases)} release(s) | "
            f"{snapshot.status_message}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
