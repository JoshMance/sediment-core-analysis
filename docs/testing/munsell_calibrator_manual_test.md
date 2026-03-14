# Manual Test: Munsell Calibrator

## Overview

A Munsell colour calibration tool embedded in the image panel. It allows the user to position an overlay grid over a Munsell chart photographed alongside a sediment core, then confirm the calibration to produce a mapping of `RGB → MunsellChip` for each chip in the selected page.

---

## Files Added

| File                                                                       | Purpose                                                                                                                 |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `src/science/__init__.py`                                                  | Package marker for science layer                                                                                        |
| `src/science/munsell.py`                                                   | Typed data model: `MunsellChip`, `MunsellValueRow`, `MunsellPage`, `MunsellBook`; `available_books()`, `get_book(name)` |
| `src/science/data/munsell_nearly_neutrals.json`                            | Munsell chip data (nearly-neutrals book)                                                                                |
| `src/ui/views/panels/image_panel/colour_calibrators/__init__.py`           | Package marker                                                                                                          |
| `src/ui/views/panels/image_panel/colour_calibrators/chip_grid.py`          | `MunsellChipGrid` — draggable/resizable overlay widget, emits `positionChanged`                                         |
| `src/ui/views/panels/image_panel/colour_calibrators/munsell_calibrator.py` | `MunsellCalibrator` panel with book/page dropdowns, Confirm button, and `_MiniGrid` live preview                        |

---

## Files Modified

| File                                             | Changes                                                                                                                                                                                                 |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ui/views/panels/image_panel/canvas.py`      | Added `calibrationComplete = Signal(list)`, `_on_munsell_page_selected()`, `_on_confirm_calibration()`, `_sample_current_grid()`, `_sample_3x3()`, `_current_cell_ratio()`, `_update_preview_colours()` |
| `src/ui/views/panels/image_panel/image_panel.py` | Added "Calibrate Munsell" checkable toolbar button and `set_calibrator_visible()`                                                                                                                       |

---

## Design Decisions

- **Book pre-selected on init** — the first book in the list is selected automatically at startup; users do not need to pick a book before picking a page.
- **Page required before Confirm** — the Confirm button is hidden until a page is selected from the dropdown.
- **Live preview via `positionChanged`** — as the grid is dragged or resized on the canvas, the `_MiniGrid` in the calibrator panel updates colour swatches in real time without needing to confirm.
- **Silent Confirm** — clicking Confirm samples the grid and emits `calibrationComplete(list[(rgb, MunsellChip)])`. The calibrator panel stays visible; nothing hides. A debug `print` statement shows RGB → notation pairs in the terminal.
- **3×3 pixel mean sampling** — at each chip crosshair centre, a 3×3 pixel neighbourhood is averaged to reduce noise.
- **Cell aspect ratio clamp** (`_MAX_CELL_RATIO = 2.0`) — cell height is clamped to at most 2× cell width, preventing degenerate elongated cells during resize.
- **4 corner handles only** — resize handles are L-bracket shaped brackets at the four corners, not filled squares and not 8-direction handles.
- **`MunsellChip.notation`** — stores the full Munsell notation as a single string e.g. `"5R 9/2"` (no separate hue/value/chroma fields on the chip object).

---

## Grid Visual Specification

| Element        | Style                                 |
| -------------- | ------------------------------------- |
| Cell borders   | 1 px white                            |
| Cell fill      | `rgba(255, 255, 255, 64)` — 25% white |
| Crosshairs     | 2 px white, centred in each cell      |
| Outer boundary | 1 px white border pen                 |
| Corner handles | White L-bracket lines (no fill)       |

---

## Manual Test Checklist

### Toggle

- [ ] Click **Calibrate Munsell** in the image panel toolbar — calibrator panel appears and the chip grid overlay appears on the canvas.
- [ ] Click **Calibrate Munsell** again — calibrator panel hides and the chip grid overlay hides.
- [ ] Switch to a different image tab and back — the calibrator state (visible/hidden) is preserved correctly per panel.

### Dropdowns

- [ ] Open the calibrator. A book is pre-selected in the Book dropdown on load.
- [ ] The Page dropdown is visible (or auto-selects a page) immediately.
- [ ] Changing the Book dropdown refreshes the Page dropdown with the correct pages for that book.
- [ ] Selecting a page makes the Confirm button visible and updates the chip grid overlay dimensions to match the page's row/column layout.
- [ ] Page count and chip layout shown in the grid match the selected page from `munsell_nearly_neutrals.json`.

### Drag

- [ ] Click and drag the chip grid from its interior — the entire grid moves with the mouse.
- [ ] Grid does not drift or jump on first click; it anchors to the cursor offset correctly.
- [ ] Dragging to the edges of the image does not cause the grid to move off-screen or crash.

### Resize from corners

- [ ] Drag the **top-left** L-bracket handle — grid resizes correctly, opposite corner stays fixed.
- [ ] Drag the **top-right** L-bracket handle — grid resizes correctly, opposite corner stays fixed.
- [ ] Drag the **bottom-left** L-bracket handle — grid resizes correctly, opposite corner stays fixed.
- [ ] Drag the **bottom-right** L-bracket handle — grid resizes correctly, opposite corner stays fixed.
- [ ] After each resize, crosshairs remain centred in their cells.

### Aspect ratio clamp

- [ ] Resize a corner by dragging downward excessively — cell height does not exceed 2× cell width.
- [ ] Resize a corner by dragging rightward — cells remain square to 2:1 portrait max; no extreme distortion.

### Live preview

- [ ] Move or resize the grid — the mini-grid swatches in the calibrator panel update in real time.
- [ ] Swatches reflect the colours visible under the crosshair positions on the image.
- [ ] Mock test: move the grid off the image (e.g., onto a blank area) — preview swatches show black or near-black (no image data).

### Confirm

- [ ] Click **Confirm** with a page selected — the terminal/console prints a line per chip in the format:
  ```
    RGB (r, g, b)  →  <notation>
  ```
- [ ] The number of printed lines matches the chip count for the selected page.
- [ ] The calibrator panel **remains visible** after confirm (does not hide).
- [ ] The `calibrationComplete` signal fires (verify via a connected debug slot or by observing downstream behaviour if wired up).

### Visual correctness

- [ ] Cell interiors have a semi-transparent white fill (visually ~25% opacity).
- [ ] Cell borders are 1 px white lines (visible against both dark and light images).
- [ ] Crosshairs are 2 px white lines centred in each cell.
- [ ] Outer boundary has a clear 1 px white border.
- [ ] Corner L-brackets are white, not filled squares.
- [ ] No artefacts or redraw glitches when resizing rapidly.

### Edge cases

- [ ] Load an image, open calibrator, close the image tab — no crash.
- [ ] Open calibrator with no image loaded — grid widget handles gracefully (no crash, no paint errors).
- [ ] Switch pages multiple times in quick succession — grid layout updates correctly each time.

---

## Known Debug State

The `_on_confirm_calibration` method on `canvas.py` currently contains a `print` statement that outputs RGB → notation pairs to stdout. This is intentional for manual testing and should be removed or gated behind a debug flag before any production release.
