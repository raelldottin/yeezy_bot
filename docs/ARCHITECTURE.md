# Architecture

## Design goals

The rebuild centers on three goals:

1. Support multiple storefronts without coupling provider-specific parsing to the rest of the app.
2. Keep business logic easy to test with fast unit tests.
3. Make brittle integrations, like HTML scraping and browser automation, thin and replaceable.

## Layering

### Domain layer

`src/sneaker_launchpad/models.py` contains immutable value objects:

- `SneakerRelease`
- `CatalogSnapshot`
- `PurchaseRequest`
- enums for store names, release state, and purchase status

These types do not know about FastAPI, sqlite, or Playwright.

### Application layer

`src/sneaker_launchpad/services.py` holds the use cases:

- `CatalogService.refresh()`
- `PurchaseService.submit()`

This is the layer that follows the book’s guidance most directly. The services talk to abstractions and simple collaborators, not to framework internals.

### Infrastructure layer

- `src/sneaker_launchpad/repositories.py`: SQLite persistence
- `src/sneaker_launchpad/providers/*.py`: HTML parsing and live-store adapters
- `src/sneaker_launchpad/automation.py`: Playwright purchase orchestration
- `src/sneaker_launchpad/http.py`: HTTP fetching details

Each infrastructure concern is kept close to its boundary so failures stay localized.

### Presentation layer

`src/sneaker_launchpad/web/app.py` owns:

- FastAPI app construction
- route handlers
- template rendering
- JSON endpoints for release and purchase feeds

The presentation layer delegates work immediately to services.

## Testing strategy

The test suite maps to the architecture:

- Unit tests target providers and services.
- Integration tests target FastAPI plus SQLite.
- No live-store test is required for CI success.

That keeps the suite stable while still proving the important seams.
