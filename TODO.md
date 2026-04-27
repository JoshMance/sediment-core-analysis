# TODO

- [x] Ribbon auto-switching (RibbonContext) + column separator lines

- [ ] Check Munsell data is correct
- [ ] Add documentation about the science section
- [ ] Decide: delete `tests/helpers/signal_logger.py` (redundant now that dev_log exists)
- [ ] Controller commands � the controller should interact with the store through commands that compose atomic CRUD operations and encapsulate business logic
- [ ] OS file association � register `.sedivis` with the OS as part of the app installer; associate with the executable and assign `sedivis_file_icon.svg` (converted to `.ico`) so `.sedivis` files show the correct icon in Windows Explorer and Open/Save dialogs

## Stage 2 Goals

Getting back to Nov 2025 functionality: length calibration, core segmentation, colour data (RGB, LAB, etc.) export, and charts.

Google MUI?

## Core Studio Reset Plan (Post-Revert)

### 1) Source Of Truth: Image -> RGB -> CIELAB

- [ ] Define canonical ingest contract for image data (final dtype, shape, channel order, alpha/grayscale handling)
- [ ] Decide and document the single source of truth for transforms (what layer owns RGB->Lab, and where that API lives)
- [ ] Define exact numeric ranges and normalization rules:
- [ ] RGB domain
- [ ] L\* domain
- [ ] a\* domain
- [ ] b\* domain
- [ ] Decide fixed-domain vs autoscaled rendering policy per channel and document why
- [ ] Create a small transform spec doc with explicit examples and expected outputs

### 2) Hierarchy + Provenance Model

- [ ] Define entity lineage model (source image -> crop(s) -> draft core -> finalized core)
- [ ] Define required provenance fields (source window/ROI, transform chain, revisions)
- [ ] Decide linear transform chain now vs hierarchical chain later (and migration-safe field naming)
- [ ] Specify how lineage behaves for full-image cores vs cropped-image cores
- [ ] Define recomputation policy when source or transform settings change

### 3) Core Studio Visualization Workstream

- [ ] Confirm orientation rules (vertical depth as canonical; when/how rotation is applied)
- [ ] Define channel visual grammar:
- [ ] Shared domains where direct comparison is required
- [ ] Distinct channel colors and accessibility constraints
- [ ] Axis direction/labels/ticks and min/max display policy
- [ ] Define what each column represents (Image, R, G, B, L*, a*, b\*, Layers, Depth)
- [ ] Add a simple visual acceptance checklist (what must be true for each column)

### 4) Application Architecture Workstream

- [ ] Reconfirm boundaries before coding:
- [ ] View responsibilities
- [ ] Presenter responsibilities
- [ ] Controller responsibilities
- [ ] Science module responsibilities
- [ ] Define whether presenters call science directly or always through controller for read-only transforms
- [ ] Define explicit no-regression rules for current workflows (open blank studio, open draft from image, no duplicate tabs)

### 5) Testing + Validation Workstream

- [ ] Build deterministic unit tests for RGB->Lab transform and channel extraction
- [ ] Add tests for full-image and crop-derived cores producing consistent pipeline behavior
- [ ] Add tests for serialization/backward compatibility if metadata fields are introduced
- [ ] Add manual QA checklist for Core Studio visuals (orientation, color, domain consistency)

### 6) Known Risks / Issues To Watch

- [ ] Hidden mismatch between normalized data and plotted domains (easy to make charts look wrong)
- [ ] Ambiguous ownership between presenter/controller/science causing duplicate logic
- [ ] Orientation inconsistencies between image and channel profiles
- [ ] Per-core metadata drift during save/load if fields are added without full archive coverage
- [ ] Visual similarity of channels misread as bug when data is genuinely correlated
- [ ] Performance regressions from repeated Lab conversion on large images (consider caching strategy later)

### 7) Planning Windows (Broad)

- [ ] Window A: Architecture + spec lock (ownership, domains, lineage)
- [ ] Window B: Science implementation (transforms + tests)
- [ ] Window C: Core Studio rendering implementation (columns, orientation, domains)
- [ ] Window D: Integration + regression pass (workflows, persistence, docs)
- [ ] Window E: Polish + deferred decisions (caching, advanced hierarchy, calibration integration later)
