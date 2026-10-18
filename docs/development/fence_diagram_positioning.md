# Fence Diagram Positioning: Absolute and Relative Offsets

## Overview

The fence diagram uses a two-value positioning model to decouple **what physically moves** (absolute position) from **what the user sees** (relative position relative to a reference baseline).

## Core Concepts

### Canvas = Absolute Reference Frame

- The canvas itself is the fixed visual coordinate system
- Canvas center (0.0 mm) is the fixed display anchor—this never moves
- Marked by an implied ruler always centered on screen

### Two Offset Values Per Core

Each core tracks:

1. **Absolute Offset** — The real position value (measured from canvas 0.0)
   - Storage: This is what actually changes during drag operations
   - Semantics: "Where is this core on the canvas ruler?"
   - Initial state: Reference core = 0.0 mm, all others = 0.0 mm
   - Dragging: Only the dragged core's absolute value changes

2. **Relative Offset** — The display value (measured from reference core's position)
   - Calculation: `relative = absolute - reference_absolute`
   - Display: This is what appears in labels and positioning
   - Semantics: "How far is this core from the reference core?"
   - Automatic: Recalculated after every absolute change

### Reference Core

- Serves as the measurement baseline (not just another draggable core)
- Its relative offset is always 0.0 mm (relative to itself)
- Its absolute offset can change when dragged
- When reference moves, all other cores' relative values recalculate (but absolute values stay constant)

## Drag Behavior

### Dragging the Reference Core

1. Reference's absolute offset changes by delta
2. Reference **moves visually** on canvas (position = canvas_center + absolute / mm_per_px)
3. All relative offsets recalculate (`relative = absolute - reference_absolute`)
4. Other cores' absolute offsets stay constant → **they don't move visually**
5. Other cores' labels (relative values) change

### Dragging Any Other Core

1. That core's absolute offset changes by delta
2. That core **moves visually** on canvas
3. Its relative offset recalculates
4. Result: Only that core's visual position changes

## Domain Storage (Future)

When moving to the domain layer for core combinations:

- **Store only relative offsets** in the combination entity
- Absolute values are transient UI state (not persisted)
- Rationale: Relative offsets fully capture the measurement relationship; absolute positions can be recreated by anchoring the reference at 0.0

Example:

```
Stored in domain:
  reference_core_id: "core_1"
  core_2_relative_offset: +50.0 mm
  core_3_relative_offset: -30.0 mm

At display time:
  reference_absolute = 0.0 (canvas center)
  core_2_absolute = 0.0 + 50.0 = 50.0
  core_3_absolute = 0.0 - 30.0 = -30.0
```

## Implementation Notes

- Absolute offset = what actually changes on drag; controls visual position on canvas
- Relative offset = calculated from absolute; shown in labels only
- User sees absolute positions visually but cares about (and reads) relative offsets as measurements
