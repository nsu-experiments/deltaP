# scripts/visualization/charts/primitives/histogram.py
"""
Histogram primitives for ΔP visualization.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Tuple, List
import pandas as pd


def histogram(
    df: pd.DataFrame,
    col: str,
    bins: int = 30,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Frequency",
    color: str = '#2196F3',
    alpha: float = 0.7,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Basic histogram.
    
    Args:
        df: DataFrame with data
        col: Column name to plot
        bins: Number of bins
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Bar color
        alpha: Transparency
        figsize: Figure size tuple
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.hist(df[col], bins=bins, color=color, alpha=alpha, edgecolor='black')
    
    # Add mean line
    mean_val = df[col].mean()
    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean = {mean_val:.2f}')
    
    ax.set_xlabel(xlabel or col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def histogram_with_kde(
    df: pd.DataFrame,
    col: str,
    bins: int = 30,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Density",
    color: str = '#2196F3',
    alpha: float = 0.7,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Histogram with kernel density estimate overlay.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Histogram
    ax.hist(df[col], bins=bins, density=True, color=color, alpha=alpha, edgecolor='black', label='Histogram')
    
    # KDE overlay
    from scipy import stats
    kde = stats.gaussian_kde(df[col].dropna())
    x_range = np.linspace(df[col].min(), df[col].max(), 200)
    ax.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')
    
    # Statistics
    mean_val = df[col].mean()
    median_val = df[col].median()
    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'Mean = {mean_val:.2f}')
    ax.axvline(median_val, color='green', linestyle='--', linewidth=2, alpha=0.7, label=f'Median = {median_val:.2f}')
    
    ax.set_xlabel(xlabel or col, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def overlaid_histograms(
    df: pd.DataFrame,
    columns: List[str],
    labels: Optional[List[str]] = None,
    bins: int = 30,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Frequency",
    colors: Optional[List[str]] = None,
    alpha: float = 0.5,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Multiple overlaid histograms for comparison.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = colors or ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    labels = labels or columns
    
    for col, label, color in zip(columns, labels, colors):
        ax.hist(df[col], bins=bins, color=color, alpha=alpha, 
                edgecolor='black', label=label)
    
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig


def histogram_by_category(
    df: pd.DataFrame,
    value_col: str,
    category_col: str,
    bins: int = 30,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Frequency",
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Faceted histograms by category (subplots).
    """
    categories = df[category_col].unique()
    n_cats = len(categories)
    
    fig, axes = plt.subplots(1, n_cats, figsize=figsize, sharey=True)
    
    if n_cats == 1:
        axes = [axes]
    
    colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
    
    for ax, category, color in zip(axes, categories, colors):
        cat_data = df[df[category_col] == category][value_col]
        ax.hist(cat_data, bins=bins, color=color, alpha=0.7, edgecolor='black')
        ax.set_title(f'{category}', fontweight='bold')
        ax.set_xlabel(xlabel or value_col, fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    axes[0].set_ylabel(ylabel, fontsize=12, fontweight='bold')
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    return fig