# scripts/visualization/charts/primitives/bar.py
"""
Bar chart primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple
import pandas as pd


def bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Basic bar chart.
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis (categories)
        y_col: Column name for y-axis (values)
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        colors: List of colors for bars
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x_data = df[x_col]
    y_data = df[y_col]
    
    ax.bar(x_data, y_data, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def bar_chart_with_ci(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    ci_lower_col: str,
    ci_upper_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Bar chart with confidence interval error bars.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x_data = range(len(df))
    y_data = df[y_col].values
    
    # Calculate asymmetric error bars
    errors_lower = y_data - df[ci_lower_col].values
    errors_upper = df[ci_upper_col].values - y_data
    
    bars = ax.bar(
        x_data, y_data,
        color=colors or ['#4CAF50', '#F44336', '#2196F3'],
        alpha=0.8,
        yerr=[errors_lower, errors_upper],
        capsize=10,
        edgecolor='black',
        linewidth=1.5,
        error_kw={'linewidth': 2}
    )
    
    # Add value labels on bars
    for bar, val in zip(bars, y_data):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height + 0.05,
            f'{val:.1%}',
            ha='center', va='bottom', fontweight='bold', fontsize=10
        )
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x_data)
    ax.set_xticklabels(df[x_col])
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def grouped_bar(
    df: pd.DataFrame,
    x_col: str,
    value_cols: List[str],
    labels: Optional[List[str]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Grouped bar chart for comparing multiple metrics side-by-side.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x = range(len(df))
    width = 0.8 / len(value_cols)
    
    colors = colors or ['#2E86AB', '#A23B72', '#F18F01', '#06A77D']
    labels = labels or value_cols
    
    for i, (col, label, color) in enumerate(zip(value_cols, labels, colors)):
        positions = [xi + (i - len(value_cols)/2 + 0.5) * width for xi in x]
        ax.bar(positions, df[col].values, width, label=label, color=color, alpha=0.8)
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df[x_col])
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig