# scripts/visualization/charts/primitives/heatmap.py
"""
Heatmap primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Optional, Tuple, List
import pandas as pd


def heatmap(
    df: pd.DataFrame,
    title: str = "",
    cmap: str = 'RdBu_r',
    annot: bool = True,
    fmt: str = '.2f',
    figsize: Tuple[int, int] = (8, 6),
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    center: Optional[float] = None
) -> plt.Figure:
    """
    Basic heatmap from DataFrame.
    
    Args:
        df: DataFrame (values are the heatmap cells)
        title: Chart title
        cmap: Colormap name
        annot: Show values in cells
        fmt: Format string for annotations
        figsize: Figure size tuple
        vmin: Minimum value for colormap
        vmax: Maximum value for colormap
        center: Center value for diverging colormap
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(df, annot=annot, fmt=fmt, cmap=cmap,
                center=center, square=True, linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax, vmin=vmin, vmax=vmax)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig


def correlation_heatmap(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    title: str = "Correlation Matrix",
    figsize: Tuple[int, int] = (8, 6)
) -> plt.Figure:
    """
    Correlation matrix heatmap.
    
    Args:
        df: DataFrame with numeric columns
        columns: Subset of columns to correlate (default: all numeric)
        labels: Display labels for columns
        title: Chart title
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    if columns:
        corr_data = df[columns].copy()
    else:
        corr_data = df.select_dtypes(include=[np.number])
    
    if labels:
        corr_data.columns = labels
    
    corr_matrix = corr_data.corr()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, square=True, linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax, vmin=-1, vmax=1)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig


def pivot_heatmap(
    df: pd.DataFrame,
    index_col: str,
    columns_col: str,
    values_col: str,
    title: str = "",
    cmap: str = 'YlOrRd',
    annot: bool = True,
    fmt: str = '.2f',
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """
    Heatmap from pivoted data.
    
    Args:
        df: Long-format DataFrame
        index_col: Column to use for rows
        columns_col: Column to use for columns
        values_col: Column to use for cell values
        title: Chart title
        cmap: Colormap name
        annot: Show values in cells
        fmt: Format string for annotations
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    pivot_table = df.pivot(index=index_col, columns=columns_col, values=values_col)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(pivot_table, annot=annot, fmt=fmt, cmap=cmap,
                square=False, linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel(columns_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(index_col, fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    return fig