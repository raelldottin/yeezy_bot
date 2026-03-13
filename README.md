# Sneaker Launchpad

Sneaker Launchpad turns the original `yeezy_bot` repository into a broader sneaker launch dashboard for Nike and Adidas. It provides:

- A FastAPI frontend for browsing upcoming sneakers and selecting which pair to target.
- A local SQLite-backed purchase history.
- Provider adapters for Nike SNKRS and Adidas release data.
- Browser automation hooks for Nike and Adidas using persistent Chromium profiles.
- Unit and integration tests built around domain services and adapter seams.

Recommended GitHub repo rename: `sneaker-launchpad`

## Why the rename

The original repo was narrowly scoped to Adidas Yeezy inventory checks. The new project covers:

- Multiple stores
- Upcoming release tracking
- Purchase selection and automation orchestration
- Purchase history and operational visibility

`yeezy_bot` no longer describes the product surface, so the internal project name is now **Sneaker Launchpad**.

## Architecture at a glance

- `src/sneaker_launchpad/models.py`: typed domain objects
- `src/sneaker_launchpad/services.py`: application services for catalog refresh and purchases
- `src/sneaker_launchpad/repositories.py`: SQLite and in-memory repositories
- `src/sneaker_launchpad/providers/`: Nike and Adidas catalog adapters
- `src/sneaker_launchpad/automation.py`: Playwright-backed browser automation
- `src/sneaker_launchpad/web/`: FastAPI routes, templates, and frontend assets

## Quick start

```bash
python3 -m pip install -e .[dev]
python3 -m playwright install chromium
cp config/settings.example.env .env.local
source .env.local
sneaker-launchpad serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Environment variables

The app reads these values directly from the environment:

- `SNEAKER_LAUNCHPAD_DB`: SQLite file path
- `SNEAKER_LAUNCHPAD_NIKE_PROFILE_DIR`: persistent Chromium profile for Nike
- `SNEAKER_LAUNCHPAD_ADIDAS_PROFILE_DIR`: persistent Chromium profile for Adidas
- `SNEAKER_LAUNCHPAD_HEADLESS`: `true` or `false`
- `SNEAKER_LAUNCHPAD_FINALIZE_PURCHASE`: whether automation should attempt the last order-submission click

Browser profiles are the safest way to keep logins and saved payment methods outside the app. Start with `SNEAKER_LAUNCHPAD_FINALIZE_PURCHASE=false`, verify that cart and checkout navigation behaves correctly, and only then decide whether to enable final order submission.

## Commands

```bash
sneaker-launchpad serve
sneaker-launchpad refresh
sneaker-launchpad buy --provider nike --release-id nike-1 --size 10.5 --run
make check
```

## Testing

This project follows the testing style from *Unit Testing: Principles, Practices, and Patterns*:

- Business rules live in services and are covered with fast unit tests using in-memory repositories and fake automators.
- Parsing adapters are tested against fixed HTML fixtures to avoid brittle network-dependent tests.
- Integration tests exercise the real FastAPI routing and SQLite persistence together.

Run everything with:

```bash
make check
```

More detail lives in [docs/ARCHITECTURE.md](/Users/raelldottin/Documents/Personal/Code Project/docs/ARCHITECTURE.md), [docs/USER_GUIDE.md](/Users/raelldottin/Documents/Personal/Code Project/docs/USER_GUIDE.md), and [docs/TESTING.md](/Users/raelldottin/Documents/Personal/Code Project/docs/TESTING.md).

## Live data caveats

- Nike SNKRS exposes enough page data for server-side parsing today.
- Adidas sometimes serves WAF or 403 pages to automated refreshes. When that happens, the app keeps cached data, and you can still add manual Adidas product URLs from the dashboard.
- Storefront markup changes over time, so browser automation is intentionally isolated behind provider-specific heuristics that are easy to update.
