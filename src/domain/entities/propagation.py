"""Field propagation rules for entities.

Declares which field changes cascade to related entities when written via
the Store.  The Store reads these rules inside ``update_field`` and fans
the change out automatically (BFS, cycle-safe).

To add a new cascading field
-----------------------------
1. Add a ``PropagationRule`` entry to ``PROPAGATION_RULES`` below.
2. That is all — the Store handles traversal and signal emission.

Rule semantics
--------------
``direction="down"``
    The value is written to every entity ID found in ``via`` (a list field).
``direction="up"``
    The value is written to the single entity ID found in ``via`` (a string
    field that may be ``None``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PropagationRule:
    """One cascading-field declaration.

    Attributes:
        entity_type: Entity class name this rule applies to (e.g. ``"CoreEntity"``).
        field:       Field name that triggers propagation when changed.
        direction:   ``"down"`` fans out to children; ``"up"`` propagates to parent.
        via:         Attribute on the entity that holds the related ID(s).
    """

    entity_type: str
    field: str
    direction: Literal["down", "up"]
    via: str


# ── Rules ─────────────────────────────────────────────────────────────────────
#
# Each entry here is the *only* place you need to touch to make a field cascade.

PROPAGATION_RULES: list[PropagationRule] = [
    # Spatial calibration cascades from a parent core down to all derived
    # child cores.  Children are listed in CoreEntity.child_core_ids.
    PropagationRule(
        entity_type="CoreEntity",
        field="mm_per_px",
        direction="down",
        via="child_core_ids",
    ),
    # Illuminant cascades the same way — if you set the capture illuminant
    # on a parent core, all derived cores inherit it.
    PropagationRule(
        entity_type="CoreEntity",
        field="illuminant",
        direction="down",
        via="child_core_ids",
    ),
    # Filter stack cascades to all child cores so they render with the
    # same processing pipeline as their parent.
    PropagationRule(
        entity_type="CoreEntity",
        field="filter_stack",
        direction="down",
        via="child_core_ids",
    ),
]
