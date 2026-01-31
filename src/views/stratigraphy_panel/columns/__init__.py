"""
Column definitions for stratigraphy panel.

Organized structure:
- base.py: BaseColumn + constants
- [name]_column.py: Concrete column implementations
"""

from .base import BaseColumn, HEADER_HEIGHT, TITLE_HEIGHT, HEADER_GAP, DOMAIN_PADDING
from .image_column import ImageColumn
from .data_column import DataColumn
from .ruler_column import RulerColumn
from .layer_column import LayerColumn, LayerStyle

__all__ = [
    'BaseColumn',
    'ImageColumn',
    'DataColumn',
    'RulerColumn',
    'LayerColumn',
    'LayerStyle',
    'HEADER_HEIGHT',
    'TITLE_HEIGHT',
    'DOMAIN_PADDING',
]
