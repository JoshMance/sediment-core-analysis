# Architecture Principles

This document explains the architecture of the sediment core analysis application. It begins with broad principles and progressively explores specific details.

---

## 1. What is MVC?

**Model-View-Controller (MVC)** is an architectural pattern that separates an application into three concerns:

| Component      | Responsibility                                                                  |
| -------------- | ------------------------------------------------------------------------------- |
| **Model**      | Data and business logic. Knows nothing about how it will be displayed.          |
| **View**       | Presentation. Renders data for the user and captures user input.                |
| **Controller** | Orchestration. Responds to user actions, updates the model, refreshes the view. |

The key benefit is **separation of concerns**: each layer can be developed, tested, and reasoned about independently. Views don't contain business logic; models don't know about buttons and windows.

### Our Adaptation

We follow MVC with one important addition: a **science layer** that contains pure computation (no dependencies on the rest of the app). Our layers are:

```
science/     → pure compute functions (no app dependencies)
models/      → datatypes, entities, services (domain logic)
controllers/ → orchestration (responds to events, coordinates model + view)
views/       → rendering + UI event dispatch (no domain logic)
```

---

## 2. Folder Structure

```
src/
├── science/           # Pure compute library
│   ├── api.py         # Single import point (ONLY module imported by app)
│   ├── catalog/       # Loads reference data into cached arrays
│   ├── data/          # Packaged reference datasets
│   ├── functions/     # Low-level compute (one function per file)
│   └── pipelines/     # Higher-level workflows
│
├── models/
│   ├── datatypes/     # Small, serializable value types
│   ├── entities/      # Domain objects with identity and behaviour
│   └── services/      # Operations that orchestrate entities + science
│
├── controllers/       # Event handling, coordination
│
└── views/             # UI components (display + event dispatch)
    └── panels/        # Specific panel widgets
```

---

## 3. Dependency Rules

Dependencies flow **downward**. Upper layers may import lower layers, but never the reverse.

```
┌─────────────────────────────────────────────────────────┐
│                        views/                           │
│   May import: entities, datatypes                       │
│   Must NOT import: science, services directly           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     controllers/                        │
│   May import: views, services, entities, datatypes      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  models/services/                       │
│   May import: entities, datatypes, science/api          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  models/entities/                       │
│   May import: datatypes, services (for behaviour)       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  models/datatypes/                      │
│   May import: nothing (or other datatypes)              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                       science/                          │
│   May import: NOTHING from models, views, controllers   │
│   Uses only: numpy, scipy, standard library             │
└─────────────────────────────────────────────────────────┘
```

**Key rule**: `science/` is completely isolated. It knows nothing about the application.

---

## 4. The Science Layer

The science layer is a **pure compute library**.  
It performs numerical transformations on arrays and returns arrays or simple data structures.

It does not know about the application, UI, entities, or files.  
The application owns data and state; science owns computation.

### Structure

```
science/
  api.py          # the ONLY module imported by the application
  data/           # packaged reference datasets (constants, lookup tables)
  catalog/        # loads data/ into reusable pandas DataFrames
  functions/      # small, reusable transformations (one function per file)
  pipelines/      # higher-level workflows composed of functions
```

### Core Rules

- No imports from `models/`, `views/`, or `controllers/`
- No filesystem, network, or UI operations
- No reading user/project data directly
- Functions must be deterministic given the same inputs
- The application imports **only** `science/api.py`
- Functions operate on arrays or DataFrames only

### Functions

Functions are **pure mathematical transformations** — single operations, no array orchestration.

Guidelines:

- One function per file
- **Pure math**: single transformation (e.g., gamma correction, matrix multiplication)
- Input: arrays with all parameters explicitly provided
- Output: transformed arrays
- No side effects
- No hidden state
- **No access to the catalog** — functions accept parameters; pipelines provide them
- No array orchestration (slicing, aggregation, iteration) — that's pipeline work

Examples:

```python
# science/functions/srgb_to_linear_rgb.py
def srgb_to_linear_rgb(srgb: np.ndarray) -> np.ndarray:
    """Apply inverse gamma correction to convert sRGB to linear RGB."""
    # Pure transformation: sRGB → Linear RGB
    ...
```

```python
# science/functions/xyz_to_lab.py
def xyz_to_lab(xyz: np.ndarray, white_point: np.ndarray) -> np.ndarray:
    """Convert CIE XYZ to CIELAB color space."""
    # Pure transformation: XYZ → LAB, with white point as parameter
    ...
```

### Pipelines

Pipelines **orchestrate functions** and handle array operations.

They may:

- Call multiple functions in sequence
- Handle array structure (slicing, aggregation, axis operations)
- Use catalog for default parameters (e.g., default illuminant)
- Accept parameters to override defaults

