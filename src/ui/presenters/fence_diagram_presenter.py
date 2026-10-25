"""FenceDiagramPresenter — manages fence diagram state and drag-to-offset logic."""
from __future__ import annotations

import logging
import math
import warnings
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.fence_diagram_panel import FenceDiagramPanel, LaneConfig

logger = logging.getLogger(__name__)

# Suppress Qt warning about disconnecting signals that don't have connections
# (this happens on first call when lane widgets are freshly created)
warnings.filterwarnings("ignore", message=".*Failed to disconnect.*from signal.*")

# UI Constants
CORE_BOX_WIDTH_PX = 130
CORE_BOX_HEIGHT_PX = 420
MAX_DRAG_OFFSET_PX = 2000  # Safety clamp: prevent runaway scrolling from single drag
DEFAULT_MM_PER_PX = 0.1    # Fallback calibration if no reference core
DEFAULT_OFFSET_PRECISION = 1  # Default decimal places for offset display


class FenceDiagramPresenter(QObject):
    """Manages fence diagram: lanes, offsets, drag interactions.
    
    Temporary state model (for MVP). Will migrate to domain entity later.
    """

    def __init__(
        self,
        view: FenceDiagramPanel,
        store: Store,
        controller: AppController,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        
        # Temporary state: lanes with both absolute and relative offsets (MVP only)
        self._lanes: dict[str, LaneConfig] = {
            "lane_0": LaneConfig(id="lane_0", core_id=None, core_name="Reference", absolute_offset_mm=0.0, relative_offset_mm=0.0, width_px=CORE_BOX_WIDTH_PX, height_px=CORE_BOX_HEIGHT_PX),
            "lane_1": LaneConfig(id="lane_1", core_id=None, core_name="—", absolute_offset_mm=0.0, relative_offset_mm=0.0, width_px=CORE_BOX_WIDTH_PX, height_px=CORE_BOX_HEIGHT_PX),
        }
        self._reference_lane_id = "lane_0"  # First lane is reference
        
        # Drag tracking: separate active lane ID from starting offsets (prevents dual-dict confusion)
        self._drag_active_lane: str | None = None  # Which lane is currently being dragged
        self._drag_start_offsets: dict[str, float] = {}  # Starting absolute offsets for all lanes at drag start
        
        # Initialize view with lanes
        self._update_view()
    
    def _update_view(self) -> None:
        """Update view with current lanes."""
        lanes_list = list(self._lanes.values())
        self._view.set_lanes(lanes_list)
        
        # Wire scale provider to offset ruler for live mm_per_px updates
        self._view.set_scale_provider(self._get_mm_per_px)
        
        # Wire drag signals and drop signals for newly created lane widgets
        # IMPORTANT: Disconnect old signals to prevent double-firing if _update_view called multiple times
        for lane_id, lane_widget in self._view._lanes.items():
            # Disconnect all existing connections for this lane (suppress warnings if none exist)
            try:
                lane_widget.offsetChanged.disconnect()
            except RuntimeError:
                pass  # No previous connections, this is expected on first call
            try:
                lane_widget.dragFinished.disconnect()
            except RuntimeError:
                pass
            try:
                lane_widget.coreDropped.disconnect()
            except RuntimeError:
                pass
            
            # Connect fresh signals
            lane_widget.offsetChanged.connect(lambda delta_px, lid=lane_id: self._on_lane_drag(lid, delta_px))
            lane_widget.dragFinished.connect(lambda lid=lane_id: self._on_lane_drag_finished(lid))
            lane_widget.coreDropped.connect(lambda core_id, lid=lane_id: self._on_core_dropped_on_lane(lid, core_id))
    
    def _on_lane_drag(self, lane_id: str, delta_px: float) -> None:
        """Handle lane drag event (offset in pixels).
        
        Any lane can be dragged, including the reference core.
        Updates absolute_offset_mm, then recalculates all relative_offset_mm.
        
        Args:
            lane_id: Which lane is being dragged.
            delta_px: Pixel offset from drag start.
        """
        # Convert px to mm using scale from reference core
        ref_lane = self._lanes.get(self._reference_lane_id)
        if not ref_lane or not ref_lane.core_id:
            logger.warning(f"Drag on lane {lane_id}: no reference core to calibrate scale")
            return  # No reference core, can't calculate scale
        
        mm_per_px = self._store.get_field(ref_lane.core_id, "mm_per_px")
        if not mm_per_px or mm_per_px <= 0:
            mm_per_px = DEFAULT_MM_PER_PX
            logger.warning(f"Reference core {ref_lane.core_id} has invalid mm_per_px; using fallback {DEFAULT_MM_PER_PX}")
        
        delta_mm = delta_px * mm_per_px
        
        # Calculate viewport boundary FIRST - this is the master constraint
        max_drag_px = self._calculate_max_drag_offset()
        max_offset_mm = max_drag_px * mm_per_px  # Convert to mm using same scale
        
        # Store initial absolute offsets if this is first drag event for this lane
        if self._drag_active_lane != lane_id:
            self._drag_active_lane = lane_id
            self._drag_start_offsets.clear()
            for lid in self._lanes:
                self._drag_start_offsets[lid] = self._lanes[lid].absolute_offset_mm
        
        # Update the dragged lane's absolute position, clamped to viewport boundary
        # CRITICAL: Use SAME boundary for absolute as we do for visual
        original_absolute = self._drag_start_offsets.get(lane_id, 0.0)
        new_absolute = original_absolute + delta_mm
        self._lanes[lane_id].absolute_offset_mm = max(-max_offset_mm, min(max_offset_mm, new_absolute))
        
        # Recalculate all relative offsets: relative = absolute - reference_absolute
        ref_absolute = self._lanes[self._reference_lane_id].absolute_offset_mm
        for lid in self._lanes:
            self._lanes[lid].relative_offset_mm = self._lanes[lid].absolute_offset_mm - ref_absolute
        
        # Update all lane visuals
        for lid in self._lanes:
            # CRITICAL: Visual position uses ABSOLUTE offset (where core actually is)
            absolute_mm = self._lanes[lid].absolute_offset_mm
            absolute_px = absolute_mm / mm_per_px
            lane_widget = self._view.get_lane_widget(lid)
            if lane_widget:
                lane_widget.set_vertical_offset(absolute_px, max_offset_px=max_drag_px)
            
            # Label uses RELATIVE offset (what user sees: position relative to reference)
            relative_mm = self._lanes[lid].relative_offset_mm
            offset_text = self._format_offset(relative_mm)
            self._view.update_lane_offset_label(lid, offset_text)
        
        # Sync ruler anchor and tracks to follow the reference core during drag
        self._view._sync_ruler_and_tracks()
    
    
    def _on_lane_drag_finished(self, lane_id: str) -> None:
        """Handle end of drag (finalize offset).
        
        TODO: Persist offsets to domain entity / Store via AppController.
        For now, offset persists locally in presenter only.
        """
        if self._drag_active_lane == lane_id:
            self._drag_active_lane = None
            self._drag_start_offsets.clear()
    
    def _calculate_max_drag_offset(self) -> float:
        """Calculate the maximum drag offset to keep core within scroll viewport.
        
        Returns:
            Maximum pixel offset the core can be dragged (before hitting scroll area edge).
        """
        try:
            scroll_area = self._view._scroll_area
            viewport_height = scroll_area.viewport().height()
            
            # Allow cores to move across 3x the viewport height
            max_offset = viewport_height * 3
            
            # Return positive value; clamping will apply both directions
            return max(max_offset, 100)  # Minimum 100px to avoid over-constraining
        except Exception:
            # Fallback if viewport not ready
            return MAX_DRAG_OFFSET_PX
    
    
    def _on_core_dropped_on_lane(self, lane_id: str, core_id: str) -> None:
        """Handle a core dropped onto a specific lane.
        
        Args:
            lane_id: The lane that received the drop.
            core_id: The core entity ID that was dropped.
        """
        # Get core entity from store
        core_entity = self._store.get(core_id)
        if core_entity is None:
            return
        
        core_name = getattr(core_entity, "name", core_id)
        core_mm_per_px = getattr(core_entity, "mm_per_px", 0.0)
        
        # Assign core to this lane
        if lane_id in self._lanes:
            self._lanes[lane_id].core_id = core_id
            self._lanes[lane_id].core_name = core_name
            
            # Update view to display the core name
            lane_widget = self._view.get_lane_widget(lane_id)
            if lane_widget:
                lane_widget.set_core_name(core_name)
                
                # Fetch and display the core image
                resolved = self._controller.get_resolved_data(core_id)
                if resolved is not None and isinstance(resolved, np.ndarray):
                    # Scale image based on calibration (mm_per_px)
                    # Get current reference calibration dynamically
                    reference_mm_per_px = self._get_mm_per_px()
                    pixmap = self._ndarray_to_pixmap(
                        resolved,
                        core_mm_per_px=core_mm_per_px,
                        reference_mm_per_px=reference_mm_per_px
                    )
                    lane_widget.set_core_image(pixmap)
                    
                    # After core image is set, force layout recalculation and wait for it to settle
                    def sync_after_layout():
                        # Force immediate layout recalculation
                        lane_widget.layout().invalidate()
                        lane_widget.layout().activate()
                        lane_widget.updateGeometry()
                        
                        actual_lane_height = lane_widget.height()
                        self._view._update_lane_height(lane_id, actual_lane_height)
                        self._view._sync_track_heights_to_lanes()
                    
                    # Defer with longer delay to ensure layout fully settles
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(100, sync_after_layout)
    
    @staticmethod
    def _ndarray_to_pixmap(
        data: np.ndarray,
        core_mm_per_px: float = 0.0,
        reference_mm_per_px: float | None = None,
    ) -> QPixmap:
        """Convert numpy ndarray (RGB888) to QPixmap, preserving aspect ratio and scale.
        
        If reference_mm_per_px is provided and core_mm_per_px > 0, scale the image
        so that all cores display at their true relative depths.
        
        Args:
            data: RGB888 numpy array (H, W, 3)
            core_mm_per_px: This core's calibration (mm per pixel)
            reference_mm_per_px: Reference scale (from first dropped core)
        """
        from PySide6.QtCore import Qt
        
        h, w = data.shape[:2]
        arr = np.ascontiguousarray(data)
        qimage = QImage(arr.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        
        # Apply scale factor if we have calibration data
        if reference_mm_per_px and reference_mm_per_px > 0 and core_mm_per_px > 0:
            # Scale factor: how much to enlarge/shrink this core relative to reference
            scale_factor = core_mm_per_px / reference_mm_per_px
            scaled_width = int(w * scale_factor)
            scaled_height = int(h * scale_factor)
            pixmap = pixmap.scaled(
                scaled_width, scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        return pixmap
    
    def _get_mm_per_px(self) -> float:
        """Get current mm_per_px calibration for scale provider.
        
        Returns the reference core's scale, or fallback default.
        Used by ruler and other UI elements to convert mm ↔ px.
        """
        ref_lane = self._lanes.get(self._reference_lane_id)
        if not ref_lane or not ref_lane.core_id:
            return DEFAULT_MM_PER_PX
        
        mm_per_px = self._store.get_field(ref_lane.core_id, "mm_per_px")
        if not mm_per_px or mm_per_px <= 0:
            return DEFAULT_MM_PER_PX
        
        return mm_per_px
    
    def _get_offset_precision(self) -> int:
        """Calculate decimal places for offset display based on reference core scale.
        
        Rule: Precision = number of decimal places in mm_per_px
        Example: If 1px = 0.05mm, show 2 decimals; If 1px = 0.1mm, show 1 decimal.
        """
        ref_lane = self._lanes.get(self._reference_lane_id)
        if not ref_lane or not ref_lane.core_id:
            return DEFAULT_OFFSET_PRECISION
        
        mm_per_px = self._store.get_field(ref_lane.core_id, "mm_per_px")
        if not mm_per_px or mm_per_px <= 0:
            return DEFAULT_OFFSET_PRECISION
        
        # Calculate log10 to find order of magnitude
        decimals = -int(math.floor(math.log10(abs(mm_per_px))))
        return max(0, decimals)
    
    def _format_offset(self, offset_mm: float) -> str:
        """Format offset with sign and correct precision.
        
        Returns:
            String like "+2.5 mm", "−15.0 mm", "0.0 mm"
        """
        precision = self._get_offset_precision()
        formatted = f"{offset_mm:.{precision}f}"
        
        # Always show sign
        if offset_mm >= 0:
            return f"+{formatted} mm"
        else:
            return f"{formatted} mm"  # Already has − from formatting
