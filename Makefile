PYTHON ?= python3

.PHONY: install lint typecheck test integration check serve refresh

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

lint:
	ruff check .

typecheck:
	pyright

test:
	pytest

integration:
	pytest -m integration

check: lint typecheck test

serve:
	sneaker-launchpad serve

refresh:
	sneaker-launchpad refresh
