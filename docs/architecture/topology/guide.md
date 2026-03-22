# Topology Guide

## What this is

`topology.yaml` is a structural inventory of the software — a complete list of components, entities, services, signals, and the calls between them. It describes _what exists and how things connect_, not _what things do_.

## Purpose

- Makes it easy to see the full shape of the system at a glance.
- Helps identify where a new feature belongs before writing any code.
- Serves as a checklist when reviewing against the pressure points in `docs/principles.md`.
- Gives a an AI agent and/or developer accurate context about what already exists, reducing the chance of duplicate or misplaced code.

## Rules

- **Keep it complete, not detailed.** List every component, entity, service, signal, and public action. Do not describe behaviour.
- **Update it when the structure changes.** Adding an entity, a presenter, a signal, or an AppController action all require an update here.
- **Names only.** No return types, no parameter descriptions, no docstrings.
- **One source of truth.** This file should reflect the code, and the code should reflect this file. If something exists in the codebase, it belongs here. If it's listed here and no longer exists, remove it.

## Structure

```
domain:
  entities      — domain objects and their fields
  components    — long-lived domain components (e.g. Store) with signals and actions
  services      — stateless domain-layer helpers

application:
  components    — long-lived application components with signals and actions
  services      — stateless application-layer helpers

ui:
  presenters    — one entry per presenter: its view, what signals it subscribes to,
                  and what components it calls
```
