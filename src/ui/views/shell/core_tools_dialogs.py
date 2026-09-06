"""Transient dialogs for core-section operations."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QStackedLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.resources.theme import theme_color


class _CoreToolsDialog(QDialog):
    """Base canvas for a core-section operation."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(640, 520)


class JoinCoresDialog(_CoreToolsDialog):
    """Modal canvas for joining two core sections."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Join Core Sections", parent)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(buttons)


class _SplitPreview(QWidget):
    """Displays the scrollable source image for the fixed split centerline."""

    positionChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setMouseTracking(True)

    def set_source(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        preview_width = min(440, max(280, pixmap.width()))
        preview_height = max(1, round(pixmap.height() * preview_width / pixmap.width()))
        self.setFixedSize(preview_width, preview_height)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        if self._pixmap is None:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No core image available")
            return
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self._pixmap)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_position_from_widget(event.position().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._set_position_from_widget(event.position().toPoint())

    def _set_position_from_widget(self, point: QPoint) -> None:
        if self._pixmap is None:
            return
        position = round(point.y() * self._pixmap.height() / self.height())
        maximum = self._pixmap.height() - 1
        self.positionChanged.emit(max(1, min(position, maximum)))


class _SplitCenterLine(QWidget):
    """Non-interactive fixed split line drawn over the detailed viewport."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("splitCenterLine")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(QPen(QColor(theme_color("image_selection")), 2))
        y = self.height() // 2
        painter.drawLine(QPoint(0, y), QPoint(self.width(), y))


class _SplitOverview(QWidget):
    """Full-image navigator for the scrollable split preview."""

    viewRequested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("splitOverview")
        self.setFixedSize(120, 260)
        self._pixmap: QPixmap | None = None
        self._visible_top = 0.0
        self._visible_height = 0.0
        self.setMouseTracking(True)

    def set_state(
        self,
        pixmap: QPixmap,
        visible_top: float,
        visible_height: float,
    ) -> None:
        self._pixmap = pixmap
        self._visible_top = visible_top
        self._visible_height = visible_height
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        if self._pixmap is None:
            return
        target = self._target_rect()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target.toRect(), self._pixmap)

        visible_top = target.top() + target.height() * self._visible_top / self._pixmap.height()
        visible_bottom = target.top() + target.height() * (
            self._visible_top + self._visible_height
        ) / self._pixmap.height()
        mask = QColor(theme_color("image_overview_mask"))
        mask.setAlpha(150)
        painter.fillRect(QRectF(target.left(), target.top(), target.width(), visible_top - target.top()), mask)
        painter.fillRect(QRectF(target.left(), visible_bottom, target.width(), target.bottom() - visible_bottom), mask)
        painter.setPen(QPen(QColor(theme_color("image_selection")), 1))
        painter.drawRect(QRectF(target.left(), visible_top, target.width(), visible_bottom - visible_top))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._pixmap is None:
            return
        target = self._target_rect()
        if not target.contains(event.position()):
            return
        position = round((event.position().y() - target.top()) * self._pixmap.height() / target.height())
        self.viewRequested.emit(max(0, min(position, self._pixmap.height() - 1)))

    def _target_rect(self) -> QRectF:
        if self._pixmap is None:
            return QRectF()
        available = self.rect().adjusted(8, 8, -8, -8)
        size = self._pixmap.size()
        size.scale(available.size(), Qt.AspectRatioMode.KeepAspectRatio)
        return QRectF(
            (self.width() - size.width()) / 2,
            (self.height() - size.height()) / 2,
            size.width(),
            size.height(),
        )


