# scripts/visualization/charts/composed/eda.py
"""
Exploratory Data Analysis (EDA) charts for ΔP simulation results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, List
from ..primitives import histogram, heatmap, scatter, boxplot


def distribution_analysis(
    df: pd.DataFrame,
    value_col: str,
    title: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Comprehensive distribution analysis with histogram and KDE.
    
    Args:
        df: DataFrame with data
        value_col: Column to analyze
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    fig = histogram.histogram_with_kde(
        df,
        col=value_col,
        title=title or f'Distribution of {value_col}',
        xlabel=value_col,
        bins=50
    )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Distribution analysis saved to: {output_path}")
    
    return fig


def correlation_analysis(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    title: str = "Correlation Matrix",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Correlation heatmap between variables.
    
    Args:
        df: DataFrame with numeric columns
        columns: Subset of columns to correlate
        labels: Display labels for columns
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    fig = heatmap.correlation_heatmap(
        df,
        columns=columns,
        labels=labels,
        title=title
    )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Correlation analysis saved to: {output_path}")
    
    return fig


def outlier_detection(
    df: pd.DataFrame,
    value_col: str,
    category_col: Optional[str] = None,
    title: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Boxplot-based outlier detection.
    
    Args:
        df: DataFrame with data
        value_col: Column to analyze for outliers
        category_col: Optional grouping column
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    if category_col:
        fig = boxplot.boxplot_with_points(
            df,
            value_col=value_col,
            category_col=category_col,
            title=title or f'Outlier Detection: {value_col} by {category_col}'
        )
    else:
        fig = boxplot.boxplot(
            df,
            columns=[value_col],
            title=title or f'Outlier Detection: {value_col}'
        )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Outlier detection saved to: {output_path}")
    
    return fig


def multivariate_comparison(
    df: pd.DataFrame,
    category_col: str,
    value_cols: List[str],
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Compare distributions of multiple variables across categories.
    
    Args:
        df: DataFrame with data
        category_col: Grouping column
        value_cols: List of value columns to compare
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    n_vars = len(value_cols)
    fig, axes = plt.subplots(1, n_vars, figsize=(6*n_vars, 5), sharey=False)
    
    if n_vars == 1:
        axes = [axes]
    
    for ax, col in zip(axes, value_cols):
        categories = sorted(df[category_col].unique())
        data = [df[df[category_col] == cat][col].dropna() for cat in categories]
        
        bp = ax.boxplot(data, labels=categories, patch_artist=True,
                        showmeans=True, meanline=True)
        
        # Color boxes
        colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title(col, fontweight='bold', fontsize=12)
        ax.set_xlabel(category_col, fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    fig.suptitle(f'Multivariate Comparison by {category_col}', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Multivariate comparison saved to: {output_path}")
    
    return fig


def pairwise_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    category_col: Optional[str] = None,
    title: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Pairwise scatter plot with optional category coloring.
    
    Args:
        df: DataFrame with data
        x_col: X-axis column
        y_col: Y-axis column
        category_col: Optional category for coloring
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    if category_col:
        fig = scatter.scatter_by_category(
            df,
            x_col=x_col,
            y_col=y_col,
            category_col=category_col,
            title=title or f'{y_col} vs {x_col} by {category_col}'
        )
    else:
        fig = scatter.scatter_with_regression(
            df,
            x_col=x_col,
            y_col=y_col,
            title=title or f'{y_col} vs {x_col}'
        )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Pairwise scatter saved to: {output_path}")
    
    return fig


def full_eda_report(
    df: pd.DataFrame,
    value_cols: List[str],
    category_col: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> dict:
    """
    Generate comprehensive EDA report with multiple charts.
    
    Args:
        df: DataFrame with simulation results
        value_cols: List of numeric columns to analyze
        category_col: Optional grouping column
        output_dir: Optional directory to save all charts
    
    Returns:
        Dictionary mapping chart names to Figure objects
    """
    charts = {}
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Distributions
    for col in value_cols:
        fig = distribution_analysis(
            df, col,
            output_path=output_dir / f'distribution_{col}.png' if output_dir else None
        )
        charts[f'distribution_{col}'] = fig
        plt.close(fig)
    
    # 2. Correlations
    fig = correlation_analysis(
        df, columns=value_cols,
        output_path=output_dir / 'correlations.png' if output_dir else None
    )
    charts['correlations'] = fig
    plt.close(fig)
    
    # 3. Outliers by category
    if category_col:
        for col in value_cols:
            fig = outlier_detection(
                df, col, category_col=category_col,
                output_path=output_dir / f'outliers_{col}.png' if output_dir else None
            )
            charts[f'outliers_{col}'] = fig
            plt.close(fig)
        
        # 4. Multivariate comparison
        fig = multivariate_comparison(
            df, category_col, value_cols,
            output_path=output_dir / 'multivariate.png' if output_dir else None
        )
        charts['multivariate'] = fig
        plt.close(fig)
    
    print(f"✅ Generated {len(charts)} EDA charts")
    
    return charts