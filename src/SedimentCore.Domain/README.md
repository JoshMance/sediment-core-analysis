# SedimentCore.Domain

This project contains all core scientific data models (POCOs only).

## Purpose
- Define data structures for sediment core metadata, depth profiles, colour profiles, and measurement units
- Pure data models with no business logic, UI logic, or analysis logic
- Shared types used by both the Analysis and UI projects

## Guidelines
- **NO** analysis or computation logic
- **NO** UI-specific code or dependencies
- Only data models, enums, and simple value objects
