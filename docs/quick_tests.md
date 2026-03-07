# Quick Tests

## Dev Mode

```bash
# Run the app with signal logging -- opens a DevLog window
uv run python main.py --dev
```

## Store Tests

```bash
# Container only (no Qt — prints to stdout)
uv run python -m tests.container_test

# Store with signals (GUI — buttons + LogWindow)
uv run python -m tests.store_test
```

## FilePanel Tests

```bash
# Views only
uv run python -m tests.file_panel_test

# Presenters + Views + Controller + Store
uv run python -m tests.file_presenter_and_panel_test
```

## Image Loading (end-to-end)

```bash
# Full chain: FilePanel → FilePresenter → Controller → Store
uv run python -m tests.image_loading_test
```

## WorkspacePanel Tests

```bash
# View + Presenter only (stub Controller — logs but doesn't delete)
uv run python -m tests.workspace_panel_test

# Full integration: FilePanel + WorkspacePanel with Controller + Store
# Load images, delete them, watch every signal and method call in the log
uv run python -m tests.workspace_test
```
