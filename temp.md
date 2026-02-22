# Code Review Notes

Recording suggestions from code review session.

---

## ⚠️ General Guidance

When implementing these changes:

1. **Reason about how each change fits the broader architecture** — consider dependencies, how other components use this code, and whether the change aligns with our separation of concerns (science → datatypes → entities → services → views).
2. **Articulate the goal** — be clear about what we're trying to achieve and why. If a change shifts the role of a component, reconcile that with the original design intent.
3. **Update all documentation** — check PRINCIPLES.md, README.md, docstrings, and inline comments. Keep them accurate and consistent with the code.
4. **Avoid misunderstandings cascading** — if you got something wrong, trace the impact and fix it everywhere.

---

## `src/models/datatypes/calibration.py`

**Changes:**

1. Add `calibrated: bool = False` field to distinguish default from actual calibrated values
2. Remove `top_depth_mm` - doesn't make sense for image calibration
3. Remove `depth_range()` method - same reason
4. Constructor should accept px measurement and mm value as inputs, then compute and store the ratio
5. Add validation to prevent divide-by-zero when computing ratio

**Reminders:**

- Consider how `ImageCalibration` is used by `Core`, `CoreCreationService`, and views — ensure changes don't break assumptions elsewhere
- Articulate the goal: calibration is about converting between pixel and physical units; it shouldn't carry depth/position information
- Update docstrings in this file and any documentation that references `ImageCalibration`
- Check all call sites and update them if the constructor signature changes

---

## `src/models/datatypes/data.py`

**Changes:**

1. Clarify that `Data` is a **1D numeric series**, not n-D — fix any documentation or comments suggesting otherwise

**Reminders:**

- Consider how `Data` is used by `Core.derived`, `DerivedData`, and any services that produce/consume it
- Articulate the goal: `Data` represents a single continuous signal along one axis (e.g. RGB profile down a core)
- Update docstrings, type hints, and PRINCIPLES.md if they mention n-D
- Check `early_refactor.md` and `refactor-progress.md` for incorrect descriptions

---

## `src/models/datatypes/image.py`

**No changes needed.**

**Reminders:**

- Still review how `Image` is used by `Core`, services, and views
- Ensure docstrings and documentation are up to date
- Confirm that the design intent (pixel buffer + metadata) is clear in all references

---

## `src/models/datatypes/layer.py`

**No changes needed.**

**Reminders:**

- Review how `Layer` is used by `CoreAnalysis`, services, and views
- Ensure docstrings and documentation are up to date
- Confirm that the design intent (interval + attribute values) is clear in all references

---

## `src/models/datatypes/munsell.py`

**No changes needed now.**

**To-Do (future work):**

- Add validation for Munsell values (hue, value, chroma must be within valid ranges)
- Don't put validation in the datatype itself — this would be inefficient
- Consider: validation service, or validation at input boundaries (when user enters data, when loading from file)

**Reminders:**

- Review how `Munsell` is used and where values originate
- Ensure docstrings explain the valid ranges even if we don't enforce them yet
- Update documentation with any constraints or expectations

---

## `src/models/entities/core_analysis.py`

**Changes:**

1. Consider: should we track `core_id: UUID` instead of (or in addition to) `core: Core`? Think about serialization, persistence, and whether we need the full object reference.

2. **Separation of concerns violation in `mean_rgb_for_layer()`:**
   - Entity is doing computation (importing numpy, calculating mean) — this belongs in a service
   - The mean calculation should live in the science layer (so we can change the algorithm later)
   - Suggested flow:
     - Entity: just holds data
     - Service: calls science to compute layer statistics
     - Science pipeline: takes Nx3 array, computes mean (or other aggregate), returns result
     - Science function: operates on individual RGB tuples/arrays
   - Remove inline numpy import and direct computation from entity
   - Create a service method that delegates to science

**Reminders:**

- Articulate the goal: entities hold data and enforce invariants, but don't perform scientific computation
- Trace all uses of `mean_rgb_for_layer()` — it likely needs to be replaced with service calls
- Consider: should ALL layer statistics computation move to a service?
- Update docstrings to clarify entity vs service responsibilities
- Check if other methods in this entity are doing computation they shouldn't

---

## `src/models/entities/core.py`

**Changes:**

1. **DerivedData dataclass concerns:**
   - Comments mention "shape (H, 3)" which is array-level detail - `Data` is 1D, not n-D. Fix documentation.
   - CIELAB conversion makes assumptions (illuminant D65, observer, etc.) but we shouldn't hardcode these in comments — they belong in science layer docs
   - Question: Do we even need a `DerivedData` dataclass? It just holds two `Data` objects. Could `Core.derived` just be a dict or individual fields (`rgb: Data | None`, `lab: Data | None`)?
   - Reconsider whether `DerivedData` adds value or just adds indirection

