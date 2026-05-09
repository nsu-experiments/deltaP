# scripts/visualization/charts/primitives/line.py
"""
Line chart primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple, Dict
import pandas as pd


def line_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = '#2196F3',
    marker: str = 'o',
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Basic line plot.
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Line color
        marker: Marker style
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(df[x_col], df[y_col], 
            color=color, marker=marker, linewidth=2, markersize=8)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def multi_line(
    df: pd.DataFrame,
    x_col: str,
    y_cols: List[str],
    labels: Optional[List[str]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[List[str]] = None,
    markers: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Multiple lines on same plot.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = colors or ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    markers = markers or ['o', 's', '^', 'd']
    labels = labels or y_cols
    
    for col, label, color, marker in zip(y_cols, labels, colors, markers):
        ax.plot(df[x_col], df[col],
                label=label, color=color, marker=marker,
                linewidth=2, markersize=8)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def line_with_ci(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    ci_lower_col: str,
    ci_upper_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = '#2196F3',
    marker: str = 'o',
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Line plot with confidence interval shading.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(df[x_col], df[y_col],
            color=color, marker=marker, linewidth=2, markersize=8)
    
    ax.fill_between(df[x_col],
                     df[ci_lower_col],
                     df[ci_upper_col],
                     alpha=0.2, color=color)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def multi_line_with_ci(
    df: pd.DataFrame,
    x_col: str,
    group_col: str,
    y_col: str,
    ci_lower_col: str,
    ci_upper_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[Dict[str, str]] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Multiple lines with confidence intervals, grouped by a category.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    default_colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    
    for i, (group_name, group_data) in enumerate(df.groupby(group_col)):
        color = colors.get(group_name, default_colors[i % len(default_colors)]) if colors else default_colors[i % len(default_colors)]
        
        ax.plot(group_data[x_col], group_data[y_col],
                label=group_name, color=color,
                marker='o', linewidth=2, markersize=8)
        
        ax.fill_between(group_data[x_col],
                         group_data[ci_lower_col],
                         group_data[ci_upper_col],
                         alpha=0.2, color=color)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig