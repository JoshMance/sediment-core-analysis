# Implementation Checklist

Use this checklist when adding features that change structure, panel wiring, or scientific behaviour.

## 1) Add A New Panel

- [ ] Define panel purpose and owning entity type.
- [ ] Add entry to `ENTITY_TYPE_TO_PANEL_TYPE` in `src/application/services/panel_registry.py`.
- [ ] Add entry to `PANEL_TYPE_CONFIG` with factory function, ID prefix, and ribbon tab.
- [ ] Define factory function `_make_*_panel()` in `src/application/services/panel_registry.py`.
- [ ] Create/update presenter and view wiring.
- [ ] Confirm open/focus/close behaviour in workspace tabs.
- [ ] Update `docs/architecture/topology/topology.yaml`.
- [ ] Add/update tests and manual QA notes.

## 2) Add Or Change Science Behaviour

- [ ] Keep scientific transformations in `/science` only.
- [ ] Do not duplicate RGB/CIELAB/Munsell logic in UI/Application/Domain.
- [ ] Views may read pixels and compute display geometry from provided parameters.
- [ ] Views must not decide science parameters (conversion constants, transform policy).
- [ ] Define/confirm API contract in science module before integration.
- [ ] Document assumptions (domains, precision, clipping, references) in code docstrings.
- [ ] Add deterministic tests for transform outputs and edge cases.

## 3) Core Studio Specific

- [ ] Ensure depth ruler receives scale parameter/provider from outside the view.
- [ ] Keep depth rendering logic view-local, parameter ownership outside the view.
- [ ] Keep channel column scientific derivation in `/science`.
- [ ] Keep current calibration pipeline limitations explicit until fixed.

## 4) Documentation Sync

- [ ] `docs/architecture/overview.md` matches current code behaviour.
- [ ] `docs/architecture/topology/topology.yaml` follows code exactly.
- [ ] `docs/architecture/topology/guide.md` matches topology format used in YAML.
- [ ] `README.md` reflects current module layout and conventions.