They must not:

- Contain mathematical transformations (delegate to functions)
- Read external files (catalog does this)
- Access application state
- Modify global data

Examples:

```python
# science/pipelines/rgb_to_lab.py
def rgb_to_lab(rgb: np.ndarray, illuminant: str = "D65") -> np.ndarray:
    """Convert RGB to CIELAB (pipeline orchestrating 3 transformations)."""
    linear = srgb_to_linear_rgb(rgb)           # Function 1
    xyz = linear_rgb_to_xyz(linear)            # Function 2
    white_point = catalog.white_point(illuminant)  # Catalog provides default
    lab = xyz_to_lab(xyz, white_point)         # Function 3
    return lab
```

```python
# science/pipelines/mean_rgb_per_row.py
def mean_rgb_per_row(image: np.ndarray) -> np.ndarray:
    """Compute mean RGB per row (pipeline handling array operations)."""
    # Array orchestration: mean across axis, normalization
    return image.mean(axis=1).astype(np.float64) / 255.0
```

**Key Distinction:**

- ❌ Don't put array operations (`.mean()`, slicing, `axis=1`) in functions
- ✅ Functions do pure math; pipelines orchestrate array structures

### Reference Data and Catalog

The `science/data/` directory contains packaged reference datasets, constants, and lookup tables used by computations.

These are accessed through the **DataCatalog** (`science/catalog/`).

The catalog:

- Loads reference datasets into numpy arrays (with lazy loading and caching)
- Provides read-only access through generic, data-driven methods
- Is used only by pipelines (never by functions — functions should accept parameters)
- Avoids hardcoding specific accessor methods; uses lookup tables and generic queries

**Design philosophy:** Data-driven and extensible. Adding new reference data should not require code changes. For example:

