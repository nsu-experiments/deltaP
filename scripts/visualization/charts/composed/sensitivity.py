# scripts/visualization/charts/composed/sensitivity.py
"""
Sensitivity analysis charts for ΔP parameter sweeps and scenario testing.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..primitives import line, heatmap, bar


def parameter_sweep(
    df: pd.DataFrame,
    parameter_col: str,
    metric_col: str,
    group_col: Optional[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Visualize how a metric changes as a parameter is swept.
    
    Args:
        df: DataFrame with parameter sweep results
        parameter_col: Column with parameter values
        metric_col: Column with metric to track
        group_col: Optional grouping (e.g., different routes)
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    if group_col:
        fig = line.multi_line(
            df,
            x_col=parameter_col,
            y_cols=[metric_col],
            title=title or f'{metric_col} vs {parameter_col}',
            xlabel=xlabel or parameter_col,
            ylabel=ylabel or metric_col
        )
    else:
        fig = line.line_plot(
            df,
            x_col=parameter_col,
            y_col=metric_col,
            title=title or f'{metric_col} vs {parameter_col}',
            xlabel=xlabel or parameter_col,
            ylabel=ylabel or metric_col
        )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Parameter sweep saved to: {output_path}")
    
    return fig


def scenario_comparison_matrix(
    df: pd.DataFrame,
    row_col: str,
    col_col: str,
    value_col: str,
    title: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Heatmap comparing scenarios across two dimensions.
    
    Args:
        df: DataFrame with scenario results
        row_col: Column for heatmap rows
        col_col: Column for heatmap columns
        value_col: Column for cell values
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    fig = heatmap.pivot_heatmap(
        df,
        index_col=row_col,
        columns_col=col_col,
        values_col=value_col,
        title=title or f'{value_col} by {row_col} and {col_col}',
        cmap='RdYlGn',
        fmt='.2%'
    )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Scenario comparison matrix saved to: {output_path}")
    
    return fig


def tornado_diagram(
    df: pd.DataFrame,
    parameter_col: str,
    impact_col: str,
    baseline_value: float,
    title: str = "Tornado Diagram - Parameter Sensitivity",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Tornado diagram showing impact of parameter variations.
    
    Args:
        df: DataFrame with parameter variations and their impacts
        parameter_col: Column with parameter names
        impact_col: Column with impact values (deviation from baseline)
        baseline_value: Baseline metric value
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calculate deviations from baseline
    df_sorted = df.copy()
    df_sorted['deviation'] = abs(df_sorted[impact_col] - baseline_value)
    df_sorted = df_sorted.sort_values('deviation', ascending=True)
    
    # Create horizontal bars
    y_pos = range(len(df_sorted))
    bars = ax.barh(y_pos, df_sorted[impact_col] - baseline_value, 
                   color=['#F44336' if x < 0 else '#4CAF50' 
                          for x in (df_sorted[impact_col] - baseline_value)])
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[parameter_col])
    ax.axvline(0, color='black', linewidth=2, linestyle='--')
    ax.set_xlabel('Impact on Metric (deviation from baseline)', 
                  fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Tornado diagram saved to: {output_path}")
    
    return fig


def threshold_analysis(
    df: pd.DataFrame,
    threshold_col: str,
    success_col: str,
    category_col: Optional[str] = None,
    title: str = "",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Show how success rate changes with threshold values.
    
    Args:
        df: DataFrame with threshold sweep results
        threshold_col: Column with threshold values
        success_col: Column with success rates
        category_col: Optional grouping column
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    if category_col:
        # Group by category and plot multiple lines
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['#2196F3', '#4CAF50', '#F44336', '#FF9800']
        for i, (category, group) in enumerate(df.groupby(category_col)):
            ax.plot(group[threshold_col], group[success_col],
                    label=category, color=colors[i % len(colors)],
                    marker='o', linewidth=2, markersize=8)
        
        ax.set_xlabel(threshold_col, fontsize=12, fontweight='bold')
        ax.set_ylabel(success_col, fontsize=12, fontweight='bold')
        ax.set_title(title or f'{success_col} vs {threshold_col}',
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(title=category_col)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
    else:
        fig = line.line_plot(
            df,
            x_col=threshold_col,
            y_col=success_col,
            title=title or f'{success_col} vs {threshold_col}'
        )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Threshold analysis saved to: {output_path}")
    
    return fig


def monte_carlo_convergence(
    df: pd.DataFrame,
    iteration_col: str,
    metric_col: str,
    window_size: int = 100,
    title: str = "Monte Carlo Convergence Analysis",
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Show convergence of Monte Carlo simulation over iterations.
    
    Args:
        df: DataFrame with iteration-by-iteration results
        iteration_col: Column with iteration numbers
        metric_col: Column with metric values
        window_size: Window size for rolling mean
        title: Chart title
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort by iteration
    df_sorted = df.sort_values(iteration_col)
    
    # Calculate cumulative mean
    cumulative_mean = df_sorted[metric_col].expanding().mean()
    
    # Calculate rolling standard deviation
    rolling_std = df_sorted[metric_col].rolling(window=window_size).std()
    
    # Plot
    ax.plot(df_sorted[iteration_col], cumulative_mean,
            label='Cumulative Mean', color='#2196F3', linewidth=2)
    
    ax.fill_between(df_sorted[iteration_col],
                     cumulative_mean - rolling_std,
                     cumulative_mean + rolling_std,
                     alpha=0.2, color='#2196F3',
                     label=f'±1 SD (rolling {window_size})')
    
    ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'Cumulative Mean of {metric_col}', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Monte Carlo convergence saved to: {output_path}")
    
    return fig