"""
Column definitions for stratigraphy panel.

Organized structure:
- protocol.py: ColumnProtocol interface
- base.py: BaseColumn + constants
- [name]_column.py: Concrete column implementations
"""

from .protocol import ColumnProtocol
from .base import BaseColumn, HEADER_HEIGHT, TITLE_HEIGHT, DOMAIN_PADDING
from .image_column import ImageColumn
from .data_column import DataColumn
from .ruler_column import RulerColumn

__all__ = [
    'ColumnProtocol',
    'BaseColumn',
    'ImageColumn',
    'DataColumn',
    'RulerColumn',
    'HEADER_HEIGHT',
    'TITLE_HEIGHT',
    'DOMAIN_PADDING',
]
