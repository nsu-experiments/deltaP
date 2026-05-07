#!/usr/bin/env python3
"""
Visualization Script for ΔP Logistics Simulation Results
========================================================

Generates plots comparing route performance across scenarios.

Usage:
    python visualize_results.py results/simulation_stats_*.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
import sys


def plot_success_rates_comparison(raw_df: pd.DataFrame, output_path: Path):
    """Create histogram showing distribution of success/failure across iterations."""
    
    route_names = {
        '1': 'Kazakhstan',
        '2': 'Kyrgyzstan', 
        '3': 'Hybrid',
        'Kazakhstan': 'Kazakhstan',
        'Kyrgyzstan': 'Kyrgyzstan',
        'Hybrid': 'Hybrid'
    }
    
    # Map route names
    raw_df['route_name'] = raw_df['route'].astype(str).map(route_names)
    
    # Calculate success rates
    routes_order = ['Kazakhstan', 'Kyrgyzstan', 'Hybrid']
    success_rates = []
    sample_sizes = []
    
    for route in routes_order:
        route_data = raw_df[raw_df['route_name'] == route]
        success_rate = route_data['composite_success'].mean()
        n = len(route_data)
        
        success_rates.append(success_rate)
        sample_sizes.append(n)
        
        # Calculate 95% CI
        se = (success_rate * (1 - success_rate) / n) ** 0.5
        ci_lower = max(0, success_rate - 1.96 * se)
        ci_upper = min(1, success_rate + 1.96 * se)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(routes_order))
    colors = ['#4CAF50', '#F44336', '#2196F3']  # Green, Red, Blue
    
    # Calculate error bars (symmetric around mean)
    errors_lower = []
    errors_upper = []
    
    for route in routes_order:
        route_data = raw_df[raw_df['route_name'] == route]
        rate = route_data['composite_success'].mean()
        n = len(route_data)
        se = (rate * (1 - rate) / n) ** 0.5
        
        # Calculate CI bounds
        ci_lower = max(0, rate - 1.96 * se)
        ci_upper = min(1, rate + 1.96 * se)
        
        # Error bar lengths from the mean
        err_lower = rate - ci_lower
        err_upper = ci_upper - rate
        
        errors_lower.append(err_lower)
        errors_upper.append(err_upper)
        
        print(f"  {route}: rate={rate:.3f}, CI=[{ci_lower:.3f}, {ci_upper:.3f}], errors=[{err_lower:.3f}, {err_upper:.3f}]")
    
    # Plot with asymmetric error bars
    bars = ax.bar(x, success_rates, color=colors, alpha=0.8, 
                   yerr=[errors_lower, errors_upper], capsize=10, 
                   edgecolor='black', linewidth=1.5, error_kw={'linewidth': 2})
    
    # Add value labels on bars
    for i, (bar, rate, n) in enumerate(zip(bars, success_rates, sample_sizes)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
               f'{rate:.1%}\n(n={n})',
               ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.set_xlabel('Route', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate', fontsize=12, fontweight='bold')
    ax.set_title('Route Performance Comparison - Baseline Scenario\n(with 95% Confidence Intervals)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(routes_order)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Success rate comparison saved to: {output_path}")
    plt.close()


def plot_kpi_breakdown(stats: pd.DataFrame, output_path: Path):
    """Create stacked bar chart showing KPI component breakdown."""
    
    route_names = {
        '1': 'Kazakhstan',
        '2': 'Kyrgyzstan', 
        '3': 'Hybrid',
        'Kazakhstan': 'Kazakhstan',
        'Kyrgyzstan': 'Kyrgyzstan',
        'Hybrid': 'Hybrid'
    }
    
    stats['route_name'] = stats['route'].astype(str).map(route_names)
    
    # Focus on baseline scenario
    baseline = stats[stats['scenario'] == 1].copy()
    
    if baseline.empty:
        print("⚠️  No baseline scenario data found")
        return
    
    baseline = baseline.sort_values('route')
    
    # Prepare data for grouped bar chart (not stacked, to show zeros)
    kpis = ['efficiency_rate', 'service_rate', 'carbon_rate']
    kpi_labels = ['Transport Efficiency', 'Service Quality', 'Carbon Limit']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(baseline))
    width = 0.25
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    
    for i, (kpi, label, color) in enumerate(zip(kpis, kpi_labels, colors)):
        positions = [xi + (i - 1) * width for xi in x]
        values = baseline[kpi].values
        ax.bar(positions, values, width, label=label, color=color, alpha=0.8)
    
    ax.set_xlabel('Route', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate', fontsize=12, fontweight='bold')
    ax.set_title('KPI Component Comparison - Baseline Scenario',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(baseline['route_name'])
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 KPI breakdown saved to: {output_path}")
    plt.close()


def plot_correlation_heatmap(stats: pd.DataFrame, output_path: Path):
    """Create correlation heatmap between KPIs and composite score."""
    
    # Focus on baseline scenario
    baseline = stats[stats['scenario'] == 1].copy()
    
    if baseline.empty:
        print("⚠️  No baseline scenario data found")
        return
    
    # Select relevant columns
    corr_cols = ['efficiency_rate', 'service_rate', 'carbon_rate', 'success_rate']
    corr_data = baseline[corr_cols].copy()
    corr_data.columns = ['Efficiency', 'Service', 'Carbon', 'Composite']
    
    # Compute correlation matrix
    corr_matrix = corr_data.corr()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plot heatmap
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                ax=ax, vmin=-1, vmax=1)
    
    ax.set_title('Correlation between KPIs and Composite Score\n(Baseline Scenario)',
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Correlation heatmap saved to: {output_path}")
    plt.close()


def plot_scenario_sensitivity(stats: pd.DataFrame, output_path: Path):
    """Create line plot showing how routes perform across scenarios."""
    
    # Check if we have multiple scenarios
    n_scenarios = stats['scenario'].nunique()
    if n_scenarios < 2:
        print("⚠️  Only one scenario found, skipping scenario sensitivity plot")
        print("    (Need multiple scenarios: baseline, border_tight, etc.)")
        return
    
    route_names = {
        '1': 'Kazakhstan',
        '2': 'Kyrgyzstan', 
        '3': 'Hybrid',
        'Kazakhstan': 'Kazakhstan',
        'Kyrgyzstan': 'Kyrgyzstan',
        'Hybrid': 'Hybrid'
    }
    
    scenario_names = {
        1: 'Baseline',
        2: 'Carbon\nStrict',
        3: 'Border\nTight',
        4: 'Carbon &\nBorder'
    }
    
    stats['route_name'] = stats['route'].astype(str).map(route_names)
    stats['scenario_name'] = stats['scenario'].map(scenario_names)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for route in stats['route_name'].unique():
        route_data = stats[stats['route_name'] == route].sort_values('scenario')
        
        ax.plot(route_data['scenario_name'], route_data['success_rate'],
                marker='o', linewidth=2, markersize=8, label=route)
        
        # Add confidence interval shading
        ax.fill_between(route_data['scenario_name'],
                        route_data['ci_lower'],
                        route_data['ci_upper'],
                        alpha=0.2)
    
    ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate', fontsize=12, fontweight='bold')
    ax.set_title('Route Resilience Across Disruption Scenarios',
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Route', loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"📊 Scenario sensitivity saved to: {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Visualize ΔP logistics simulation results'
    )
    parser.add_argument(
        'stats_file',
        type=str,
        help='Path to statistics CSV file'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='results/plots',
        help='Output directory for plots'
    )
    
    args = parser.parse_args()
    
    # Load data
    stats_file = Path(args.stats_file)
    if not stats_file.exists():
        print(f"❌ File not found: {stats_file}")
        sys.exit(1)
    
    print(f"📂 Loading data from: {stats_file}")
    stats = pd.read_csv(stats_file)
    
    # Also load raw data for boxplot
    raw_file = stats_file.parent / stats_file.name.replace('stats', 'raw')
    if raw_file.exists():
        print(f"📂 Loading raw data from: {raw_file}")
        raw_df = pd.read_csv(raw_file)
    else:
        print("⚠️  Raw data file not found, skipping boxplot")
        raw_df = None
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Generate plots
    print("\n📊 Generating visualizations...")
    
    if raw_df is not None:
        plot_success_rates_comparison(
            raw_df, 
            output_dir / 'success_rates_comparison.png'
        )
    else:
        print("⚠️  Skipping boxplot (raw data not available)")
    
    plot_kpi_breakdown(
        stats,
        output_dir / 'kpi_breakdown.png'
    )
    
    plot_correlation_heatmap(
        stats,
        output_dir / 'correlation_heatmap.png'
    )
    
    plot_scenario_sensitivity(
        stats,
        output_dir / 'scenario_sensitivity.png'
    )
    
    print(f"\n✅ All plots saved to: {output_dir.absolute()}")


if __name__ == '__main__':
    main()