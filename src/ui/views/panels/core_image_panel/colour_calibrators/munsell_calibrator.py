"""MunsellCalibrator — draggable overlay for Munsell calibration.

The widget is draggable anywhere within the bounds of its parent canvas widget.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from science.lib.munsell import MunsellPage, available_books, get_book

_TITLE_BAR_HEIGHT = 24
_DEFAULT_WIDTH = 220

_COMBO_STYLE = (
    "QComboBox { background: #2a2a2a; color: white; font-size: 11px;"
    "            border: 1px solid #555; border-radius: 3px; padding: 1px 4px; }"
    "QComboBox:disabled { color: #666; border-color: #444; }"
    "QComboBox QAbstractItemView { background: #2a2a2a; color: white;"
    "                              selection-background-color: #0078d4; }"
)
_LABEL_STYLE = "background: transparent; color: #ccc; font-size: 11px;"
_LABEL_DISABLED_STYLE = "background: transparent; color: #555; font-size: 11px;"
_MINI_GRID_MAX_H = 160  # cap so the calibrator doesn't grow unbounded


class _MiniGrid(QWidget):
    """Read-only miniature chip colour preview shown inside the calibrator panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: int = 0
        self._cols: int = 0
        self._chip_cells: frozenset[tuple[int, int]] = frozenset()
        self._colours: dict[tuple[int, int], QColor] = {}
        self._cell_ratio: float = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_page(self, page: MunsellPage) -> None:
        all_chromas = sorted({c.chroma for row in page.values for c in row.chromas})
        chroma_to_col = {c: i for i, c in enumerate(all_chromas)}
        self._rows = len(page.values)
        self._cols = len(all_chromas)
        cells: set[tuple[int, int]] = set()
        for r, row in enumerate(page.values):
            for chip in row.chromas:
                cells.add((r, chroma_to_col[chip.chroma]))
        self._chip_cells = frozenset(cells)
        self._colours = {}
        self._recalc_height()
        self.update()

    def set_colours(self, colours: dict[tuple[int, int], tuple[int, int, int]]) -> None:
        self._colours = {k: QColor(*v) for k, v in colours.items()}
        self.update()

    def set_cell_ratio(self, ratio: float) -> None:
        """Update the cell aspect ratio (cell_h / cell_w) and recalculate height."""
        self._cell_ratio = max(0.1, ratio)
        self._recalc_height()

    def _recalc_height(self) -> None:
        if not self._cols or not self._rows:
            return
        available_w = _DEFAULT_WIDTH - 12  # widget width minus left+right margins
        cell_px_h = (available_w / self._cols) * self._cell_ratio
        h = max(20, min(_MINI_GRID_MAX_H, int(cell_px_h * self._rows)))
        self.setFixedHeight(h)

    def clear(self) -> None:
        self._rows = 0
        self._cols = 0
        self._chip_cells = frozenset()
        self._colours = {}
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Background card
        painter.setBrush(QColor(20, 20, 20, 200))
        painter.setPen(QPen(QColor(70, 70, 70, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 3, 3)
        if not self._rows or not self._cols:
            return
        cw = self.width() / self._cols
        ch = self.height() / self._rows
        for r, c in self._chip_cells:
            fill = self._colours.get((r, c), QColor(55, 55, 55, 200))
            painter.setBrush(fill)
            painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
            painter.drawRect(QRectF(c * cw, r * ch, cw, ch))


class MunsellCalibrator(QWidget):
    """Floating overlay widget draggable anywhere within the canvas viewport."""

    # Emitted when the user selects a page; None when selection is cleared.
    pageSelected = Signal(object)  # MunsellPage | None
    # Emitted when the user clicks "Confirm" to sample the chip grid.
    confirmRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dragging = False
        self._drag_offset = QPoint()

        self.setFixedWidth(_DEFAULT_WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        self._build_ui()
        self.hide()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 8)
        layout.setSpacing(4)

        title = QLabel("Munsell Calibrator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(_TITLE_BAR_HEIGHT - 4)
        title.setStyleSheet(
            "background: transparent; color: white;"
            " font-weight: bold; font-size: 11px;"
        )
        layout.addWidget(title)

        # ── Book row ──────────────────────────────────────────────────────
        book_row = QHBoxLayout()
        book_row.setContentsMargins(0, 0, 0, 0)
        book_row.setSpacing(4)

        book_label = QLabel("Select Book:")
        book_label.setFixedWidth(72)
        book_label.setStyleSheet(_LABEL_STYLE)
        book_row.addWidget(book_label)

        self._book_combo = QComboBox()
        self._book_combo.setCursor(Qt.CursorShape.ArrowCursor)
        self._book_combo.addItem("— select book —")
        self._book_combo.addItems(available_books())
        self._book_combo.setStyleSheet(_COMBO_STYLE)
        self._book_combo.currentIndexChanged.connect(self._on_book_changed)
        book_row.addWidget(self._book_combo, 1)

        layout.addLayout(book_row)

        # ── Page row ──────────────────────────────────────────────────────
        page_row = QHBoxLayout()
        page_row.setContentsMargins(0, 0, 0, 0)
        page_row.setSpacing(4)

        self._page_label = QLabel("Select Page:")
        self._page_label.setFixedWidth(72)
        self._page_label.setStyleSheet(_LABEL_DISABLED_STYLE)
        page_row.addWidget(self._page_label)

        self._page_combo = QComboBox()
        self._page_combo.setCursor(Qt.CursorShape.ArrowCursor)
        self._page_combo.addItem("— select page —")
        self._page_combo.setEnabled(False)
        self._page_combo.setStyleSheet(_COMBO_STYLE)
        self._page_combo.currentIndexChanged.connect(self._on_page_changed)
        page_row.addWidget(self._page_combo, 1)

        layout.addLayout(page_row)

        # ── Mini grid preview ──────────────────────────────────────────
        self._mini_grid = _MiniGrid()
        self._mini_grid.hide()
        layout.addWidget(self._mini_grid)

        # ── Confirm button ────────────────────────────────────────────
        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setCursor(Qt.CursorShape.ArrowCursor)
        self._confirm_btn.setFixedHeight(26)
        self._confirm_btn.setStyleSheet(
            "QPushButton { background: #0078d4; color: white; font-size: 11px;"
            "              font-weight: bold; border: 1px solid #005a9e;"
            "              border-radius: 3px; }"
            "QPushButton:hover { background: #106ebe; }"
            "QPushButton:pressed { background: #005a9e; }"
        )
        self._confirm_btn.clicked.connect(self.confirmRequested.emit)
        self._confirm_btn.setVisible(False)
        layout.addWidget(self._confirm_btn)

        # Pre-select the first available book so the widget is ready to use.
        if available_books():
            self._book_combo.setCurrentIndex(1)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_book_changed(self, index: int) -> None:
        self._page_combo.blockSignals(True)
        self._page_combo.clear()
        if index == 0:
            self._page_combo.addItem("— select page —")
            self._page_combo.setEnabled(False)
            self._page_label.setStyleSheet(_LABEL_DISABLED_STYLE)
        else:
            book_name = self._book_combo.currentText()
            book = get_book(book_name)
            self._page_combo.addItem("— select page —")
            self._page_combo.addItems([p.hue for p in book.pages])
            self._page_combo.setEnabled(True)
            self._page_label.setStyleSheet(_LABEL_STYLE)
        self._page_combo.blockSignals(False)        # Book change always clears the page selection.
        self._confirm_btn.setVisible(False)
        self._mini_grid.clear()
        self._mini_grid.hide()
        self._after_layout_change()
        self.pageSelected.emit(None)

    def _on_page_changed(self, index: int) -> None:
        if index < 0:
            return
        book_idx = self._book_combo.currentIndex()
        if book_idx == 0 or index == 0:
            self._confirm_btn.setVisible(False)
            self._mini_grid.hide()
            self._after_layout_change()
            self.pageSelected.emit(None)
            return
        book = get_book(self._book_combo.currentText())
        page = book.pages[index - 1]  # -1 because index 0 is the placeholder
        self._mini_grid.set_page(page)
        self._mini_grid.show()
        self._confirm_btn.setVisible(True)
        self._after_layout_change()
        self.pageSelected.emit(page)
    # ── Public API ──────────────────────────────────────────────────────────
    def set_preview_colours(
        self,
        colours: dict[tuple[int, int], tuple[int, int, int]],
        cell_ratio: float = 1.0,
    ) -> None:
        """Update the mini grid preview with newly sampled colours and current cell ratio."""
        self._mini_grid.set_cell_ratio(cell_ratio)
        self._mini_grid.set_colours(colours)
        self._after_layout_change()
    def sync_to_canvas(self) -> None:
        """Re-clamp position to parent bounds (e.g. after a canvas resize)."""
        if not self.parent():
            return
        p = self.parent()
        x = max(0, min(self.x(), p.width() - self.width()))
        y = max(0, min(self.y(), p.height() - self.height()))
        self.move(x, y)
        self.raise_()

    def _after_layout_change(self) -> None:
        """Recalculate own height after children are shown/hidden, then re-clamp."""
        self.adjustSize()
        self.sync_to_canvas()

    # ── Painting ────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent dark card background.
        painter.setBrush(QColor(30, 30, 30, 210))
        painter.setPen(QPen(QColor(100, 100, 100, 220), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)

        # Divider below the title bar.
        painter.setPen(QPen(QColor(80, 80, 80, 180), 1))
        painter.drawLine(1, _TITLE_BAR_HEIGHT, self.width() - 2, _TITLE_BAR_HEIGHT)

        super().paintEvent(event)

    # ── Mouse interaction ────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragging or not self.parent():
            event.accept()
            return

        p = self.parent()
        target = self.mapToParent(event.position().toPoint() - self._drag_offset)
        x = max(0, min(target.x(), p.width() - self.width()))
        y = max(0, min(target.y(), p.height() - self.height()))
        self.move(x, y)
        self.raise_()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        event.accept()
