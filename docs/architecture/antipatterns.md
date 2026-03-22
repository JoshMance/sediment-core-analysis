# Antipatterns

Things to avoid when working on this codebase.

## Generic store signals

Avoid vague signals like `stateChanged()`. Emit specific events that describe what changed and where.

## Presenter becoming a mini-controller

Presenters should interpret UI events and update views, not accumulate domain or workflow logic.

## Controller becoming a god object

Keep business actions in small command/use-case files. The controller should orchestrate, not implement everything.

## Store doing I/O or parsing

The store holds runtime state only. File formats, serialisation, and decoding belong in a persistence module.

## Presenters tightly coupling to store internals

Provide small, stable read methods on the store instead of letting presenters perform deep queries.

## Over-emitting signals during bulk operations

Batch updates or emit a single reset/bulk event to avoid UI thrashing.

## Signals that instruct instead of inform

Store events should announce facts (`entityUpdated`) rather than UI intentions (`refreshSidebar`).
