# scripts/visualization/charts/primitives/boxplot.py
"""
Boxplot primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Tuple, List
import pandas as pd


def boxplot(
    df: pd.DataFrame,
    columns: List[str],
    labels: Optional[List[str]] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Basic boxplot for one or more columns.
    
    Args:
        df: DataFrame with data
        columns: List of column names to plot
        labels: Display labels for columns
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        colors: List of colors for boxes
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    data = [df[col].dropna() for col in columns]
    labels = labels or columns
    
    bp = ax.boxplot(data, labels=labels, patch_artist=True, 
                     showmeans=True, meanline=True)
    
    # Color boxes
    if colors:
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def boxplot_by_category(
    df: pd.DataFrame,
    value_col: str,
    category_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[dict] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Boxplot grouped by category.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    categories = sorted(df[category_col].unique())
    data = [df[df[category_col] == cat][value_col].dropna() for cat in categories]
    
    bp = ax.boxplot(data, labels=categories, patch_artist=True,
                     showmeans=True, meanline=True)
    
    # Color boxes
    default_colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    for i, (patch, cat) in enumerate(zip(bp['boxes'], categories)):
        color = colors.get(cat, default_colors[i % len(default_colors)]) if colors else default_colors[i % len(default_colors)]
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xlabel(xlabel or category_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or value_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def violin_plot(
    df: pd.DataFrame,
    value_col: str,
    category_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[dict] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Violin plot showing distribution by category.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    categories = sorted(df[category_col].unique())
    data = [df[df[category_col] == cat][value_col].dropna() for cat in categories]
    
    parts = ax.violinplot(data, positions=range(len(categories)),
                          showmeans=True, showmedians=True)
    
    # Color violins
    default_colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    for i, pc in enumerate(parts['bodies']):
        color = colors.get(categories[i], default_colors[i % len(default_colors)]) if colors else default_colors[i % len(default_colors)]
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)
    ax.set_xlabel(xlabel or category_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or value_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def boxplot_with_points(
    df: pd.DataFrame,
    value_col: str,
    category_col: str,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[dict] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Boxplot with individual data points overlaid.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    categories = sorted(df[category_col].unique())
    data = [df[df[category_col] == cat][value_col].dropna() for cat in categories]
    
    bp = ax.boxplot(data, labels=categories, patch_artist=True,
                     showmeans=True, meanline=True)
    
    # Color boxes
    default_colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    for i, (patch, cat) in enumerate(zip(bp['boxes'], categories)):
        color = colors.get(cat, default_colors[i % len(default_colors)]) if colors else default_colors[i % len(default_colors)]
        patch.set_facecolor(color)
        patch.set_alpha(0.5)
        
        # Overlay points with jitter
        cat_data = df[df[category_col] == cat][value_col].dropna()
        x = np.random.normal(i + 1, 0.04, size=len(cat_data))
        ax.scatter(x, cat_data, alpha=0.4, s=20, color=color)
    
    ax.set_xlabel(xlabel or category_col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel or value_col, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig