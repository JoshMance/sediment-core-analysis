"""Correlation service for fence diagram core alignment.

Handles resampling cores to a common depth grid and computing Pearson
correlation curves that show alignment quality at each depth offset.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def resample(
    ref_data: np.ndarray,
    comp_data: np.ndarray,
    ref_mm_per_px: float,
    comp_mm_per_px: float,
) -> np.ndarray:
    """Resample comparison data to reference data's depth grid.
    
    Args:
        ref_data: Reference data array, shape (N,) or (N, C)
        comp_data: Comparison data array, shape (M,) or (M, C)
        ref_mm_per_px: Reference depth scale (mm per pixel)
        comp_mm_per_px: Comparison depth scale (mm per pixel)
    
    Returns:
        Resampled comparison data on reference grid, same shape as ref_data
    
    Raises:
        ValueError: If data is invalid or scale is non-positive.
    """
    if ref_data.size == 0 or comp_data.size == 0:
        raise ValueError("Both data arrays must be non-empty")
    
    if ref_mm_per_px <= 0 or comp_mm_per_px <= 0:
        raise ValueError("mm_per_px values must be positive")
    
    # Handle 1D and multi-channel data
    ref_height = ref_data.shape[0]
    comp_height = comp_data.shape[0]
    is_1d = len(ref_data.shape) == 1
    
    ref_grid = np.arange(ref_height) * ref_mm_per_px
    comp_grid = np.arange(comp_height) * comp_mm_per_px
    
    # Resample comparison data to reference grid
    if is_1d:
        # 1D data: simple interpolation
        resampled = np.interp(ref_grid, comp_grid, comp_data, left=np.nan, right=np.nan)
    else:
        # Multi-channel data: interpolate each channel
        channels = comp_data.shape[1]
        resampled = np.full((ref_height, channels), np.nan)
        for ch in range(channels):
            resampled[:, ch] = np.interp(ref_grid, comp_grid, comp_data[:, ch], left=np.nan, right=np.nan)
    
    return resampled


def correlate(
    ref_values: np.ndarray,
    comp_values: np.ndarray,
    depth_step_mm: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Pearson correlation curve fixed to reference core depth.
    
    For each possible offset of the comparison core, calculate r-value
    at each depth in the reference core's coordinate space. The curve
    has 2N-1 points, where N is the reference core's depth resolution.
    
    Args:
        ref_values: Reference data (1D or multi-channel, shape (N,) or (N, C))
        comp_values: Resampled comparison data (same grid as ref_values)
        depth_step_mm: Grid resolution in mm
    
    Returns:
        (offsets_mm, r_values)
            offsets_mm: Array of offset values (mm), from -(n-1) to +(n-1)
            r_values: Corresponding Pearson r at each offset (2n-1 values)
    """
    # Handle multi-channel: flatten to 1D or average
    if len(ref_values.shape) > 1:
        ref_flat = ref_values.mean(axis=1) if ref_values.shape[1] > 0 else ref_values[:, 0]
    else:
        ref_flat = ref_values
    
    if len(comp_values.shape) > 1:
        comp_flat = comp_values.mean(axis=1) if comp_values.shape[1] > 0 else comp_values[:, 0]
    else:
        comp_flat = comp_values
    
    n_ref = len(ref_flat)
    n_comp = len(comp_flat)
    
    # Offset range: negative = comp shifted up, positive = comp shifted down
    max_offset_samples = n_ref - 1
    offsets_samples = np.arange(-max_offset_samples, max_offset_samples + 1)
    offsets_mm = offsets_samples * depth_step_mm
    
    r_values = []
    
    for offset_samples in offsets_samples:
        # Compute overlapping region based on offset
        if offset_samples >= 0:
            # Comparison core shifted down (positive offset)
            ref_start = 0
            ref_end = n_ref - offset_samples if offset_samples < n_ref else 0
            comp_start = offset_samples
            comp_end = n_comp
        else:
            # Comparison core shifted up (negative offset)
            ref_start = -offset_samples
            ref_end = n_ref
            comp_start = 0
            comp_end = n_comp + offset_samples if -offset_samples < n_comp else 0
        
        # Check for valid overlap
        if ref_end <= ref_start or comp_end <= comp_start:
            r_values.append(np.nan)
            continue
        
        # Extract overlapping segments
        ref_segment = ref_flat[ref_start:ref_end]
        comp_segment = comp_flat[comp_start:comp_end]
        
        # Need at least 2 points to compute Pearson correlation
        if len(ref_segment) < 2 or len(comp_segment) < 2:
            r_values.append(np.nan)
            continue
        
        # Skip if all values are NaN
        if np.isnan(ref_segment).all() or np.isnan(comp_segment).all():
            r_values.append(np.nan)
            continue
        
        # Compute Pearson correlation coefficient
        try:
            r, _ = stats.pearsonr(ref_segment, comp_segment)
            r_values.append(r)
        except Exception:
            # Handle edge cases (e.g., constant value)
            r_values.append(np.nan)
    
    return offsets_mm, np.array(r_values)