class SplitCoreDialog(_CoreToolsDialog):
    """Modal input view for a non-destructive core split."""

    splitRequested = Signal(str, str, int, str, str)

    def __init__(
        self,
        core_options: list[tuple[str, str, int, int, float, QPixmap]],
        parent: QWidget | None = None,
        preferred_core_id: str | None = None,
    ) -> None:
        super().__init__("Split Core Section", parent)
        self._core_options = {
            core_id: (name, width, height, mm_per_px, pixmap)
            for core_id, name, width, height, mm_per_px, pixmap in core_options
        }

        self._source_combo = QComboBox()
        for core_id, name, _width, _height, _mm_per_px, _pixmap in core_options:
            self._source_combo.addItem(name, userData=core_id)
        self._source_combo.currentIndexChanged.connect(lambda _index: self._select_source())

        self._horizontal = QRadioButton("Horizontal")
        self._vertical = QRadioButton("Vertical")
        orientation = QButtonGroup(self)
        orientation.addButton(self._horizontal)
        orientation.addButton(self._vertical)
        self._horizontal.toggled.connect(lambda _checked: self._update_source())
        orientation_row = QWidget()
        orientation_layout = QHBoxLayout(orientation_row)
        orientation_layout.setContentsMargins(0, 0, 0, 0)
        orientation_layout.addWidget(self._horizontal)
        orientation_layout.addWidget(self._vertical)
        orientation_layout.addStretch()

        self._preview = _SplitPreview()
        self._preview.positionChanged.connect(self._set_split_position)
        self._preview_scroll = QScrollArea()
        self._preview_scroll.setWidget(self._preview)
        self._preview_scroll.setWidgetResizable(False)
        self._preview_scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self._preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._preview_scroll.setMinimumHeight(260)
        self._preview_scroll.verticalScrollBar().valueChanged.connect(self._sync_split_to_scroll)
        self._center_line = _SplitCenterLine()
        self._detail_view = QWidget()
        detail_layout = QStackedLayout(self._detail_view)
        detail_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(self._preview_scroll)
        detail_layout.addWidget(self._center_line)
        self._center_line.raise_()
        self._overview = _SplitOverview()
        self._overview.viewRequested.connect(self._scroll_to_overview_position)
        self._split_position = QSpinBox()
        self._first_name = QLineEdit()
        self._second_name = QLineEdit()
        self._first_name_edited = False
        self._second_name_edited = False
        self._first_name.textEdited.connect(self._mark_first_name_edited)
        self._second_name.textEdited.connect(self._mark_second_name_edited)
        self._first_name.setTextMargins(3, 3, 3, 3)
        self._second_name.setTextMargins(3, 3, 3, 3)
        self._split_position.setFixedHeight(self._first_name.sizeHint().height())
        self._split_position.valueChanged.connect(self._update_preview)
        self._position_label = QLabel()

        form = QFormLayout()
        form.addRow("Source core:", self._source_combo)
        form.addRow("Split direction:", orientation_row)
        form.addRow("Split at:", self._split_position)
        form.addRow("First section:", self._first_name)
        form.addRow("Second section:", self._second_name)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._split_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._split_button.setText("Split")
        self._split_button.setEnabled(bool(core_options))
        buttons.accepted.connect(self._request_split)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(self._detail_view, 1)
        preview_row.addWidget(self._overview)
        preview_row.addStretch()
        layout.addLayout(preview_row, 1)
        layout.addWidget(self._position_label)
        layout.addWidget(buttons)
        if preferred_core_id in self._core_options:
            self._source_combo.setCurrentIndex(self._source_combo.findData(preferred_core_id))
        self._select_source()

    def _axis(self) -> str:
        return "horizontal" if self._horizontal.isChecked() else "vertical"

    def _select_source(self) -> None:
        core_id = self._source_combo.currentData()
        option = self._core_options.get(core_id)
        if option is None:
            return
        _name, width, height, _mm_per_px, _pixmap = option
        self._first_name_edited = False
        self._second_name_edited = False
        self._horizontal.blockSignals(True)
        self._vertical.blockSignals(True)
        (self._horizontal if height >= width else self._vertical).setChecked(True)
        self._horizontal.blockSignals(False)
        self._vertical.blockSignals(False)
        self._update_source(reset_names=True)

    def _update_source(self, reset_names: bool = False) -> None:
        core_id = self._source_combo.currentData()
        option = self._core_options.get(core_id)
        if option is None:
            self._split_position.setRange(0, 0)
            self._position_label.clear()
            return
        name, width, height, mm_per_px, pixmap = option
        self._split_position.blockSignals(True)
        length = height if self._axis() == "horizontal" else width
        self._split_position.setRange(1, max(1, length - 1))
        self._split_position.setValue(max(1, length // 2))
        self._split_position.blockSignals(False)
        first, second = ("Upper", "Lower") if self._axis() == "horizontal" else ("Left", "Right")
        if reset_names or not self._first_name_edited:
            self._first_name.setText(f"{name} {first.lower()}")
        if reset_names or not self._second_name_edited:
            self._second_name.setText(f"{name} {second.lower()}")
        preview_pixmap = pixmap if self._axis() == "horizontal" else pixmap.transformed(QTransform().rotate(90))
        self._preview.set_source(preview_pixmap)
        self._update_position_label()
        QTimer.singleShot(0, self._reveal_split)

    def _mark_first_name_edited(self, _text: str) -> None:
        self._first_name_edited = True

    def _mark_second_name_edited(self, _text: str) -> None:
        self._second_name_edited = True

    def _set_split_position(self, position: int) -> None:
        self._split_position.setValue(position)

    def _update_preview(self) -> None:
        self._update_position_label()
        QTimer.singleShot(0, self._reveal_split)

    def _reveal_split(self) -> None:
        if self._preview._pixmap is None:
            return
        preview_y = self._split_position.value() * self._preview.height() / self._preview._pixmap.height()
        scroll_bar = self._preview_scroll.verticalScrollBar()
        scroll_bar.setValue(round(preview_y - self._preview_scroll.viewport().height() / 2))
        self._update_overview()

    def _scroll_to_overview_position(self, position: int) -> None:
        if self._preview._pixmap is None:
            return
        preview_y = position * self._preview.height() / self._preview._pixmap.height()
        scroll_bar = self._preview_scroll.verticalScrollBar()
        scroll_bar.setValue(round(preview_y - self._preview_scroll.viewport().height() / 2))

    def _sync_split_to_scroll(self) -> None:
        if self._preview._pixmap is None:
            return
        source_y = round(
            (self._preview_scroll.verticalScrollBar().value()
             + self._preview_scroll.viewport().height() / 2)
            * self._preview._pixmap.height() / self._preview.height()
        )
        self._split_position.blockSignals(True)
        self._split_position.setValue(max(1, min(source_y, self._preview._pixmap.height() - 1)))
        self._split_position.blockSignals(False)
        self._update_position_label()
        self._update_overview()

    def _update_overview(self) -> None:
        if self._preview._pixmap is None:
            return
        scale = self._preview._pixmap.height() / self._preview.height()
        visible_top = self._preview_scroll.verticalScrollBar().value() * scale
        visible_height = self._preview_scroll.viewport().height() * scale
        self._overview.set_state(
            self._preview._pixmap,
            visible_top,
            visible_height,
        )

    def _update_position_label(self) -> None:
        core_id = self._source_combo.currentData()
        option = self._core_options.get(core_id)
        if option is None:
            return
        mm_per_px = option[3]
        position = self._split_position.value()
        text = f"{position} px"
        if mm_per_px > 0:
            text += f"  |  {position * mm_per_px:.2f} mm"
        self._position_label.setText(text)

    def _request_split(self) -> None:
        source_id = self._source_combo.currentData()
        first_name = self._first_name.text().strip()
        second_name = self._second_name.text().strip()
        if not source_id or not first_name or not second_name:
            return
        self.splitRequested.emit(source_id, self._axis(), self._split_position.value(), first_name, second_name)
        self.accept()