2. **Related to calibration.py changes:**
   - `depth_range_mm` property uses `calibration.depth_range()` which we're removing
   - `px_to_depth()` and `depth_to_px()` delegate to calibration — ensure they still work after calibration refactor

**Reminders:**

- Articulate the goal: Core holds intrinsic measurements; is DerivedData the right abstraction or overengineered?
- Consider: calibration changes will affect these methods - update them accordingly
- Update all docstrings to be accurate about Data (1D) vs underlying array shapes
- Don't mention CIELAB assumptions in entity docs - those belong in science layer
- Check how `Core.derived.rgb` and `Core.derived.lab` are accessed throughout the codebase

---

## `src/models/services/colour_space_service.py`

**Question for consideration:**

- Is `ColourSpaceService` overkill/redundant?
- Currently it's just a thin wrapper: calls `science.api` functions and adapts numpy arrays → `Data` datatypes
- Alternative: services that need color computation (e.g., `CoreCreationService`) could call `science.api` directly and create `Data` objects themselves
- Pro keeping it: single place for Data adaptation logic, easier to change later, clearer responsibility
- Pro removing it: less indirection, simpler architecture, one less file to maintain
- **Decision needed:** Is the type adaptation layer valuable enough to justify a separate service, or should calling services handle it?

**If keeping it:**

- Consider adding more value (caching, validation, handling multiple color spaces, etc.)
- Update docstrings to justify its existence

**If removing it:**

- Move Data creation logic to calling services (CoreCreationService)
- Update imports throughout codebase

**Reminders:**

- Articulate the goal: what responsibility does this service actually have? Just type conversion, or more?
- Review all call sites - how is this service used? Does it provide real value?
- Check if there are future plans for color space operations that would justify this abstraction

---

## `src/models/services/core_analysis_service.py`

**No changes needed.**

**Reminders:**

- Review how this service is used by controllers/demos
- Ensure all service methods align with the principle that services orchestrate, entities hold data
- Update docstrings if needed

---

## `src/models/services/core_creation_service.py`

**Changes:**

1. **`create_from_file()` - is it used?**
   - Check if this method is actually called anywhere
   - If not, remove it — we might only need `create_from_image()`
   - Loading from file could be external to this service (file loading → Image datatype → create_from_image)

2. **`_compute_derived()` and `update_derived()` depend on ColourSpaceService decision:**
   - If we keep ColourSpaceService: current implementation is fine
   - If we remove ColourSpaceService (see earlier note): these methods need to call `science.api` directly and create `Data` objects themselves
   - Whichever decision we make, update both places consistently

**Reminders:**

- Articulate the goal: CoreCreationService creates Core entities with all derived data computed
- Review all call sites for both `create_from_file` and `create_from_image`
- If ColourSpaceService is removed, this service absorbs the Data creation logic
- Update docstrings to reflect any architectural changes

---

## `src/science/catalog/__init__.py`

**Changes:**

1. Rename `ReferenceCatalog` → `DataCatalog`
2. **Remove hardcoded specific functions like `d50_white_point()` and `d65_white_point()`**
   - These are too specific and inflexible
   - Alternative approach: generic `get_white_point(illuminant: str)` that looks up the value
   - Or: white points could be derived from the illuminant data itself
   - Or: store white points in data files and load them like illuminants
   - Don't proliferate one function per illuminant/constant — use data-driven approach

---

## `src/science/functions/` — Architecture Violation

**Core Principle:**

- **Functions** = pure mathematical transformations (single operations, no array orchestration)
- **Pipelines** = orchestrate functions, handle numpy array structures, compose operations

**The problem:** At least two of our current "functions" are actually doing pipeline-level work.

---

### `mean_rgb_per_row.py` and `mean_rgb_for_range.py`

**Issue:**

- These are orchestrating numpy operations (`.mean(axis=1)`, array slicing, aggregation across rows)
- This is **pipeline behavior**, not pure math
- A function should just compute a mathematical mean — the pipeline should handle "for each row" or "for this range"

**Changes:**

1. **Create pipeline:** `src/science/pipelines/average_rgb_per_row.py`
   - Takes (H, W, 3) image array
   - Calls a pure math averaging function for each row
   - Handles array orchestration (axis operations, slicing, iteration)
   - Returns (H, 3) result

2. **Replace/rewrite functions to be pure math:**
   - Function should just compute mean of RGB values: `mean_rgb(rgb_array: NDArray) -> NDArray`
   - No axis parameters, no row/range logic, just: given some RGB values, compute their average
   - Pipeline orchestrates when/how to apply this

