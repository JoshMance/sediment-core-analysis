# Core Studio Workflow Contract

This document defines the intended Core Studio behavior and ownership boundaries.

## Identity and Panel Rules

- Core Studio is core-bound.
- Workspace identity for Core Studio tabs is the CoreEntity id.
- At most one open Core Studio tab per CoreEntity.
- Different cores may be open in parallel.

## Draft Core Rule

- A core can exist in draft form using `is_draft: bool`.
- Draft cores are first-class entities and must appear in VariablesList.
- Opening a core into Core Studio must not create a second duplicate core.

## State Ownership

- Domain state lives on CoreEntity (for example: draft lifecycle and data availability facts).
- AppController is the only writer to Store.
- Views do not own workflow truth.
- Presenters translate domain facts to UI behavior (for example: visible columns).
- Presenters call Application services for scientific computations; they do not call `science.lib` directly.

## Column Visibility Rule

- Column visibility should be derived from core facts/capabilities.
- CoreEntity must not encode direct UI commands such as "show column".
- Presenter maps core facts to concrete visible/hidden columns.

## Current Behavior

- VariablesList context menu on a CoreEntity provides "Open In Core Studio".
- That action opens the existing core tab (or focuses it if already open).
- Ribbon "Core Studio" focuses the active core when applicable, otherwise the most recent existing core.
- If no core exists yet, Ribbon opens a blank Core Studio panel instance.
