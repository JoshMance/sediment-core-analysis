# Dev Cycle Checklist

A short list of documents worth consulting before starting work and again before committing.

---

## Before starting

- [ ] **[architecture/overview.md](architecture/overview.md)** — confirm which layer the work belongs in and where it should live.
- [ ] **[architecture/topology/topology.yaml](architecture/topology/topology.yaml)** — check what already exists. Entities, actions, signals, presenters. No need to reinvent the wheel every day.
- [ ] **[implementation_checklist.md](implementation_checklist.md)** — run structural checklists for panel wiring, science ownership, and documentation sync.

## Before committing

- [ ] **[principles.md](../architecture/principles.md)** — run through the DRY pressure points. Has anything that should be expressed once ended up in two places?
- [ ] **[architecture/overview.md](architecture/overview.md)** — update only if a layer's responsibilities or a core architectural decision has changed.
- [ ] **[architecture/topology/topology.yaml](architecture/topology/topology.yaml)** — update it to reflect any structural changes made: new entities, actions, signals, presenters, or services.
