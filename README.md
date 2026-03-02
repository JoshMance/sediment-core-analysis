# Sediment Core Analysis Toolkit

Desktop application for analyzing sediment core images with colour metrics, depth profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6** using clean **MVP architecture**.

## 🚧 Project Status

**Currently rebuilding from the ground up** following clean MVP architecture principles.

- ✅ **Architecture designed** - See [PRINCIPLES.md](docs/architecture/PRINCIPLES.md)
- ✅ **Legacy UI preserved** - Available in `src_legacy/` for reference
- 🔄 **Active rebuild** - Implementing new `src/` with MVP pattern
- 🔄 **Core components** - Store, Controller, Presenters, Views being built

---

## Architecture Overview

Following **Model-View-Presenter (MVP)** pattern optimized for PySide6:

![MVP Architecture](docs/architecture/PRINCIPLES.md)

### Core Components

| Component      | Purpose                | Implementation                   |
| -------------- | ---------------------- | -------------------------------- |
| **Entities**   | Domain models          | Plain Python dataclasses (no Qt) |
| **Store**      | Single source of truth | QObject with signals             |
| **Controller** | Command processing     | QUndoStack + business logic      |
| **Presenters** | Wire Store ↔ Views     | One per panel, Qt signals/slots  |
| **Views**      | Display only           | Dumb PySide6 widgets             |

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

# Run main application (work in progress)
uv run main.py
```

### View Legacy Demos

Current working UI demos from previous implementation:

```bash
uv run src_legacy/views/panels/stratigraphy_panel/demo.py
uv run src_legacy/views/panels/image_panel/demo.py
uv run src_legacy/views/panels/file_panel/demo.py
uv run src_legacy/views/panels/workspace_panel/demo.py
uv run src_legacy/views/chrome/ribbon/demo.py
```

---

## Project Structure

```
sediment-core-analysis/
├── main.py                    # Application entry point
├── pyproject.toml             # Dependencies & config
│
├── src/                       # 🆕 NEW: Clean MVP architecture
│   ├── entities/              # Plain Python domain models
│   ├── store/                 # QObject state + signals
│   ├── controller/            # Commands + QUndoStack
│   ├── presenters/            # Store ↔ View wiring
│   ├── views/                 # PySide6 widgets
│   │   ├── panels/            # Dock panels
│   │   └── chrome/            # Ribbon, main window
│   ├── science/               # Scientific computation
│   │   ├── functions/         # Pure calculation functions
│   │   └── data/              # Reference datasets
│   └── tests/                 # Testing directories
       └── helpers/           # Shared DRY components
│
├── src_legacy/                # 🗂️ LEGACY: Previous implementation
│   ├── views/                 # Working UI components
│   ├── models/                # Domain models (being refactored)
│   └── science/               # Scientific functions (being migrated)
│
└── docs/
    └── architecture/
        └── PRINCIPLES.md      # 📋 MVP architecture guide
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
uv run python -m src.tests.{component}_test

# Example: FilePanel tests
uv run python -m src.tests.file_panel_test
uv run python -m src.tests.file_presenter_and_panel_test
```

### Architecture Rules

**Key Principles:**

1. **Presenters never talk directly** — communicate via Store signals
2. **Only Controller writes to Store** — Presenters read-only
3. **All Store mutations via QUndoCommand** — automatic undo/redo
4. **Views are dumb** — emit signals, display what Presenters provide
5. **No Qt in Entities** — plain Python dataclasses only

See [Architecture Principles](docs/architecture/PRINCIPLES.md) for complete guide.

---

## Tech Stack

| Layer               | Technology                    |
| ------------------- | ----------------------------- |
| **GUI**             | PySide6 (Qt6) + MVP pattern   |
| **State**           | Qt Signals/Slots + QUndoStack |
| **Data**            | Plain Python dataclasses      |
| **Science**         | NumPy, SciPy                  |
| **Visualization**   | Matplotlib                    |
| **Package Manager** | uv                            |
| **Testing**         | pytest + visual demos         |

---

## Contributing

This project is currently in active architectural rebuild.

**Current priorities:**

1. Implement Store with Qt signals
2. Create basic Entities (Core, Layer, etc.)
3. Build Controller with undo/redo
4. Port existing View components with Presenter wrappers
5. Migrate scientific functions to new structure

**Before contributing:** Please read [PRINCIPLES.md](docs/architecture/PRINCIPLES.md) to understand the MVP architecture approach.

---

## License

MIT License
