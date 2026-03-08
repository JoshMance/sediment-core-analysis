# Sediment Core Analysis Toolkit

Desktop application for analyzing sediment core images with colour metrics, depth profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6** using clean **MVP architecture**.

## 🚧 Project Status

**Rebuilding from the ground up** following clean MVP architecture principles.

- ✅ **Architecture designed** — See [overview.md](docs/architecture/overview.md)
- ✅ **Domain layer** — Store, Entities, Container built
- ✅ **Application layer** — AppController, WorkspaceState, WorkspaceService, image loading
- ✅ **UI layer** — FileBrowser, VariablesList, FilePresenter, VariablesPresenter
- ✅ **Workspace system** — tabbed panel host with extensible factory; ImagePanel for image viewing and core selection
- ✅ **Ribbon** — Home tab with File, Image (Load Image / Load Data / Load Map), and Edit groups; SVG icon support
- ✅ **Status bar** — `StatusBar` view + `StatusBarPresenter`; reflects Store signals, reverts to "Ready" after 5 s
- ✅ **Legacy UI preserved** — Available in `src_legacy/` for reference
- ✅ **Composition root** — `main.py` wires all three layers
- ✅ **Dev mode** — `--dev` flag opens a signal log window

---

## Architecture Overview

Following **Model-View-Presenter (MVP)** pattern optimized for PySide6. Dependencies flow inward: **UI → Application → Domain**.

See [Architecture Overview](docs/architecture/overview.md) for the full guide.

### Layers

| Layer                              | What lives here                                                                                                                                                                                                                                                                                    |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Domain** `src/domain/`           | **Entities** — plain Python dataclasses (`ImageEntity`, `CoreEntity`). **Store** — `QObject` Component; single source of truth, emits signals on every mutation.                                                                                                                                   |
| **Application** `src/application/` | **AppController** — long-lived Component; coordinates use-cases, the only writer to the Store. **WorkspaceState** — long-lived Component; tracks which panels are open (app-layer state, no widgets). **Services** — stateless helpers internal to this layer (`load_image`, `workspace_service`). |
| **UI** `src/ui/`                   | **Presenters** — one Component per panel/sidebar; wire Store signals and View events to AppController calls. **Views** — dumb PySide6 widgets split into `shell/` (created at startup, always present) and `panels/` (created at runtime on demand).                                               |

---

## Quick Start

```bash
# Install uv (Python package manager)
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/your-username/sediment-core-analysis.git
cd sediment-core-analysis
uv sync

# Run the application
uv run python main.py

# Force dark or light theme
uv run python main.py --dark
uv run python main.py --light

# Run with signal log window
uv run python main.py --dev
```

### View Legacy Demos

Current working UI demos from previous implementation:

```bash
uv run src_legacy/views/panels/stratigraphy_panel/demo.py
uv run src_legacy/views/panels/image_panel/demo.py
uv run src_legacy/views/panels/file_panel/demo.py
uv run src_legacy/views/panels/workspace_panel/demo.py
uv run src_legacy/views/shell/ribbon/demo.py
```

---

## Project Structure

```
sediment-core-analysis/
├── main.py                    # Application entry point
├── pyproject.toml             # Dependencies & config
│
├── src/                       # Clean MVP architecture
│   ├── domain/                # Domain layer (innermost)
│   │   ├── entities/          # Plain Python domain models
│   │   ├── store/             # QObject state + signals
│   │   └── services/          # Domain services (future)
│   ├── application/           # Application layer
│   │   ├── app_controller.py  # Orchestrates use-cases; sole writer to the Store
│   │   ├── workspace_state.py # Tracks open panels (app-layer QObject, no widgets)
│   │   └── services/          # I/O + orchestration helpers (load_image, workspace_service)
│   └── ui/                    # UI layer (outermost)
│       ├── presenters/        # Store ↔ View wiring
│       │   ├── workspace_presenter.py   # Panel lifecycle + factory registry
│       │   └── image_panel_presenter.py # ImageEntity → ImagePanel bridge
│       ├── resources/         # Static assets
│       │   └── theme/         # QSS files + colour tokens + apply_theme()
│       └── views/             # PySide6 widgets
│           ├── panels/        # Runtime panels (created on demand)
│           │   └── image_panel/  # Pan/zoom/rotate canvas + toolbar + selection
            └── shell/         # Persistent shell views
                ├── ribbon/    # Ribbon view + RibbonButton + RibbonGroup
                └── workspace.py  # Tabbed panel host (always-present)
│
├── tests/                     # Testing (outside src)
│   └── helpers/               # Shared DRY components
│
├── src_legacy/                # Legacy implementation (reference)
│   ├── views/                 # Working UI components
│   ├── datatypes/             # Domain data types
│   ├── entities/              # Domain entities
│   ├── services/              # Business logic services
│   └── science/               # Scientific functions
│
└── docs/
    └── architecture/
        └── overview.md        # 📋 MVP architecture guide
```

---

## Development

### Setup

```bash
uv sync --all-extras
```

### Code Quality

```bash
uv run black src/
uv run ruff check src/ --fix
```

### Testing

```bash
uv run pytest
# Manual tests (visual component verification)
uv run python -m tests.{component}_test

# Example: FileBrowser tests
uv run python -m tests.file_browser_test
uv run python -m tests.file_presenter_and_panel_test
```

### Architecture Rules

**Key Principles:**

1. **Only AppController writes to Store** — Presenters are read-only
2. **Views are dumb** — emit signals, display what Presenters provide
3. **No Qt in Entities** — plain Python dataclasses only
4. **Dependencies flow inward** — UI → Application → Domain

See [Architecture Overview](docs/architecture/overview.md) for complete guide.

---

## Tech Stack

| Layer               | Technology                  |
| ------------------- | --------------------------- |
| **GUI**             | PySide6 (Qt6) + MVP pattern |
| **State**           | Qt Signals/Slots            |
| **Data**            | Plain Python dataclasses    |
| **Science**         | NumPy, SciPy                |
| **Visualization**   | Matplotlib                  |
| **Package Manager** | uv                          |
| **Testing**         | pytest + visual demos       |

---

## Contributing

This project is currently in active architectural rebuild.

**Current priorities:**

1. Add undo/redo via QUndoStack in AppController
2. Add CorePanel (view and crop controls for CoreEntity)
3. Session save/load (`.sedivis` file — entity store + workspace state)
4. Migrate scientific functions to new structure

**Before contributing:** Please read [overview.md](docs/architecture/overview.md) to understand the MVP architecture approach.

---

## License

MIT License