- ❌ Bad: `catalog.d65_white_point()`, `catalog.d50_white_point()` (hardcoded, doesn't scale)
- ✅ Good: `catalog.white_point('D65')`, `catalog.white_point('D50')` (generic, extensible)

This avoids duplicating data loading logic across pipelines and makes the catalog flexible.

### API Module

`science/api.py` is the only public interface to the science layer.

It:

- Exposes approved functions and pipelines
- Manages a shared catalog instance
- Shields the application from internal structure

The rest of the application should never import from `science/functions/`, `science/pipelines/`, or `science/catalog/` directly.

```python
from science.api import derive_colour_profile
```

### Design Principle

**Science code never fetches data — it only computes on what it's given.**

The application:

- Loads images and entities
- Manages state
- Decides when computations run

The science layer:

- Transforms data into new data

---

## 5. The Models Layer

The models layer contains the **domain model**: the data structures and logic that represent the problem domain.

### 5.1 Datatypes

Datatypes are **small, serializable value types**. They have no identity — two datatypes with the same values are equal.

| Type               | Purpose                                                           |
| ------------------ | ----------------------------------------------------------------- |
| `Image`            | Pixel buffer reference + metadata                                 |
| `ImageCalibration` | Pixel ↔ physical units scale (mm_per_px, calibrated flag)         |
| `Layer`            | A segment with start/end pixels and attribute values              |
| `Data`             | Measurements along a **single axis**, each point scalar or vector |
| `Munsell`          | A Munsell colour specification (hue, value, chroma)               |

**Note on calibration vs. position:**  
`ImageCalibration` provides only the _scale_ (how many mm per pixel), not absolute position. The `Core` entity handles absolute positioning via its `top_depth_mm` field, which specifies where pixel 0 sits in absolute depth space.

**Note on Data:**  
`Data` represents measurements along **one axis** (e.g., depth down a core). Each point along that axis can be:

- **Scalar**: a single number, shape (H,)
- **Vector**: multiple components, shape (H, N)  
  Example: RGB data is (H, 3) - H depth points, each point is [R, G, B]

This is NOT multi-dimensional with separate independent axes. It's ONE axis with scalar or vector measurements at each point.

### 5.2 Entities

Entities are **domain objects with identity and lifecycle**. They aggregate datatypes and may have behaviour.

| Entity         | Purpose                                                           |
| -------------- | ----------------------------------------------------------------- |
| `Core`         | A sediment core image with calibration and intrinsic derived data |
| `DerivedData`  | RGB/Lab profiles computed from the core image                     |
| `CoreAnalysis` | User interpretation: layers, boundaries, classifications          |

**Important distinction:**

- `Core` holds **intrinsic data** — deterministic measurements from the image
- `CoreAnalysis` holds **interpretation** — user-defined segmentation and labels

### 5.3 Services

Services **orchestrate operations** that involve computation or affect multiple objects. They delegate heavy math to `science/api`.

| Service               | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `CoreCreationService` | Creates a Core with all derived data computed                 |
| `ColourSpaceService`  | Wraps colour space conversions                                |
| `CoreAnalysisService` | Layer operations: add/remove/move boundaries, recompute stats |

Services are the **only place** where `science/api` is called.

---

## 6. The Views Layer

Views **render data and capture user input**. They do not contain domain logic.

### Rules

1. **Render what you are given** — views receive entities/datatypes and display them
2. **Manage only UI state** — zoom level, selected tool, hover state
3. **Emit events via callbacks** — don't call services directly
4. **Never compute domain data** — no colour transforms, no statistics, no data wrangling

### Callback Pattern

Instead of views calling services directly, they expose callbacks that a controller wires up:

```python
# View exposes callbacks
class StratigraphyPanel:
    on_boundary_add: Callable[[float], None] | None = None
    on_boundary_delete: Callable[[int], None] | None = None

    def _handle_click(self, depth_mm: float):
        if self.on_boundary_add:
            self.on_boundary_add(depth_mm)

# Controller wires them
panel.on_boundary_add = lambda depth: (
    CoreAnalysisService.add_boundary(analysis, depth),
    panel.refresh()
)
```

### Demo Files as Quasi-Controllers

Each panel has a `demo.py` that acts as a controller for standalone testing:

- Creates test data using services
- Wires callbacks to service operations
- Calls `panel.refresh()` after changes

---

## 7. The Controllers Layer

Controllers respond to user actions, coordinate model updates, and refresh views.

In the current architecture, `demo.py` files serve as quasi-controllers. A full application would have a dedicated controller layer that:

- Manages application state
- Routes events from views to services
- Ensures views stay in sync with model state

---

## 8. Data Flow Example

Here's how data flows when a user adds a layer boundary:

```
1. User clicks canvas
         │
         ▼
2. View captures click coordinates
         │
         ▼
3. View invokes callback: on_boundary_add(depth_mm)
         │
         ▼
4. Controller receives callback
         │
         ▼
5. Controller calls CoreAnalysisService.add_boundary(analysis, depth_mm)
         │
         ▼
6. Service updates the CoreAnalysis entity
         │
         ▼
7. Controller calls panel.refresh()
         │
         ▼
8. View re-renders from updated entity
```

The view never touches the entity directly. It only:

- Reads the entity to render
- Emits events when the user acts

---

## 9. Data-Driven Views

Views **discover** what data exists from the model, rather than hardcoding expectations.

**Bad Practice (Hardcoded Expectations):**

```python
# View assumes specific fields exist
def setup_ui(self):
    self._config = {
        'rgb': True,
        'cielab': False,
        'munsell': True
    }
```

**Problem:** If the model adds `grain_size` data, the view won't show it without code changes.

**Good Practice (Data-Driven Discovery):**

```python
# View introspects model to discover available data
def _discover_available_columns(self, analysis: CoreAnalysis) -> dict[str, bool]:
    config = {}

    # Discover derived data from Core
    if analysis.core.derived.rgb is not None:
        config['rgb'] = True
    if analysis.core.derived.lab is not None:
        config['cielab'] = True

    # Discover layer attributes from schema
    for field_name in analysis.schema.fields.keys():
        config[field_name] = True

    return config
```

**Benefits:**

1. **Loose coupling** — model can add new data without view changes
2. **Automatic UI updates** — new data types appear automatically
3. **Model is source of truth** — view reflects what exists, not what it expects
4. **Extensibility** — easy to add new computed metrics (porosity, etc.)
5. **Less maintenance** — no hardcoded configs to keep in sync

**Implementation in Stratigraphy Panel:**

- `widget.py`: `_discover_available_columns()` introspects `CoreAnalysis` when `set_analysis()` is called
- Configuration is built dynamically: `{'rgb': True, 'cielab': True, 'munsell': True, ...}`
- Column settings modal shows only discovered columns
- If model adds new derived data, it appears automatically

**Exception: View-Only Elements**

Some UI elements don't represent model data (rulers, gridlines, spacing).  
These are **view concerns** and may be hardcoded as they're not model-driven.

---

## 10. Summary of Key Principles

1. **Separation of concerns** — each layer has a single responsibility
2. **Downward dependencies** — upper layers import lower layers, never the reverse
3. **Science is isolated** — pure compute with no app dependencies
4. **Views don't compute** — they render and emit events
5. **Services orchestrate** — they coordinate entities and call science
6. **Callbacks for events** — views emit callbacks, controllers handle them
7. **Intrinsic vs interpretation** — Core holds measurements, CoreAnalysis holds user interpretation
8. **Data-driven views** — views discover available data from the model, not hardcode expectations
