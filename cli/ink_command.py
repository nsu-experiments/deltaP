# cli/ink_command.py
"""
ΔP visualization command (dp ink)
Generate charts from simulation results.
"""

import sys
from pathlib import Path
import tomli
import pandas as pd
from typing import Optional, Dict, Any
import matplotlib.pyplot as plt

DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}


def load_visualize_config(module_path: Path) -> Dict[str, Any]:
    """Load visualize.toml config for module."""
    config_path = module_path / "visualize.toml"
    
    if not config_path.exists():
        return {}
    
    with open(config_path, 'rb') as f:
        return tomli.load(f)


def find_latest_results(module_name: str, result_type: str = 'stats') -> Optional[Path]:
    """Find the most recent results CSV file."""
    results_dir = Path('results') / module_name
    
    if not results_dir.exists():
        return None
    
    # Use 'latest' symlink
    latest_link = results_dir / 'latest'
    if latest_link.exists():
        latest_dir = latest_link
    else:
        timestamped_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name != 'latest']
        if not timestamped_dirs:
            return None
        latest_dir = max(timestamped_dirs, key=lambda p: p.name)
    
    # Match actual pattern: {mode}_results_{timestamp}.csv
    if result_type == 'stats':
        pattern = "*_results_*.csv"  # Match any mode
    else:
        pattern = f"*{result_type}*.csv"
    
    csv_files = list(latest_dir.glob(pattern))
    
    return csv_files[0] if csv_files else None

