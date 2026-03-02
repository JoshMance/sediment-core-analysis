# Quick Tests

## Store Tests

```bash
# Container only (no Qt — prints to stdout)
uv run python -m src.tests.container_test

# Store with signals (GUI — buttons + LogWindow)
uv run python -m src.tests.store_test
```

## FilePanel Tests

```bash
# Views only
uv run python -m src.tests.file_panel_test

# Presenters + Views
uv run python -m src.tests.file_presenter_and_panel_test
```
