# Testing

## Principles

The project intentionally follows the style from *Unit Testing: Principles, Practices, and Patterns*:

- Put logic in small application services.
- Use stable fakes for dependencies in unit tests.
- Keep integration tests focused on boundaries that matter.
- Avoid making CI depend on live third-party storefronts.

## Test layers

### Unit tests

Unit tests cover:

- Nike HTML parsing
- Adidas HTML parsing and blocked-page handling
- catalog refresh fallback behavior
- purchase submission orchestration

These tests run against in-memory repositories and fake automators.

### Integration tests

Integration tests cover:

- FastAPI routing
- real SQLite persistence
- end-to-end request flow from catalog refresh to purchase history

## Commands

```bash
ruff check .
pyright
pytest
pytest -m integration
make check
```

## Browser automation note

Playwright is included so the automation feature can run locally, but CI does not depend on live browser checkout. That keeps the integration suite deterministic while still shipping the real adapter in production code.
