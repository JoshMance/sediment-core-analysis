"""Entity type registry.

Single source of truth for all entity types in the application.
Used by the store's container for type validation, filtering, and stats.
"""
from src.domain.entities.image_entity import ImageEntity
from src.domain.entities.core_entity import CoreEntity
from src.domain.entities.csv_entity import CsvEntity

ENTITY_TYPES: dict[str, type] = {
    "ImageEntity": ImageEntity,
    "CoreEntity": CoreEntity,
    "CsvEntity": CsvEntity,
}
