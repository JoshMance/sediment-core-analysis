# Sediment Core Analysis Toolkit

Desktop application for analyzing sediment core images with colour metrics, depth profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6** using clean **MVP architecture**.

## 🚧 Project Status

**Rebuilding from the ground up** following clean MVP architecture principles.

- ✅ **Architecture designed** — See [overview.md](docs/architecture/overview.md)
- ✅ **Domain layer** — Store, Entities, Container built
- ✅ **Application layer** — AppController + image loading service
- ✅ **UI layer** — FilePanel, WorkspacePanel, FilePresenter, WorkspacePresenter
- ✅ **Legacy UI preserved** — Available in `src_legacy/` for reference
- ✅ **Composition root** -- `main.py` wires all three layers
- ✅ **Dev mode** -- `--dev` flag opens a signal log window

---

## Architecture Overview

Following **Model-View-Presenter (MVP)** pattern optimized for PySide6:

See [Architecture Overview](docs/architecture/overview.md) for the full guide.

### Core Components

| Component         | Purpose                | Implementation                   |
| ----------------- | ---------------------- | -------------------------------- |
| **Entities**      | Domain models          | Plain Python dataclasses (no Qt) |
| **Store**         | Single source of truth | QObject with signals             |
| **AppController** | Orchestrates use-cases | Calls services, writes to Store  |
| **Presenters**    | Wire Store ↔ Views     | One per panel, Qt signals/slots  |
| **Views**         | Display only           | Dumb PySide6 widgets             |

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
│   │   └── services/          # Pure I/O helpers (load_image, etc.)
│   └── ui/                    # UI layer (outermost)
│       ├── presenters/        # Store ↔ View wiring
│       └── views/             # PySide6 widgets
│           ├── panels/        # Dock panels
│           ├── shell/         # Ribbon, main window
│           └── widgets/       # Reusable widgets
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

# Example: FilePanel tests
uv run python -m tests.file_panel_test
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

1. Wire `main.py` composition root to new `src/` layers
2. Add undo/redo via QUndoStack in AppController
3. Port remaining View components with Presenter wrappers
4. Migrate scientific functions to new structure

**Before contributing:** Please read [overview.md](docs/architecture/overview.md) to understand the MVP architecture approach.

---

## License

MIT License
