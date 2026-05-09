# scripts/visualization/charts/primitives/scatter.py
"""
Scatter plot primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Tuple
import pandas as pd


def scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = '#2196F3',
    alpha: float = 0.6,
    s: float = 50,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Basic scatter plot.
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Point color
        alpha: Transparency
        s: Point size
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.scatter(df[x_col], df[y_col], color=color, alpha=alpha, s=s, edgecolors='black')
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def scatter_with_regression(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = '#2196F3',
    alpha: float = 0.6,
    s: float = 50,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Scatter plot with linear regression line.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x = df[x_col].values
    y = df[y_col].values
    
    # Scatter points
    ax.scatter(x, y, color=color, alpha=alpha, s=s, edgecolors='black')
    
    # Regression line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), "r--", linewidth=2, label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
    
    # Calculate R²
    y_pred = p(x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    ax.text(0.05, 0.95, f'R² = {r_squared:.3f}',
            transform=ax.transAxes, fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def scatter_by_category(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    category_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[dict] = None,
    alpha: float = 0.6,
    s: float = 50,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Scatter plot with points colored by category.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    default_colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800', '#9C27B0']
    
    for i, (category, group) in enumerate(df.groupby(category_col)):
        color = colors.get(category, default_colors[i % len(default_colors)]) if colors else default_colors[i % len(default_colors)]
        ax.scatter(group[x_col], group[y_col],
                   label=category, color=color, alpha=alpha, s=s, edgecolors='black')
    
    ax.set_xlabel(xlabel or x_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or y_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(title=category_col)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig