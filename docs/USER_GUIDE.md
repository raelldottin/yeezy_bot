# User Guide

## Install

```bash
python3 -m pip install -e .[dev]
python3 -m playwright install chromium
```

## Configure persistent browser profiles

Create dedicated Chromium profiles for each store. These profiles should hold your existing store login, shipping preferences, and any saved payment methods you want the browser automation to use.

Example:

```bash
mkdir -p "$HOME/.config/sneaker-launchpad/nike"
mkdir -p "$HOME/.config/sneaker-launchpad/adidas"
```

Then export the profile paths:

```bash
export SNEAKER_LAUNCHPAD_NIKE_PROFILE_DIR="$HOME/.config/sneaker-launchpad/nike"
export SNEAKER_LAUNCHPAD_ADIDAS_PROFILE_DIR="$HOME/.config/sneaker-launchpad/adidas"
export SNEAKER_LAUNCHPAD_HEADLESS=false
export SNEAKER_LAUNCHPAD_FINALIZE_PURCHASE=false
```

Start with final purchase submission disabled. That lets you verify that the automation reaches cart or checkout before allowing it to click the final order button.

## Run the dashboard

```bash
sneaker-launchpad serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Refresh releases

Use the **Refresh Catalog** button or run:

```bash
sneaker-launchpad refresh
```

## Select sneakers to purchase

There are two paths:

1. Click **Select For Purchase** on a release card.
2. Enter a manual Nike or Adidas product URL if a provider did not return a live listing.

Then choose:

- Store
- Size
- Whether to run browser automation immediately

Submitting the form always writes a history entry. If automation is enabled, the app also tries to drive the store page with Playwright.

## Review purchase history

The bottom table on the dashboard stores:

- submission time
- store
- target release
- size
- status
- result notes

This makes it easier to rerun the same target or see where provider automation needs adjustment.
