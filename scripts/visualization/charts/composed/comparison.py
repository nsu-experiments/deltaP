# scripts/visualization/charts/composed/comparison.py
"""
Composed comparison charts for ΔP logistics analysis.
Combines primitives for high-level analysis patterns.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict, Any
from ..primitives import bar, line, boxplot


def route_comparison(
    df: pd.DataFrame,
    route_col: str = 'route',
    success_col: str = 'composite_success',
    route_names: Optional[Dict[Any, str]] = None,
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Compare success rates across routes with confidence intervals.
    
    Args:
        df: Raw simulation results with individual iterations
        route_col: Column name for route identifier
        success_col: Column name for success indicator (0/1 or True/False)
        route_names: Mapping from route IDs to display names
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    # Default route names
    if route_names is None:
        route_names = {
            1: 'Kazakhstan',
            2: 'Kyrgyzstan',
            3: 'Hybrid',
            '1': 'Kazakhstan',
            '2': 'Kyrgyzstan',
            '3': 'Hybrid'
        }
    
    # Map route names
    df_mapped = df.copy()
    df_mapped['route_name'] = df_mapped[route_col].astype(str).map(route_names)
    
    # Calculate statistics per route
    stats = []
    for route_name in ['Kazakhstan', 'Kyrgyzstan', 'Hybrid']:
        route_data = df_mapped[df_mapped['route_name'] == route_name]
        if len(route_data) == 0:
            continue
            
        success_rate = route_data[success_col].mean()
        n = len(route_data)
        
        # 95% CI
        se = (success_rate * (1 - success_rate) / n) ** 0.5
        ci_lower = max(0, success_rate - 1.96 * se)
        ci_upper = min(1, success_rate + 1.96 * se)
        
        stats.append({
            'route_name': route_name,
            'success_rate': success_rate,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n': n
        })
    
    stats_df = pd.DataFrame(stats)
    
    # Create bar chart with CI
    fig = bar.bar_chart_with_ci(
        stats_df,
        x_col='route_name',
        y_col='success_rate',
        ci_lower_col='ci_lower',
        ci_upper_col='ci_upper',
        title='Route Performance Comparison - Baseline Scenario\n(with 95% Confidence Intervals)',
        xlabel='Route',
        ylabel='Success Rate',
        colors=['#4CAF50', '#F44336', '#2196F3']
    )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Route comparison saved to: {output_path}")
    
    return fig


def kpi_breakdown(
    stats_df: pd.DataFrame,
    route_col: str = 'route',
    scenario_col: str = 'scenario',
    kpi_cols: Optional[list] = None,
    kpi_labels: Optional[list] = None,
    route_names: Optional[Dict[Any, str]] = None,
    baseline_scenario: int = 1,
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Compare KPI components across routes for baseline scenario.
    
    Args:
        stats_df: Aggregated statistics DataFrame
        route_col: Column name for route identifier
        scenario_col: Column name for scenario identifier
        kpi_cols: List of KPI column names
        kpi_labels: Display labels for KPIs
        route_names: Mapping from route IDs to display names
        baseline_scenario: Scenario ID to filter for
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    # Defaults
    if kpi_cols is None:
        kpi_cols = ['efficiency_rate', 'service_rate', 'carbon_rate']
    if kpi_labels is None:
        kpi_labels = ['Transport Efficiency', 'Service Quality', 'Carbon Limit']
    if route_names is None:
        route_names = {
            1: 'Kazakhstan',
            2: 'Kyrgyzstan',
            3: 'Hybrid',
            '1': 'Kazakhstan',
            '2': 'Kyrgyzstan',
            '3': 'Hybrid'
        }
    
    # Filter baseline and map route names
    baseline = stats_df[stats_df[scenario_col] == baseline_scenario].copy()
    baseline['route_name'] = baseline[route_col].astype(str).map(route_names)
    baseline = baseline.sort_values(route_col)
    
    # Create grouped bar chart
    fig = bar.grouped_bar(
        baseline,
        x_col='route_name',
        value_cols=kpi_cols,
        labels=kpi_labels,
        title='KPI Component Comparison - Baseline Scenario',
        xlabel='Route',
        ylabel='Success Rate',
        colors=['#2E86AB', '#A23B72', '#F18F01']
    )
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 KPI breakdown saved to: {output_path}")
    
    return fig


def scenario_sensitivity(
    stats_df: pd.DataFrame,
    route_col: str = 'route',
    scenario_col: str = 'scenario',
    success_col: str = 'success_rate',
    ci_lower_col: str = 'ci_lower',
    ci_upper_col: str = 'ci_upper',
    route_names: Optional[Dict[Any, str]] = None,
    scenario_names: Optional[Dict[int, str]] = None,
    output_path: Optional[Path] = None
) -> plt.Figure:
    """
    Show how routes perform across different scenarios.
    
    Args:
        stats_df: Aggregated statistics DataFrame
        route_col: Column name for route identifier
        scenario_col: Column name for scenario identifier
        success_col: Column name for success rate
        ci_lower_col: Column name for CI lower bound
        ci_upper_col: Column name for CI upper bound
        route_names: Mapping from route IDs to display names
        scenario_names: Mapping from scenario IDs to display names
        output_path: Optional path to save figure
    
    Returns:
        matplotlib Figure
    """
    # Check if multiple scenarios exist
    n_scenarios = stats_df[scenario_col].nunique()
    if n_scenarios < 2:
        print("⚠️  Only one scenario found, skipping scenario sensitivity plot")
        return None
    
    # Defaults
    if route_names is None:
        route_names = {
            1: 'Kazakhstan',
            2: 'Kyrgyzstan',
            3: 'Hybrid',
            '1': 'Kazakhstan',
            '2': 'Kyrgyzstan',
            '3': 'Hybrid'
        }
    if scenario_names is None:
        scenario_names = {
            1: 'Baseline',
            2: 'Carbon\nStrict',
            3: 'Border\nTight',
            4: 'Carbon &\nBorder'
        }
    
    # Map names
    df_mapped = stats_df.copy()
    df_mapped['route_name'] = df_mapped[route_col].astype(str).map(route_names)
    df_mapped['scenario_name'] = df_mapped[scenario_col].map(scenario_names)
    
    # Create multi-line plot with CI
    fig = line.multi_line_with_ci(
        df_mapped,
        x_col='scenario_name',
        group_col='route_name',
        y_col=success_col,
        ci_lower_col=ci_lower_col,
        ci_upper_col=ci_upper_col,
        title='Route Resilience Across Disruption Scenarios',
        xlabel='Scenario',
        ylabel='Success Rate'
    )
    
    # Adjust y-axis limits
    ax = fig.gca()
    ax.set_ylim(0, 1.0)
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Scenario sensitivity saved to: {output_path}")
    
    return fig