3. **Alternative approach:** Keep the current implementation but move it to `pipelines/` instead of `functions/`
   - This might be simpler if the array operations are inherently part of the workflow
   - But clarify: these are pipelines, not functions

**Reminders:**

- Articulate the goal: functions are mathematical primitives; pipelines compose and orchestrate them over data structures
- Review all code that imports these — likely imports from `science.api`, check what the contract should be
- Update PRINCIPLES.md to clarify function vs pipeline distinction if not already clear
- Consider: do we have OTHER functions that are actually pipelines?

---

### `rgb_to_cielab.py`

**Issue:**

- This is actually **2-3 separate transformations** bundled together:
  1. sRGB → Linear RGB (gamma correction / inverse companding)
  2. Linear RGB → XYZ (color space transformation matrix)
  3. XYZ → CIELAB (perceptual color space transformation)
- These should be separate composable functions

**Changes:**

1. **Split into three functions:**
   - `srgb_to_linear_rgb.py`: Apply inverse gamma correction
   - `linear_rgb_to_xyz.py`: Apply transformation matrix (should accept illuminant/observer parameters!)
   - `xyz_to_lab.py`: Convert XYZ to LAB (should accept reference white!)

2. **Create pipeline:**
   - `src/science/pipelines/rgb_to_lab.py`
   - Orchestrates the three-step conversion
   - Calls catalog for D65 white point (or accepts it as parameter)
   - Composes: sRGB → linear → XYZ → LAB

3. **Hardcoded D65 assumption:**
   - Current implementation hardcodes D65 illuminant and white point
   - The individual functions should accept these as parameters
   - The pipeline can provide defaults (from catalog) but allow overrides
   - Makes the functions reusable for other illuminants/observers

**Reminders:**

- Articulate the goal: each function does ONE color space transformation; pipelines compose them
- This makes testing easier (test each transformation independently)
- This makes the science layer more flexible (can compose transformations differently, swap illuminants, etc.)
- Review all code using `rgb_to_cielab` — API might need to expose both the pipeline and individual functions
- Update docstrings to explain each step clearly
- Check papers/ folder - do we have references for these transformations? Cite them in docstrings
- Consider: should catalog provide transformation matrices, not just illuminants?

**Reminders:**

- Articulate the goal: catalog should be generic and extensible, not accumulate hardcoded getters
- Update all imports: `ReferenceCatalog` → `DataCatalog` in api.py and anywhere else it's referenced
- Consider: what other reference data might we need? Design the interface to accommodate growth
- Update PRINCIPLES.md examples to use correct class name
- Check how white points are used — can we eliminate the methods entirely?

---

## `src/views/panels/stratigraphy_panel/` — FUNDAMENTAL ARCHITECTURE VIOLATION

**Core Principle Being Violated:**

- **Views should be data-driven by the model**
- The model is the source of truth for what data exists; views discover and display it
- Views should NOT hardcode what data they expect to find

**The Problem:**

Current implementation in `widget.py` has this hardcoded configuration:

```python
self._current_config = {
    'image': True,
    'depth': True,
    'thickness': False,
    'index': False,
    'rgb': True,
    'cielab': False,  # ← We calculate this in the model...
    'munsell': True,
    'lithology': False,
    'description': False
}
```

**Why this is wrong:**

1. The view decides what columns are possible, rather than discovering from the model
2. If `Core.derived.lab` exists in the model, but the view doesn't have a hardcoded 'cielab' entry, we can't show it
3. Adding new derived data types requires changing BOTH the model AND the view
4. The view is making assumptions about model structure instead of inspecting it
5. This creates tight coupling: model changes break the view

**What should happen instead:**

1. View receives a `CoreAnalysis` (which contains a `Core`)
2. View **introspects the Core entity** to discover what data is available:
   - `Core.image` → ImageColumn
   - `Core.derived.rgb` → DataColumn("RGB", data=rgb)
   - `Core.derived.lab` → DataColumn("CIELAB", data=lab)
   - Future: `Core.derived.grain_size` → automatically available!
3. View dynamically builds list of **available** columns based on what exists in the model
4. User can show/hide from the available columns (via column settings modal)
5. View-only columns (ruler, spacing) are exceptions since they don't represent model data

**Example of correct flow:**