def generate_charts(
    module_name: str,
    config: Dict[str, Any],
    stats_path: Path,
    raw_path: Optional[Path] = None
):
    """
    Generate charts based on config and available data.
    
    Args:
        module_name: Name of the module
        config: Loaded visualize.toml config
        stats_path: Path to stats CSV
        raw_path: Optional path to raw CSV
    """
    # Import visualization modules
    scripts_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))    
    from visualization import loaders, charts
    
    print(f"📊 Generating visualizations for '{module_name}'...")
    
    # Load data
    stats_df, _ = loaders.load_csv_with_metadata(stats_path)
    raw_df = None
    if raw_path and raw_path.exists():
        raw_df, _ = loaders.load_csv_with_metadata(raw_path)
    
    # Get output settings
    output_config = config.get('output', {})
    output_dir = Path(output_config.get('directory', 'results/plots'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get enabled charts
    enabled_charts = config.get('charts', {}).get('enabled', ['comparison'])
    
    chart_count = 0
    
    # Generate simple bar chart instead of comparison with CI
    if 'comparison' in enabled_charts:
        comp_config = config.get('charts', {}).get('comparison', {})
        
        # Aggregate by route
        route_stats = stats_df.groupby('route')['composite'].mean().reset_index()
        
        # Get route names from config and convert keys to int
        route_names = comp_config.get('route_names', {})
        # Convert string keys to int if needed
        route_names_int = {int(k) if isinstance(k, str) else k: v for k, v in route_names.items()}
        if not route_names_int:
            route_names_int = {1: 'Route 1', 2: 'Route 2', 3: 'Route 3'}
        
        route_stats['route_name'] = route_stats['route'].map(route_names_int)
        
        fig = charts.primitives.bar.bar_chart(
            route_stats,
            x_col='route_name',
            y_col='composite',
            title='Average Composite Success by Route',
            xlabel='Route',
            ylabel='Average Success Score',
            colors=['#4CAF50', '#F44336', '#2196F3']
        )
        fig.savefig(output_dir / 'route_comparison.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        chart_count += 1
    
    # Generate KPI breakdown
    if 'kpi_breakdown' in enabled_charts:
        kpi_config = config.get('charts', {}).get('kpi_breakdown', {})
        fig = charts.composed.comparison.kpi_breakdown(
            stats_df,
            route_col=kpi_config.get('route_col', 'route'),
            scenario_col=kpi_config.get('scenario_col', 'scenario'),
            kpi_cols=kpi_config.get('kpi_cols'),
            kpi_labels=kpi_config.get('kpi_labels'),
            route_names=kpi_config.get('route_names'),
            baseline_scenario=kpi_config.get('baseline_scenario', 1),
            output_path=output_dir / 'kpi_breakdown.png'
        )
        chart_count += 1
    
    # Generate scenario sensitivity
    if 'scenario_sensitivity' in enabled_charts:
        sens_config = config.get('charts', {}).get('scenario_sensitivity', {})
        fig = charts.composed.comparison.scenario_sensitivity(
            stats_df,
            route_col=sens_config.get('route_col', 'route'),
            scenario_col=sens_config.get('scenario_col', 'scenario'),
            success_col=sens_config.get('success_col', 'success_rate'),
            ci_lower_col='ci_lower',
            ci_upper_col='ci_upper',
            route_names=sens_config.get('route_names'),
            scenario_names=sens_config.get('scenario_names'),
            output_path=output_dir / 'scenario_sensitivity.png'
        )
        chart_count += 1
    
    # Generate EDA report if enabled
    if config.get('charts', {}).get('eda', {}).get('enabled', False):
        eda_config = config.get('charts', {}).get('eda', {})
        charts.composed.eda.full_eda_report(
            raw_df if raw_df is not None else stats_df,
            value_cols=eda_config.get('value_cols', []),
            category_col=eda_config.get('category_col'),
            output_dir=output_dir / 'eda'
        )
        chart_count += 5  # EDA generates multiple charts
    
    print(f"✅ Generated {chart_count} chart(s) in {output_dir.absolute()}")


def cmd_ink(args):
    """Main logic for dp ink command."""
    module_name = args.module_name
    
    # Resolve domain shortcuts
    module_name = DOMAIN_SHORTCUTS.get(module_name, module_name)

    # Load config from src/{module_name}/visualize.toml
    config_path = Path("src") / module_name / "visualize.toml"
    
    if config_path.exists():
        with open(config_path, 'rb') as f:
            config = tomli.load(f)
    else:
        print(f"⚠️  No visualize.toml found for '{module_name}'")
        print("   Using default settings...")
        config = {
            'charts': {'enabled': ['comparison']},
            'output': {}
        }
    
    # Override with CLI flags
    if args.eda:
        config.setdefault('charts', {}).setdefault('eda', {})['enabled'] = True
    
    # Find latest results directory
    results_base = Path('results') / module_name
    latest_link = results_base / 'latest'
    
    if not latest_link.exists():
        print(f"❌ No results found for '{module_name}'")
        print(f"   Run 'dp run {module_name}' first")
        return 1
    
    latest_dir = latest_link
    
    # Look for both simulation and decision CSV files
    sim_stats = list(latest_dir.glob('simulation_results_*.csv'))
    sim_raw = list(latest_dir.glob('simulation_raw_*.csv'))
    dec_stats = list(latest_dir.glob('decision_results_*.csv'))
    
    if not sim_stats and not dec_stats:
        print(f"❌ No CSV results found in {latest_dir}")
        print(f"   Expected simulation_results_*.csv or decision_results_*.csv")
        return 1
    
    # Set output directory to same timestamped folder as results
    if not args.output:
        output_dir = latest_dir
    else:
        output_dir = Path(args.output)
    
    config.setdefault('output', {})['directory'] = str(output_dir)
    
    # Generate charts for available modes
    chart_count = 0
    
    if sim_stats:
        print(f"\n{'='*60}")
        print(f"📊 Generating simulation visualizations...")
        print(f"{'='*60}")
        print(f"📂 Using results:")
        print(f"   Stats: {sim_stats[0]}")
        if sim_raw:
            print(f"   Raw:   {sim_raw[0]}")
        
        try:
            generate_charts(
                module_name, 
                config, 
                sim_stats[0], 
                sim_raw[0] if sim_raw else None
            )
            chart_count += 1
        except Exception as e:
            print(f"❌ Error generating simulation charts: {e}")
            import traceback
            traceback.print_exc()
    
    if dec_stats:
        print(f"\n{'='*60}")
        print(f"📊 Generating decision visualizations...")
        print(f"{'='*60}")
        print(f"📂 Using results:")
        print(f"   Stats: {dec_stats[0]}")
        
        try:
            generate_charts(module_name, config, dec_stats[0], None)
            chart_count += 1
        except Exception as e:
            print(f"❌ Error generating decision charts: {e}")
            import traceback
            traceback.print_exc()
    
    if chart_count > 0:
        print(f"\n{'='*60}")
        print(f"✅ Generated visualizations in: {output_dir}")
        print(f"{'='*60}")
        return 0
    else:
        return 1
    
def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualizations from simulation results")
    parser.add_argument('module_name', help='Name of the module')
    parser.add_argument('--eda', action='store_true', help='Enable full EDA report')
    parser.add_argument('--output', help='Output directory (default: results/plots)')
    
    args = parser.parse_args()
    return cmd_ink(args)


if __name__ == "__main__":
    sys.exit(main())