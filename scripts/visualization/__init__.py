# scripts/visualization/__init__.py
"""
ΔP Visualization Pipeline
========================

Modular visualization system for ΔP simulation results.

Structure:
- loaders: Data loading from CSV/HDF5
- charts.primitives: Basic chart types (bar, line, heatmap, etc.)
- charts.composed: High-level analysis patterns (comparison, EDA, sensitivity)
- autodiscover: Metadata-driven chart generation
"""

from . import loaders
from . import charts
from . import autodiscover

__all__ = ['loaders', 'charts', 'autodiscover']

__version__ = '0.1.0'