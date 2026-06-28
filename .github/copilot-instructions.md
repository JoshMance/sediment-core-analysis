# Sedivis — Agent Instructions

Before implementing anything, read the following docs in full. They define architecture, ownership boundaries, and what to avoid. Implementing against these rules is worse than not implementing at all.

## Required reading (always)

- `docs/architecture/overview.md` — layer boundaries, component roles, dependency rules
- `docs/architecture/principles.md` — DRY pressure points; the six cross-component seams to check
- `docs/architecture/antipatterns.md` — explicit things to avoid
- `docs/architecture/topology/topology.yaml` — what already exists (entities, signals, actions, presenters); check this before adding anything new
- `docs/development/checklist.md` — what to verify before starting and before committing

## Read when relevant

- `docs/development/implementation_checklist.md` — structural checklists for new panels, science changes, Core Studio work, and doc sync
- `docs/development/core_studio_workflow.md` — Core Studio identity rules, draft core behaviour, state ownership, column visibility
- `docs/planning/saving and loading.md` — `.sedivis` format, save/load flow, serialization ownership
- `docs/development/ribbon_guide.md` — how to add ribbon buttons (view + presenter, same label key)

## Hard rules (non-negotiable)

- **Layer dependencies flow inward only**: UI → Application → Domain. Never the reverse.
- **`AppController` is the sole writer to the Store.** Presenters call it; they do not write state directly.
- **Scientific logic lives in `science/` only.** Do not reimplement RGB/CIELAB/Munsell logic in any other layer.
- **Application Services are internal to the Application layer.** Nothing outside `src/application/` imports them directly.
- **Store signals announce facts, not UI instructions.** (`entityUpdated`, not `refreshSidebar`).
- **Presenters translate domain facts to UI behaviour.** They do not accumulate workflow logic.
- **`topology.yaml` must be updated** whenever structure changes: new entities, actions, signals, presenters, or services.

## Before writing any code

1. Check `topology.yaml` — does what you need already exist?
2. Identify which layer the work belongs in (overview.md).
3. Check the six DRY pressure points (principles.md) — will your change require multiple files to stay in sync?
4. If adding a panel, run through the panel checklist (implementation_checklist.md §1).
5. If touching science behaviour, run through the science checklist (implementation_checklist.md §2).
