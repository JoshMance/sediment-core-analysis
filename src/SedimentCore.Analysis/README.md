# SedimentCore.Analysis

This project contains all numerical and colour analysis logic.

## Purpose
- Single source of truth for scientific computation
- FFT, PCA, colour conversions, depth alignment algorithms
- Statistical analysis and data processing

## Dependencies
- References `SedimentCore.Domain` for data models

## Guidelines
- **NO** UI logic or dependencies
- All scientific algorithms and computations belong here
- Implementations should be testable and framework-agnostic
