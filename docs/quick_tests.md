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

## FileBrowser Tests

```bash
# Views only
uv run python -m tests.file_browser_test

# Presenters + Views + Controller + Store
uv run python -m tests.file_browser_presenter_test
```

## Dataset Panel (end-to-end)

Manual — run the app, load a CSV via the file browser, and verify:

- Table renders with correct columns and values
- Column type menu shows Text / Number / Date
- Changing a type updates the display without altering raw data
- Cell edits round-trip (invalid values for the declared type are rejected)
- Rename column updates header

```bash
uv run python main.py
```

## Image Loading (end-to-end)

```bash
# Full chain: FileBrowser → FilePresenter → Controller → Store
uv run python -m tests.image_loading_test
```

## VariablesList Tests

```bash
# View + Presenter only (stub Controller — logs but doesn't delete)
uv run python -m tests.variables_list_test

# Full integration: FileBrowser + VariablesList with Controller + Store
# Load images, delete them, watch every signal and method call in the log
uv run python -m tests.variables_test
```

## Core Studio (manual)

1. Run the app: `uv run python main.py`
2. Click **Core Studio** in the **Prepare** ribbon tab
3. Verify: a blank Core Studio tab opens (single blank instance)
4. Load at least one image
5. In VariablesList, right-click the image and click **Open In Core Studio**
6. Verify: a new **CoreEntity** appears in VariablesList with draft status
7. Verify: a Core Studio tab opens for that core
8. Open the same core again from VariablesList — verify it focuses the existing tab (no duplicate for that core)
9. Create/open a different core — verify it opens in a separate tab

## Image Crop (manual)

1. Load an image via the file browser
2. Open it in the workspace (double-click in VariablesList)
3. Click the **Crop** button in the image toolbar
4. Adjust the crop rectangle, click **✓** to confirm
5. Verify: a new **ImageEntity** (not CoreEntity) appears in VariablesList with name `<original>_crop`
6. Open the cropped image — verify it shows the cropped region
