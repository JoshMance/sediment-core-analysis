"""Stratigraphy panel for visualization and interaction."""

from .widget import StratigraphyPanel
from .columns import (
    BaseColumn, ImageColumn, DataColumn, RulerColumn, LayerColumn, LayerStyle,
    StratRow, rows_from_layers,
    HEADER_HEIGHT, TITLE_HEIGHT, HEADER_GAP, DOMAIN_PADDING,
)

__all__ = [
    'StratigraphyPanel', 
    'BaseColumn',
    'ImageColumn',
    'DataColumn',
    'RulerColumn',
    'LayerColumn',
    'LayerStyle',
    'StratRow',
    'rows_from_layers',
]
