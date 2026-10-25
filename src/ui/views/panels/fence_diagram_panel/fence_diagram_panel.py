"""FenceDiagramPanel — core alignment visualization with draggable lanes."""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QMouseEvent, QDragEnterEvent, QDropEvent, QPixmap, QTransform
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel, QScrollArea, QSpacerItem, QSizePolicy

from .offset_ruler import OffsetRulerColumn

ENTITY_MIME_TYPE = "application/x-entity-id"

# Suppress Qt warning about disconnecting signals that don't have connections
warnings.filterwarnings("ignore", message=".*Failed to disconnect.*from signal.*")

# UI Constants
CORE_BOX_WIDTH_PX = 260
CORE_BOX_HEIGHT_PX = 420
TRACK_WIDTH_PX = 160  # Width of each data track
MAX_DRAG_OFFSET_PX = 2000  # Safety clamp: prevent runaway scrolling from single drag
INITIAL_SPACER_HEIGHT_PX = 50  # Minimal initial space above/below core; grows dynamically with dragging
OFFSET_LABEL_HEIGHT_PX = 20  # Height of offset text label below core
CORE_LABEL_SPACING_PX = 8  # Spacing between core box and offset label
LANE_SPACING_PX = 5  # Inter-lane horizontal spacing
CENTER_LAYOUT_PADDING_PX = 40  # Top/bottom padding in lanes container
LEFT_LANE_PADDING_PX = 20  # Left padding before lanes (right of ruler)


@dataclass
class LaneConfig:
    """Temporary lane state model (before moving to domain).
    
    Tracks both absolute position (what actually changes on drag) and
    relative position (what user sees, calculated from absolute values).
    """
    id: str
    core_id: str | None = None
    core_name: str | None = None
    absolute_offset_mm: float = 0.0  # Storage: actual position on canvas
    relative_offset_mm: float = 0.0  # Display: position relative to reference (calculated)
    width_px: int = CORE_BOX_WIDTH_PX
    height_px: int = CORE_BOX_HEIGHT_PX


class _CoreBoxCross(QWidget):
    """Custom widget that draws a centered cross."""

    def paintEvent(self, event):
        """Draw a + cross in the center."""
        painter = QPainter(self)
        pen = QPen(QColor("#CBD5E1"), 2)  # 2px stroke to match border
        painter.setPen(pen)

        cx = self.width() // 2
        cy = self.height() // 2
        line_size = 30  # Slightly smaller cross

        # Horizontal line
        painter.drawLine(cx - line_size, cy, cx + line_size, cy)
        # Vertical line
        painter.drawLine(cx, cy - line_size, cx, cy + line_size)

        painter.end()


