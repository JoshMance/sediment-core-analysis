"""Entity type registry.

Single source of truth for all entity types in the application.
Used by the store's container for type validation, filtering, and stats.
"""
from src.domain.entities.image_entity import ImageEntity

ENTITY_TYPES: dict[str, type] = {
    "ImageEntity": ImageEntity,
}
