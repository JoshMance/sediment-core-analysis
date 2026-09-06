"""Excel export for Core Studio row-wise measurements."""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from src.application.services.compute_channels import ChannelProfiles
from src.domain.entities.core_entity import CoreEntity


def export_core(path: Path, core: CoreEntity, channels: ChannelProfiles) -> None:
    """Write a Core Studio workbook with one row per displayed image row.

    The profiles are already oriented to match Core Studio. ``depth_mm`` is
    included only for calibrated cores; uncalibrated workbooks retain their
    image-row coordinate without inventing physical depth.
    """
    workbook = Workbook()
    data = workbook.active
    data.title = "Core data"

    headers = ["image_row_px"]
    if core.mm_per_px > 0:
        headers.append("depth_mm")
    headers.extend(["R_mean", "G_mean", "B_mean", "L_star", "a_star", "b_star"])
    data.append(headers)
    for cell in data[1]:
        cell.font = Font(bold=True)

    for row_index in range(len(channels.r)):
        row: list[float | int] = [row_index]
        if core.mm_per_px > 0:
            row.append(row_index * core.mm_per_px)
        row.extend([
            float(channels.r[row_index]),
            float(channels.g[row_index]),
            float(channels.b[row_index]),
            float(channels.l_star[row_index]),
            float(channels.a_star[row_index]),
            float(channels.b_star[row_index]),
        ])
        data.append(row)

    data.freeze_panes = "A2"
    for column in data.columns:
        width = max(len(str(cell.value or "")) for cell in column) + 2
        data.column_dimensions[column[0].column_letter].width = min(width, 20)

    workbook.save(path)