class _DraggableLaneBox(QWidget):
    """A draggable core box with offset label below it."""
    
    offsetChanged = Signal(float)  # Emitted during drag, value in pixels
    dragFinished = Signal()  # Emitted when user releases mouse
    coreDropped = Signal(str)  # Emitted when a core is dropped on this lane, passes core_id
    
    def __init__(self, lane_id: str, width_px: int = CORE_BOX_WIDTH_PX, height_px: int = CORE_BOX_HEIGHT_PX, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lane_id = lane_id
        self.width_px = width_px
        self.height_px = height_px
        print(f"[_DraggableLaneBox.__init__] {lane_id}: width_px={width_px}, height_px={height_px}")
        self._initial_spacer_height = INITIAL_SPACER_HEIGHT_PX  # Minimal initial space; grows dynamically with dragging
        self._drag_start_y = 0
        self._is_dragging = False
        self._current_offset_px = 0.0  # Track cumulative vertical offset
        
        # Accept drops
        self.setAcceptDrops(True)
        
        # Fix width; height expands naturally as spacers grow with dragging
        self.setFixedWidth(width_px)
        # Start with minimal height: core + initial spacers
        min_height = height_px + 2 * self._initial_spacer_height
        self.setMinimumHeight(min_height)
        
        # Prevent this lane from being stretched to match other lanes' heights
        # (Horizontal growth: ignored because width is fixed; Vertical: stay at minimum unless explicitly resized)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        # Main container with flexible spacers for positioning
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top spacer (grows/shrinks dynamically as offset changes)
        self._top_spacer = QSpacerItem(0, self._initial_spacer_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(self._top_spacer)
        
        # Container for core box + offset label (keeps them together)
        core_container = QWidget()
        core_layout = QVBoxLayout(core_container)
        core_layout.setContentsMargins(0, 0, 0, 0)
        core_layout.setSpacing(CORE_LABEL_SPACING_PX)
        
        # Core box (draggable area)
        self._core_box = self._make_core_box()
        core_layout.addWidget(self._core_box)
        
        # Offset label (below box)
        self._offset_label = QLabel("0.0 mm")
        self._offset_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._offset_label.setStyleSheet(
            "QLabel { font-size: 11px; color: #64748B; font-weight: 500; }"
        )
        self._offset_label.setFixedHeight(OFFSET_LABEL_HEIGHT_PX)
        core_layout.addWidget(self._offset_label)
        
        # Add core container to main layout
        main_layout.addWidget(core_container)
        
        # Bottom spacer (grows/shrinks dynamically as offset changes)
        self._bottom_spacer = QSpacerItem(0, self._initial_spacer_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(self._bottom_spacer)
        
        # Store reference to layout for updating spacer stretches
        self._main_layout = main_layout
        self._current_vertical_offset_px = 0.0  # Track current offset for ruler anchor calculation
    
    def set_offset_text(self, text: str) -> None:
        """Update the offset label display."""
        self._offset_label.setText(text)
    
    def set_core_name(self, core_name: str) -> None:
        """Update the core name display in the box."""
        if hasattr(self, '_core_name_label'):
            self._core_name_label.setText(core_name)
    
    def set_core_image(self, pixmap: QPixmap) -> None:
        """Display a core image, hiding the placeholder cross and border.
        
        Pixmap should already be scaled to the correct size based on mm_per_px calibration.
        We only rotate it and display it; no further scaling.
        """
        if not hasattr(self, '_core_image_label') or not hasattr(self, '_border_frame'):
            return
        
        # Rotate pixmap 90° clockwise so depth runs vertically (top to bottom)
        transform = QTransform().rotate(90)
        rotated = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        # Set pixmap (already properly scaled, QLabel will center it)
        self._core_image_label.setPixmap(rotated)
        # Force label to size itself to the pixmap, not vice versa
        self._core_image_label.adjustSize()
        self._core_image_label.show()
        
        # Remove border frame from layout to free up space for image
        parent_layout = self._core_box.layout()
        if parent_layout:
            parent_layout.removeWidget(self._border_frame)
        self._border_frame.hide()
    
    def set_vertical_offset(self, offset_px: float, max_offset_px: float | None = None) -> None:
        """Move the core vertically by resizing top/bottom spacers.
        
        Positive offset moves core down, negative offset moves core up.
        Spacers grow/shrink dynamically; no pre-allocated limits.
        
        Args:
            offset_px: Desired vertical offset in pixels.
            max_offset_px: Maximum allowed offset (clamps movement to scroll area bounds).
                If None, uses MAX_DRAG_OFFSET_PX safety limit.
        
        IMPORTANT: Always keep a minimum draggable strip visible at top/bottom
        so the core remains clickable even at extreme offsets.
        """
        # Clamp to either physical bounds (max_offset_px) or safety limit
        if max_offset_px is not None:
            clamped_offset = max(-max_offset_px, min(max_offset_px, float(offset_px)))
        else:
            clamped_offset = max(-MAX_DRAG_OFFSET_PX, min(MAX_DRAG_OFFSET_PX, float(offset_px)))
        self._current_vertical_offset_px = clamped_offset  # Store for ruler anchor calculation
        
        # Adjust spacing based on offset: positive offset increases top_spacer (core moves down)
        # CRITICAL: Keep minimum spacer height (10px) so core header is always visible for dragging
        MIN_VISIBLE_HEIGHT = 10
        top_height = max(MIN_VISIBLE_HEIGHT, self._initial_spacer_height + int(clamped_offset))
        bottom_height = max(MIN_VISIBLE_HEIGHT, self._initial_spacer_height - int(clamped_offset))
        
        # Update spacer sizes
        self._top_spacer.changeSize(0, top_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self._bottom_spacer.changeSize(0, bottom_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        # Force immediate layout recalculation and repaint
        self._main_layout.invalidate()
        self._main_layout.activate()
        self.update()
    
    def get_vertical_offset_px(self) -> float:
        """Return the current vertical offset in pixels."""
        return self._current_vertical_offset_px
    
    def _make_core_box(self) -> QWidget:
        """Create the draggable core box with cross placeholder and image area."""
        container = QWidget()
        container.setFixedWidth(self.width_px)
        # Height will be determined by contents (image or placeholder)
        container.setCursor(Qt.CursorShape.OpenHandCursor)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image label (initially hidden, shown when core is dropped)
        # Add to outer layout so it shows when border frame is hidden
        self._core_image_label = QLabel()
        self._core_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._core_image_label.setStyleSheet("background-color: transparent;")
        self._core_image_label.hide()
        layout.addWidget(self._core_image_label)  # Size to pixmap, don't stretch
        
        # Border frame (for empty state: name label + cross placeholder)
        self._border_frame = QFrame()
        self._border_frame.setFrameShape(QFrame.Shape.NoFrame)
        self._border_frame.setStyleSheet(
            "QFrame { border: 2px dashed #94A3B8; border-radius: 6px; background-color: white; }"
        )
        
        inner_layout = QVBoxLayout(self._border_frame)
        inner_layout.setContentsMargins(8, 8, 8, 8)
        inner_layout.setSpacing(4)
        
        # Core name label (shows which core is in this lane)
        self._core_name_label = QLabel("—")
        self._core_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._core_name_label.setStyleSheet(
            "QLabel { font-size: 9px; color: #475569; font-weight: 600; }"
        )
        self._core_name_label.setWordWrap(True)
        inner_layout.addWidget(self._core_name_label)
        
        inner_layout.addStretch()
        
        # Cross placeholder (shown when no core, hidden when core is dropped)
        self._cross_placeholder = _CoreBoxCross()
        self._cross_placeholder.setFixedHeight(80)
        self._cross_placeholder.setStyleSheet("background-color: transparent;")
        inner_layout.addWidget(self._cross_placeholder)
        
        inner_layout.addStretch()
        
        layout.addWidget(self._border_frame)
        
        return container
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start dragging when clicking anywhere on the lane."""
        # Any mouse press on this lane starts a drag (no geometry check needed)
        self._is_dragging = True
        self._drag_start_y = event.globalY()
        self._core_box.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Emit offset change during drag."""
        if self._is_dragging:
            delta_y = event.globalY() - self._drag_start_y
            # Dragging DOWN (positive Y) → positive offset; dragging UP (negative Y) → negative offset
            self.offsetChanged.emit(float(delta_y))
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finish dragging."""
        if self._is_dragging:
            self._is_dragging = False
            self._core_box.setCursor(Qt.CursorShape.OpenHandCursor)
            self.dragFinished.emit()
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drops with entity ID."""
        if event.mimeData().hasFormat(ENTITY_MIME_TYPE):
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event) -> None:
        """Just accept the leave."""
        pass
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop of core onto this lane."""
        if event.mimeData().hasFormat(ENTITY_MIME_TYPE):
            data = event.mimeData().data(ENTITY_MIME_TYPE)
            core_id = bytes(data).decode("utf-8")
            self.coreDropped.emit(core_id)
            event.acceptProposedAction()


class _DataTrackPlaceholder(QWidget):
    """Placeholder data track widget — vertical strip that moves with its paired lane.
    
    Currently just a colored rectangle. Will eventually render line plots or
    correlation curves. Syncs vertical offset with its paired lane.
    """
    
    def __init__(
        self,
        track_id: str,
        width_px: int = TRACK_WIDTH_PX,
        height_px: int = CORE_BOX_HEIGHT_PX,
        color: str = "#E0E7FF",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.track_id = track_id
        self.width_px = width_px
        self.height_px = height_px
        self.color = color
        self._current_vertical_offset_px = 0.0
        
        # Fixed width; height expands with spacers
        self.setFixedWidth(width_px)
        min_height = height_px + 2 * INITIAL_SPACER_HEIGHT_PX
        self.setMinimumHeight(min_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        # Main container with vertical spacers (same pattern as lane)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top spacer
        self._top_spacer = QSpacerItem(0, INITIAL_SPACER_HEIGHT_PX, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(self._top_spacer)
        
        # Content area (colored rectangle)
        self._content = QFrame()
        self._content.setFixedWidth(width_px)
        self._content.setFixedHeight(height_px)
        self._content.setStyleSheet(f"QFrame {{ background-color: {color}; border: 1px solid #CBD5E1; }}")
        main_layout.addWidget(self._content)
        
        # Bottom spacer
        self._bottom_spacer = QSpacerItem(0, INITIAL_SPACER_HEIGHT_PX, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(self._bottom_spacer)
        
        self._main_layout = main_layout
    
    def set_vertical_offset(self, offset_px: float) -> None:
        """Move track vertically to match its paired lane.
        
        Args:
            offset_px: Vertical offset in pixels (positive = down, negative = up).
        """
        clamped_offset = max(-MAX_DRAG_OFFSET_PX, min(MAX_DRAG_OFFSET_PX, float(offset_px)))
        self._current_vertical_offset_px = clamped_offset
        
        # Keep minimum spacer height so content stays visible
        MIN_VISIBLE_HEIGHT = 10
        top_height = max(MIN_VISIBLE_HEIGHT, INITIAL_SPACER_HEIGHT_PX + int(clamped_offset))
        bottom_height = max(MIN_VISIBLE_HEIGHT, INITIAL_SPACER_HEIGHT_PX - int(clamped_offset))
        
        self._top_spacer.changeSize(0, top_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self._bottom_spacer.changeSize(0, bottom_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self._main_layout.invalidate()
        self._main_layout.activate()
        self.update()
    
    def set_content_height(self, height_px: int) -> None:
        """Update the colored rectangle's height to match a paired lane.
        
        Args:
            height_px: New height for the colored content rectangle.
        """
        print(f"[SET_CONTENT_HEIGHT] {self.track_id}: old={self.height_px}, new={height_px}")
        self.height_px = height_px
        self._content.setFixedHeight(height_px)
        # Update minimum container height to match
        min_height = height_px + 2 * INITIAL_SPACER_HEIGHT_PX
        self.setMinimumHeight(min_height)
        print(f"[SET_CONTENT_HEIGHT] {self.track_id}: _content.height set to {height_px}, widget min_height={min_height}")
        self.update()
    
    def get_vertical_offset_px(self) -> float:
        """Return current vertical offset in pixels."""
        return self._current_vertical_offset_px


class FenceDiagramPanel(QWidget):
    """Fence diagram panel with draggable core lanes and data tracks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fenceDiagramPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#fenceDiagramPanel { background-color: white; }")
        
        self._lanes: dict[str, _DraggableLaneBox] = {}
        self._tracks: dict[str, _DataTrackPlaceholder] = {}  # Track widgets keyed by track_id
        
        # Signals for presenter (logging/debugging while developing)
        from PySide6.QtCore import Signal as QtSignal
        
        # Note: These would normally be class-level, but for now we're adding them dynamically
        # so the view code is ready for presenter wiring
        self.coreSelected = QtSignal(str, str)  # (lane_id, core_id) — when user selects core for lane
        self.trackDataRequested = QtSignal(str, str, str)  # (track_id, core_id, axis) — when track data needed
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Ribbon toolbar at the top (ready for buttons, empty for now)
        self._ribbon = QFrame()
        self._ribbon.setFixedHeight(40)
        self._ribbon.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0; }"
        )
        self._ribbon_layout = QHBoxLayout(self._ribbon)
        self._ribbon_layout.setContentsMargins(12, 0, 12, 0)
        self._ribbon_layout.setSpacing(8)
        # Stretch to absorb empty space (buttons will be added here later)
        self._ribbon_layout.addStretch()
        main_layout.addWidget(self._ribbon)

        # Scroll area for lanes
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        
        # Lanes container — holds ruler + actual lane widgets in horizontal layout
        self._center_widget = QWidget()
        self._center_widget.setStyleSheet("background-color: white;")
        # Prevent container from expanding to fill scroll area height—let it size to content
        self._center_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._center_layout = QHBoxLayout(self._center_widget)
        self._center_layout.setContentsMargins(0, CENTER_LAYOUT_PADDING_PX, 20, CENTER_LAYOUT_PADDING_PX)  # Left padding removed for ruler, top/right/bottom
        self._center_layout.setSpacing(LANE_SPACING_PX)  # Inter-column spacing
        
        # Offset ruler on the left (shows ±mm offsets)
        self._offset_ruler = OffsetRulerColumn(scale_provider=lambda: 0.1)  # Default scale, will be updated by presenter
        self._offset_ruler.setFixedWidth(60)  # Fixed width for ruler
        self._offset_ruler.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)  # Expand vertically
        self._offset_ruler.setStyleSheet("QFrame { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }")
        self._center_layout.addWidget(self._offset_ruler, stretch=0)  # Don't use AlignTop—let it expand
        
        # Container for lanes inside scroll (so ruler scrolls with lanes vertically)
        self._lanes_container = QWidget()
        self._lanes_container.setStyleSheet("background-color: white;")
        self._lanes_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._lanes_layout = QHBoxLayout(self._lanes_container)
        self._lanes_layout.setContentsMargins(LEFT_LANE_PADDING_PX, 0, 0, 0)  # Left padding for lanes
        self._lanes_layout.setSpacing(LANE_SPACING_PX)
        
        self._center_layout.addWidget(self._lanes_container, stretch=1)
        
        self._scroll_area.setWidget(self._center_widget)
        main_layout.addWidget(self._scroll_area)
        
        # Connect scroll area signals to update ruler anchor when viewport changes
        # This ensures the ruler's zero point follows the reference core as user scrolls
        self._scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._scroll_area.horizontalScrollBar().valueChanged.connect(self._on_scroll)
    
    def set_lanes(self, lanes: list[LaneConfig]) -> None:
        """Update the panel with lane configuration and create paired data tracks.
        
        Creates:
        - All draggable lanes first
        - All data tracks after (each synced to a specific lane via explicit mapping)
        - One correlation track (synced to reference lane)
        
        Args:
            lanes: List of LaneConfig objects defining lanes and offsets.
        """
        # Clear existing lanes completely
        for lane_widget in self._lanes.values():
            self._lanes_layout.removeWidget(lane_widget)
            lane_widget.deleteLater()
        self._lanes.clear()
        
        # Clear existing tracks
        for track_widget in self._tracks.values():
            self._lanes_layout.removeWidget(track_widget)
            track_widget.deleteLater()
        self._tracks.clear()
        
        # Clear sync mappings
        self._track_to_lane = {}  # Map: track_id → lane_id for explicit sync
        
        # Clear all layout items (including old stretches)
        while self._lanes_layout.count() > 0:
            item = self._lanes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add left stretch to center lanes horizontally
        self._lanes_layout.addStretch()
        
        # ==== PHASE 1: Add all lanes first ====
        for i, lane_cfg in enumerate(lanes):
            # Create lane
            lane_widget = _DraggableLaneBox(lane_cfg.id, lane_cfg.width_px, lane_cfg.height_px)
            # Reference lane (lane_0) shows "Reference", others show offset with appropriate precision
            if lane_cfg.id == "lane_0":
                lane_widget.set_offset_text("Reference")
            else:
                lane_widget.set_offset_text(f"{lane_cfg.relative_offset_mm:+.1f} mm")
            if lane_cfg.core_name:
                lane_widget.set_core_name(lane_cfg.core_name)
            self._lanes[lane_cfg.id] = lane_widget
            
            # Hook lane drag signals to update ruler and track offsets
            try:
                lane_widget.offsetChanged.disconnect()
            except RuntimeError:
                pass  # Fresh widget, no prior connections
            lane_widget.offsetChanged.connect(self._on_lane_drag)
            lane_widget.dragFinished.connect(self._on_lane_drag_finished)
            
            # Add lane to layout
            self._lanes_layout.addWidget(lane_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
        
        # ==== PHASE 2: Add all tracks after (with explicit lane → track mapping) ====
        for i, lane_cfg in enumerate(lanes):
            track_id = f"track_{i}"
            lane_id = lane_cfg.id
            
            # Use different colors for visual distinction
            if i == 0:
                color = "#E0E7FF"  # Light blue for ref core track
            elif i == 1:
                color = "#FCE7F3"  # Light pink for comp core track
            else:
                color = "#F3E8FF"  # Light purple for other tracks
            
            track_widget = _DataTrackPlaceholder(track_id, TRACK_WIDTH_PX, lane_cfg.height_px, color)
            self._tracks[track_id] = track_widget
            
            # Explicit mapping: this track syncs with this lane
            self._track_to_lane[track_id] = lane_id
            
            self._lanes_layout.addWidget(track_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
        
        # ==== PHASE 3: Add correlation track (synced to reference lane) ====
        if "lane_0" in self._lanes:
            corr_track_id = "track_correlation"
            corr_track = _DataTrackPlaceholder(
                corr_track_id, 
                TRACK_WIDTH_PX, 
                self._lanes["lane_0"].height_px,
                "#FEE2E2"  # Light red for correlation
            )
            self._tracks[corr_track_id] = corr_track
            
            # Explicit mapping: correlation track syncs with reference lane
            self._track_to_lane[corr_track_id] = "lane_0"
            
            self._lanes_layout.addWidget(corr_track, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Add right stretch to center lanes horizontally
        self._lanes_layout.addStretch()
        
        # Defer height sync until after layout is computed
        # This ensures lane widgets have been rendered and their total heights are known
        QTimer.singleShot(0, self._sync_track_heights_to_lanes)
        QTimer.singleShot(0, self._sync_ruler_and_tracks)
    
    def _sync_track_heights_to_lanes(self) -> None:
        """Sync each track's content height to match its paired lane's content height.
        
        Called after layout is computed or when a core is dropped.
        """
        for track_id, lane_id in self._track_to_lane.items():
            if track_id in self._tracks and lane_id in self._lanes:
                lane_widget = self._lanes[lane_id]
                track_widget = self._tracks[track_id]
                lane_content_height = lane_widget.height_px
                track_widget.set_content_height(lane_content_height)
    
    def _update_lane_height(self, lane_id: str, new_height_px: int) -> None:
        """Update a lane's content height when a new core is dropped.
        
        Adjusts for offset label and spacers so track aligns perfectly with core.
        
        Args:
            lane_id: The lane to update.
            new_height_px: The new total rendered lane widget height.
        """
        if lane_id in self._lanes:
            lane_widget = self._lanes[lane_id]
            # Track's total height = lane height - (label height + spacing)
            # Because lane includes label+spacing but track doesn't
            track_total_height = new_height_px - (OFFSET_LABEL_HEIGHT_PX + CORE_LABEL_SPACING_PX)
            
            # Track content height = track_total_height - (top_spacer + bottom_spacer)
            track_content_height = track_total_height - (2 * INITIAL_SPACER_HEIGHT_PX)
            
            lane_widget.height_px = track_content_height
    
    def _on_scroll(self) -> None:
        """Handle scroll area scroll events — update ruler anchor to stay with reference core."""
        self._sync_ruler_and_tracks()
    
    def _on_lane_drag(self, delta_px: float) -> None:
        """Handle lane drag events — update ruler and track positions in real-time."""
        if not self._lanes:
            return
        
        # Update track offsets to match their paired lanes
        for i, (lane_id, lane_widget) in enumerate(self._lanes.items()):
            track_id = f"track_{i}"
            if track_id in self._tracks:
                offset = lane_widget.get_vertical_offset_px()
                self._tracks[track_id].set_vertical_offset(offset)
        
        # Keep ruler anchor in sync
        self._sync_ruler_and_tracks()
    
    def _on_lane_drag_finished(self) -> None:
        """Handle end of lane drag — emit signal for presenter to compute new correlation data."""
        # This is where presenter would recalculate correlation based on new offset
        # For now, just log that drag finished
        if "lane_0" in self._lanes and "lane_1" in self._lanes:
            ref_offset = self._lanes["lane_0"].get_vertical_offset_px()
            comp_offset = self._lanes["lane_1"].get_vertical_offset_px()
            # Could emit signal here: self.offsetsFinalized.emit(ref_offset, comp_offset)
    
    def _sync_ruler_and_tracks(self) -> None:
        """Update ruler anchor, data tracks, and correlation track positions.
        
        Syncs each track to its paired lane (via explicit mapping in self._track_to_lane),
        keeps the ruler's zero point synced with the reference lane, and keeps the 
        correlation track synced with the reference lane.
        """
        if "lane_0" not in self._lanes:
            return
        
        ref_lane = self._lanes["lane_0"]
        if not ref_lane.parent():
            return
        
        try:
            # Sync each data track to its mapped lane using explicit relationships
            for track_id, lane_id in self._track_to_lane.items():
                if track_id in self._tracks and lane_id in self._lanes:
                    lane_widget = self._lanes[lane_id]
                    track_widget = self._tracks[track_id]
                    offset = lane_widget.get_vertical_offset_px()
                    track_widget.set_vertical_offset(offset)
            
            # Map reference lane's top-left to _center_widget coordinates
            from PySide6.QtCore import QPoint
            ref_lane_pos_in_center = ref_lane.mapTo(self._center_widget, QPoint(0, 0))
            
            # Map ruler's top-left to _center_widget coordinates
            ruler_pos_in_center = self._offset_ruler.mapTo(self._center_widget, QPoint(0, 0))
            
            # Get the reference lane's current visual offset (from set_vertical_offset)
            # The core is visually positioned at: lane_top + initial_spacer_height + offset
            ref_offset_px = ref_lane.get_vertical_offset_px()
            
            # Core visual Y in center_widget coordinates:
            # = lane_top + initial_spacer_height + offset
            core_visual_y = ref_lane_pos_in_center.y() + ref_lane._initial_spacer_height + ref_offset_px
            
            # Anchor Y in ruler's coordinate space:
            # = (core_visual_y - ruler_top)
            anchor_y = core_visual_y - ruler_pos_in_center.y()
            
            # Clamp ruler anchor to stay within scroll viewport bounds
            # CRITICAL: When core hits max drag boundary, ruler stops moving too
            try:
                scroll_viewport_height = self._scroll_area.viewport().height()
                # Anchor stays within visible viewport bounds
                # Don't allow overflow—ruler should stop when core stops
                min_anchor = 0
                max_anchor = scroll_viewport_height
                anchor_y = max(min_anchor, min(max_anchor, anchor_y))
            except Exception:
                # If can't calculate bounds, use generous fallback
                pass
            
            self._offset_ruler.set_anchor_y(int(anchor_y))
        except Exception as e:
            # If mapping fails (during early init), skip for now
            pass
    
    def update_lane_offset_label(self, lane_id: str, offset_text: str) -> None:
        """Update the offset label for a specific lane."""
        if lane_id in self._lanes:
            self._lanes[lane_id].set_offset_text(offset_text)
    
    def set_scale_provider(self, scale_provider) -> None:
        """Set the scale provider for the offset ruler.
        
        Args:
            scale_provider: Callable that returns mm_per_px
        """
        self._offset_ruler.set_scale_provider(scale_provider)
    
    def get_lane_widget(self, lane_id: str) -> _DraggableLaneBox | None:
        """Get the lane widget for signal wiring in presenter."""
        return self._lanes.get(lane_id)