def prepare(
    ref_data: np.ndarray,
    comp_data: np.ndarray,
    ref_mm_per_px: float,
    comp_mm_per_px: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Resample and correlate for given data arrays.
    
    Orchestrator: resamples comparison data to reference grid,
    computes correlation curve.
    
    Args:
        ref_data: Reference data array (defines depth grid)
        comp_data: Comparison data array
        ref_mm_per_px: Reference depth scale (mm per pixel)
        comp_mm_per_px: Comparison depth scale (mm per pixel)
    
    Returns:
        (ref_data, resampled_comp_data, offsets_mm, r_values)
            ref_data: Original reference data
            resampled_comp_data: Comparison data resampled to ref grid
            offsets_mm: Offset values (mm) for correlation curve
            r_values: Pearson r at each offset (2n-1 values)
    
    Raises:
        ValueError: If data is invalid or scale is non-positive.
    """
    # Resample comparison data to reference grid
    resampled_comp = resample(ref_data, comp_data, ref_mm_per_px, comp_mm_per_px)
    
    # Compute correlation curve
    offsets_mm, r_values = correlate(ref_data, resampled_comp, ref_mm_per_px)
    
    return ref_data, resampled_comp, offsets_mm, r_values



def resample(
    ref_data: np.ndarray,
    comp_data: np.ndarray,
    ref_mm_per_px: float,
    comp_mm_per_px: float,
) -> np.ndarray:
    """Resample comparison data to reference data's depth grid.
    
    Args:
        ref_data: Reference data array, shape (N,) or (N, C)
        comp_data: Comparison data array, shape (M,) or (M, C)
        ref_mm_per_px: Reference depth scale (mm per pixel)
        comp_mm_per_px: Comparison depth scale (mm per pixel)
    
    Returns:
        Resampled comparison data on reference grid, same shape as ref_data
    
    Raises:
        ValueError: If data is invalid or scale is non-positive.
    """
    if ref_data.size == 0 or comp_data.size == 0:
        raise ValueError("Both data arrays must be non-empty")
    
    if ref_mm_per_px <= 0 or comp_mm_per_px <= 0:
        raise ValueError("mm_per_px values must be positive")
    
    # Handle 1D and multi-channel data
    ref_height = ref_data.shape[0]
    comp_height = comp_data.shape[0]
    is_1d = len(ref_data.shape) == 1
    
    # Create depth grids
    ref_depth_max = ref_height * ref_mm_per_px
    comp_depth_max = comp_height * comp_mm_per_px
    
    ref_grid = np.arange(ref_height) * ref_mm_per_px
    comp_grid = np.arange(comp_height) * comp_mm_per_px
    
    # Resample comparison data to reference grid
    if is_1d:
        # 1D data: simple interpolation
        resampled = np.interp(ref_grid, comp_grid, comp_data, left=np.nan, right=np.nan)
    else:
        # Multi-channel data: interpolate each channel
        channels = comp_data.shape[1]
        resampled = np.full((ref_height, channels), np.nan)
        for ch in range(channels):
            resampled[:, ch] = np.interp(ref_grid, comp_grid, comp_data[:, ch], left=np.nan, right=np.nan)
    
    return resampled
    
    for core_id, core in [(ref_core_id, ref_core), (comp_core_id, comp_core)]:
        h, w, c = core.base_data.shape
        
        # Extract RGB channels (average across width to get depth profile)
        if c >= 3:
            r_profile = core.base_data[:, :, 0].astype(float).mean(axis=1)
            g_profile = core.base_data[:, :, 1].astype(float).mean(axis=1)
            b_profile = core.base_data[:, :, 2].astype(float).mean(axis=1)
            
            # Native depth grid for this core
            core_depth = np.arange(h) * core.mm_per_px
            
            # Resample to reference grid
            for axis, profile in [('R', r_profile), ('G', g_profile), ('B', b_profile)]:
                resampled = np.interp(ref_grid, core_depth, profile)
                result[(core_id, axis)] = resampled
    
    return result


def correlate(ref_values: np.ndarray, comp_values: np.ndarray, depth_step_mm: float) -> tuple:
    """Compute Pearson correlation curve fixed to reference core depth.
    
    For each possible offset of the comparison core, calculate r-value
    at each depth in the reference core's coordinate space. The curve
    has 2N-1 points, where N is the reference core's depth resolution.
    
    Args:
        ref_values: Resampled reference core data (aligned to grid)
        comp_values: Resampled comparison core data (same grid)
        depth_step_mm: Grid resolution in mm
    
    Returns:
        (offsets_mm, r_values)
            offsets_mm: Array of offset values (mm), from -(n-1) to +(n-1)
            r_values: Corresponding Pearson r at each offset (2n-1 values)
    """
    n_ref = len(ref_values)
    n_comp = len(comp_values)
    
    # Offset range: when comparison core is shifted relative to reference
    # Negative: comp_core top is above ref_core top
    # Positive: comp_core top is below ref_core top
    max_offset_samples = n_ref - 1
    offsets_samples = np.arange(-max_offset_samples, max_offset_samples + 1)
    offsets_mm = offsets_samples * depth_step_mm
    
    r_values = []
    
    for offset_samples in offsets_samples:
        # Compute overlapping region based on offset
        if offset_samples >= 0:
            # Comparison core shifted down (positive offset)
            ref_start = 0
            ref_end = n_ref - offset_samples
            comp_start = offset_samples
            comp_end = n_comp
        else:
            # Comparison core shifted up (negative offset)
            ref_start = -offset_samples
            ref_end = n_ref
            comp_start = 0
            comp_end = n_comp + offset_samples
        
        # Check for valid overlap
        if ref_end <= ref_start or comp_end <= comp_start:
            r_values.append(np.nan)
            continue
        
        # Extract overlapping segments
        ref_segment = ref_values[ref_start:ref_end]
        comp_segment = comp_values[comp_start:comp_end]
        
        # Need at least 2 points to compute Pearson correlation
        if len(ref_segment) < 2:
            r_values.append(np.nan)
            continue
        
        # Compute Pearson correlation coefficient
        try:
            r, _ = stats.pearsonr(ref_segment, comp_segment)
            r_values.append(r)
        except Exception:
            # Handle edge cases (e.g., constant value)
            r_values.append(np.nan)
    
    return offsets_mm, np.array(r_values)


def prepare(store: Store, ref_core_id: str, comp_core_id: str, axis: str) -> tuple:
    """Resample and correlate for a given axis.
    
    Orchestrator: derives reference grid, resamples comparison core to it,
    computes correlation curve.
    
    Args:
        store: The Store
        ref_core_id: Reference core ID (defines depth grid)
        comp_core_id: Comparison core ID
        axis: Data dimension to correlate ('R', 'G', 'B', etc.)
    
    Returns:
        (ref_values, comp_values, offsets_mm, r_values)
            ref_values: Resampled reference core data (1D array)
            comp_values: Resampled comparison core data (1D array)
            offsets_mm: Offset values (mm) for correlation curve
            r_values: Pearson r at each offset (2n-1 values)
    
    Raises:
        ValueError: If cores not found, axis unavailable, or data invalid.
    """
    # Resample both cores to reference grid
    resampled = resample(store, ref_core_id, comp_core_id)
    
    # Extract values for the given axis
    if (ref_core_id, axis) not in resampled:
        raise ValueError(f"Axis '{axis}' not available for reference core {ref_core_id}")
    if (comp_core_id, axis) not in resampled:
        raise ValueError(f"Axis '{axis}' not available for comparison core {comp_core_id}")
    
    ref_values = resampled[(ref_core_id, axis)]
    comp_values = resampled[(comp_core_id, axis)]
    
    # Get depth step from reference core
    ref_core = store.get(ref_core_id)
    depth_step_mm = ref_core.mm_per_px
    
    # Compute correlation curve
    offsets_mm, r_values = correlate(ref_values, comp_values, depth_step_mm)
    
    return ref_values, comp_values, offsets_mm, r_values
