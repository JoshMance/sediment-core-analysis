## Why use Model–View in large Qt apps?

When your state is real data (rows, trees, domain objects), don’t store it in widgets.

Use QAbstractItemModel so:

- the model owns the data
- views are just windows onto it
- multiple views can show the same data at once

---

## What you get for free

When you do:

table.setModel(model)

Qt automatically handles:

- change notifications (views update when data changes)
- partial updates (only changed cells repaint)
- selection state
- undo/redo (via QUndoStack)
- multiple synced views (table + plot + tree)

No manual signal wiring between widgets.

---

## Why this matters for serious tools (like Sedivis)

Scientific / engineering apps need:

- large datasets
- multiple coordinated views
- predictable performance
- clean separation of UI and data

Model–View gives you that without UI spaghetti.

---

## One-line takeaway

If it’s data, put it in a model — not a widget.

That’s Qt’s power move.
