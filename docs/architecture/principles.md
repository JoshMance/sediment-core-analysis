# Principles

This document covers how broad software engineering principles should be applied in this codebase. Not hard rules per se, but worth reviewing about before committing. It's also useful as a prompt for an AI agent — these are exactly the kinds of things agents tend to overlook when focused on solving the immediate problem.

---

## DRY (Don't Repeat Yourself) across components

Duplication _within_ a single file is a readability call — a developer can see it, and abstracting it away can sometimes make things worse. The duplication that causes real problems is **the same fact expressed in two or more unrelated files**. When that fact changes, every location must be updated, and none of them make it obvious the others exist.

The rule: **a fact that crosses component boundaries should be expressed once.**

### Example: AppController method surface

The clearest instance of this in the codebase is the AppController. Any user action — regardless of which presenter triggers it — maps to exactly one controller method. If two presenters can both initiate the same action, they call the same method. There is never a reason to have two controller methods that do the same thing for different callers.

### Pressure points

Intra-component repetition is out of scope here. When making changes, check these five cross-component seams:

| #   | Seam                                                                                                                                                                                                                                                       | Ask yourself                                               |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1   | **Entity type registration** — type dispatch logic can spread across multiple files. It should be registered in one place and derived everywhere else.                                                                                                     | Adding a new entity type: how many files change?           |
| 2   | **AppController method surface** — two presenters may independently implement the same action. Each distinct user action should map to exactly one controller method.                                                                                      | Two presenters doing the same thing: same method?          |
| 3   | **Panel registration** — the mapping from entity type to panel, and from panel to its factory, may end up in separate places. They should be expressed together.                                                                                           | Adding a new panel type: how many files change?            |
| 4   | **Store signal contract** — presenters implicitly depend on what signals carry and when they fire. If that contract changes, all consumers should be obviously affected.                                                                                   | Changing a signal shape: is it obvious what breaks?        |
| 5   | **Serialization/hydration pipeline** — entity serialization, asset bundling, and data reload are three stages of one pipeline owned by different parts of the system. If an entity changes, all three stages must stay in sync.                            | Adding a field to an entity: are all three stages obvious? |
| 6   | **Column type label set** — the valid type labels (`Text`, `Number`, `Date`) are expressed in three places: `_TYPE_OPTIONS` (view menu), `_dtype_to_label` (controller inference), and `_parse_cell_value` (view validation). All three must stay in sync. | Adding a new column type: did you update all three?        |