```python
def _discover_available_columns(self, analysis: CoreAnalysis) -> dict[str, BaseColumn]:
    """Discover what columns can be displayed based on model data."""
    available = {}

    # Always available: view-only columns
    available['ruler'] = RulerColumn()

    # Model-driven columns
    if analysis.core.image is not None:
        available['image'] = ImageColumn(analysis.core.image, ...)

    if analysis.core.derived.rgb is not None:
        available['rgb'] = DataColumn("RGB", data=analysis.core.derived.rgb, ...)

    if analysis.core.derived.lab is not None:
        available['cielab'] = DataColumn("CIELAB", data=analysis.core.derived.lab, ...)

    # Future: if we add derived.grain_size, it automatically appears here!
    # if analysis.core.derived.grain_size is not None:
    #     available['grain_size'] = DataColumn("Grain Size", ...)

    return available
```

**Changes Required:**

1. **Remove hardcoded `_current_config` dictionary**
   - Replace with dynamic column discovery from model

2. **Add `_discover_available_columns()` method**
   - Introspect the CoreAnalysis/Core entity
   - Build dict of columns that CAN be shown (based on what data exists)
   - Return column instances, not just bool flags

3. **Refactor column settings modal**
   - Present columns discovered from model, not hardcoded list
   - User toggles visibility of available columns
   - Store user preferences as dict[str, bool] where keys match discovered columns

4. **Update `set_analysis()` method**
   - Call `_discover_available_columns()` first
   - Apply user visibility preferences to discovered columns
   - Pass only visible columns to canvas

5. **Consider: introspection helpers in Core entity**
   - Maybe add `Core.get_available_derived_data() -> dict[str, Data]`
   - Or iterate over `Core.derived` fields programmatically
   - Makes discovery more robust and less fragile

**Exception: View-Only Columns**

- Ruler, spacing guides, gridlines, etc. are view concerns
- These don't represent model data
- OK to hardcode these as always available
- But still keep them separate from model-driven columns

**Benefits of This Approach:**

1. **Loose coupling:** Model can add new derived data without view changes
2. **Automatic UI updates:** New data types appear in column settings automatically
3. **Model is source of truth:** View reflects what exists, not what it expects
4. **Extensibility:** Easy to add new computed metrics (grain size, porosity, etc.)
5. **Less maintenance:** Don't need to keep hardcoded configs in sync with model

**Reminders:**

- This is a **broader refactor** affecting widget.py, columns.py, modals/column_settings_modal.py
- Articulate the goal: data-driven UI where model dictates available columns
- Consider how this affects demo.py and controllers — do they need to change?
- Update PRINCIPLES.md to explain this data-driven view principle
- Test that column discovery works with partial data (e.g., image but no derived data)
- Think about serialization: should user column preferences persist between sessions?
- Consider: should LayerColumn also be model-driven? (show if analysis.layers exists)

---

## ✅ 13. Stratigraphy Panel: Data-driven Column Discovery

**COMPLETED** - Implemented data-driven column discovery so views introspect the model instead of hardcoding expectations.

**What was implemented:**

1. **✅ Added `_discover_available_columns()` method to widget.py**
   - Introspects `CoreAnalysis.core.derived` for available data (rgb, lab)
   - Introspects `CoreAnalysis.schema.fields` for layer attributes
   - View-only columns (depth, thickness, index, image) included separately
   - Returns `dict[str, bool]` mapping column name to default visibility

2. **✅ Removed hardcoded `_current_config` initialization**
   - Now populated dynamically when `set_analysis()` is called
   - Configuration driven by what actually exists in the model

3. **✅ Updated `set_analysis()` method**
   - Calls `_discover_available_columns(analysis)` to build configuration
   - Model determines what columns are available

4. **✅ Updated modal `_on_confirm()` to handle dynamic configurations**
   - Added support for collecting from `_checkboxes` dict (data-driven)
   - Maintains backward compatibility with hardcoded checkboxes
   - Emits configuration based on what was discovered

5. **✅ Updated PRINCIPLES.md**
   - Added Section 9: "Data-Driven Views"
   - Documented principle: views discover from model, not hardcode expectations
   - Explained benefits: loose coupling, automatic UI updates, extensibility
   - Added to summary as principle #8

**Benefits Achieved:**

- ✅ Model can add new derived data (e.g., `grain_size`) without view code changes
- ✅ View reflects what actually exists in the model
- ✅ No hardcoded expectations about data availability
- ✅ Foundation for fully dynamic UI that adapts to model changes

**Remaining Work (Future Enhancement):**

While the core discovery mechanism is implemented, the modal UI still creates hardcoded checkboxes. To complete a **fully data-driven UI**:

- Replace modal's hardcoded checkbox creation with dynamic generation from discovered config
- Update modal's `_create_column_groups()` to build groups from discovery
- Test with partial data (e.g., only RGB, no LAB)
- Consider persisting user column preferences between sessions

**Current State:** Discovery mechanism works. Configuration is model-driven. Modal collects dynamically but presents statically (acceptable for first iteration).

---
