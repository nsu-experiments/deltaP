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
    results_dir = Path('src') / 'results' / module_name  # CHANGED
    
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
    csv_path: Path
):
    """Generate charts based on config and available data."""
    # Import visualization modules
    scripts_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))
    
    # Import primitives
    from visualization.charts.primitives import bar, line  # type: ignore

    
    print(f"📊 Generating visualizations for '{module_name}'...")
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} rows, columns: {list(df.columns)}")
    
    # Get output settings
    output_config = config.get('output', {})
    output_dir = Path(output_config.get('directory', 'results/plots'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get enabled charts
    enabled_charts = config.get('charts', {}).get('enabled', [])
    print(f"  Enabled charts: {enabled_charts}")
    
    chart_count = 0
    
    # LOGISTICS: Risk comparison
    if 'risk_comparison' in enabled_charts:
        risk_config = config.get('charts', {}).get('risk_comparison', {})
        risk_col = risk_config.get('risk_col', 'risk')
        perf_col = risk_config.get('performance_col', 'composite')
        
        if risk_col in df.columns and perf_col in df.columns:
            # Aggregate by risk level
            risk_stats = df.groupby(risk_col)[perf_col].mean().reset_index()
            
            # Get risk names
            risk_names = risk_config.get('risk_names', {1: 'Low', 2: 'Moderate', 3: 'High'})
            risk_names_int = {int(k): v for k, v in risk_names.items()}
            risk_stats['risk_name'] = risk_stats[risk_col].map(risk_names_int)
            
            fig = bar.bar_chart(
                df=risk_stats,
                x_col='risk_name',
                y_col=perf_col,
                title='Performance by Risk Level',
                xlabel='Risk Level',
                ylabel='Average Performance',
                colors=['#4CAF50', '#FF9800', '#F44336']
            )
            fig.savefig(output_dir / 'risk_comparison.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
            chart_count += 1
            print(f"  ✓ risk_comparison.png")
        else:
            print(f"  ⚠️  Skipping risk_comparison: missing columns {risk_col} or {perf_col}")
    
    # LOGISTICS: Hourly performance
    if 'hourly_performance' in enabled_charts:
        hourly_config = config.get('charts', {}).get('hourly_performance', {})
        hour_col = hourly_config.get('hour_col', 'hour')
        perf_cols = hourly_config.get('performance_cols', ['on_time', 'fuel', 'cargo'])
        
        # Filter to only columns that exist
        available_cols = [col for col in perf_cols if col in df.columns]
        
        if hour_col in df.columns and available_cols:
            # Aggregate by hour
            hourly_stats = df.groupby(hour_col)[available_cols].mean().reset_index()
            
            fig = line.multi_line(
                df=hourly_stats,
                x_col=hour_col,
                y_cols=available_cols,
                title='24-Hour Performance Profile',
                xlabel='Hour of Day',
                ylabel='Performance',
                labels=hourly_config.get('performance_labels', available_cols),
                colors=['#2196F3', '#4CAF50', '#F44336', '#FF9800']
            )
            fig.savefig(output_dir / 'hourly_performance.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
            chart_count += 1
            print(f"  ✓ hourly_performance.png")
        else:
            print(f"  ⚠️  Skipping hourly_performance: missing columns")
    
    # MANUFACTURING: Comparison chart
    if 'comparison' in enabled_charts:
        comp_config = config.get('charts', {}).get('comparison', {})
        
        # Try 'country' first (manufacturing), fallback to 'route'
        group_col = 'country' if 'country' in df.columns else comp_config.get('route_col', 'route')
        success_col = comp_config.get('success_col', 'composite')
        
        if group_col in df.columns and success_col in df.columns:
            # Aggregate
            stats = df.groupby(group_col)[success_col].mean().reset_index()
            
            # Get names
            route_names = comp_config.get('route_names', {})
            route_names_int = {int(k): v for k, v in route_names.items()}
            
            if route_names_int:
                stats['name'] = stats[group_col].map(route_names_int)
                x_col = 'name'
            else:
                x_col = group_col
            
            fig = bar.bar_chart(
                df=stats,
                x_col=x_col,
                y_col=success_col,
                title='Average Composite Success',
                xlabel='Route' if group_col == 'route' else 'Country',
                ylabel='Average Success Score',
                colors=['#4CAF50', '#F44336', '#2196F3', '#FF9800', '#9C27B0']
            )
            fig.savefig(output_dir / 'comparison.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
            chart_count += 1
            print(f"  ✓ comparison.png")
        else:
            print(f"  ⚠️  Skipping comparison: missing columns")
    
    if chart_count == 0:
        print(f"  ⚠️  No charts generated - check config and CSV columns")
    else:
        print(f"✅ Generated {chart_count} chart(s) in {output_dir.absolute()}")
def cmd_ink(args):
    """Main logic for dp ink command."""
    module_name = args.module_name
    mode = getattr(args, 'mode', None)  # 'decision' or 'simulation'
    
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
    
    # Determine which mode to visualize
    if not mode:
        # Ask user to select mode
        print(f"\nSelect mode to visualize:")
        print("  1. Decision")
        print("  2. Simulation")
        print("  3. Both")
        choice = input("Choice [1]: ").strip() or "1"
        
        if choice == "1":
            modes = ['decision']
        elif choice == "2":
            modes = ['simulation']
        elif choice == "3":
            modes = ['decision', 'simulation']
        else:
            print("Invalid choice")
            return 1
    else:
        modes = [mode]
    
    # Process each mode
    total_charts = 0
    
    for current_mode in modes:
        # Find results directory for this mode
        results_base = Path('results') / module_name / current_mode
        
        if not results_base.exists():
            print(f"❌ No {current_mode} results found for '{module_name}'")
            print(f"   Expected: {results_base}")
            print(f"   Run 'dp run {module_name} {current_mode}' first")
            continue
        
        # List available timestamped folders
        timestamped_dirs = [d for d in results_base.iterdir() 
                           if d.is_dir() and d.name != 'latest' and not d.name.startswith('.')]
        
        if not timestamped_dirs:
            print(f"❌ No timestamped results found in {results_base}")
            continue
        
        # Sort by timestamp (newest first)
        timestamped_dirs.sort(reverse=True)
        
        # Check if 'latest' symlink exists
        latest_link = results_base / 'latest'
        
        if latest_link.exists():
            selected_dir = latest_link.resolve()
            print(f"\n📊 Using latest {current_mode} results: {selected_dir.name}")
        else:
            # Show selection menu
            print(f"\n📂 Available {current_mode} results:")
            for i, d in enumerate(timestamped_dirs[:10], 1):  # Show max 10
                print(f"  {i}. {d.name}")
            
            if len(timestamped_dirs) > 10:
                print(f"  ... and {len(timestamped_dirs) - 10} more")
            
            choice = input(f"\nSelect result [1]: ").strip() or "1"
            
            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(timestamped_dirs):
                    print("Invalid selection")
                    continue
                selected_dir = timestamped_dirs[idx]
            except ValueError:
                print("Invalid input")
                continue
        
        # Find CSV file in selected directory
        csv_files = list(selected_dir.glob(f'{current_mode}_results*.csv'))
        
        if not csv_files:
            print(f"❌ No CSV results found in {selected_dir}")
            print(f"   Expected: {current_mode}_results*.csv")
            continue
        
        csv_path = csv_files[0]
        
        # Set output directory to plots subfolder in same timestamped folder
        output_dir = selected_dir
        output_dir.mkdir(exist_ok=True)
        
        config.setdefault('output', {})['directory'] = str(output_dir)
        
        print(f"\n{'='*60}")
        print(f"📊 Generating {current_mode} visualizations...")
        print(f"{'='*60}")
        print(f"📂 Input:  {csv_path}")
        print(f"📂 Output: {output_dir}")
        print()
        
        try:
            generate_charts(module_name, config, csv_path)
            total_charts += 1
        except Exception as e:
            print(f"❌ Error generating {current_mode} charts: {e}")
            import traceback
            traceback.print_exc()
    
    if total_charts > 0:
        print(f"\n{'='*60}")
        print(f"✅ Generated visualizations for {total_charts} mode(s)")
        print(f"{'='*60}")
        return 0
    else:
        return 1


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualizations from simulation results")
    parser.add_argument('module_name', help='Name of the module (or domain shortcut: lg, mf, etc.)')
    parser.add_argument('mode', nargs='?', choices=['decision', 'simulation', 'd', 's'], 
                       help='Mode to visualize (optional, will prompt if omitted)')
    parser.add_argument('--eda', action='store_true', help='Enable full EDA report')
    
    args = parser.parse_args()
    
    # Resolve mode shortcuts
    if args.mode:
        args.mode = 'decision' if args.mode == 'd' else 'simulation' if args.mode == 's' else args.mode
    
    return cmd_ink(args)


if __name__ == "__main__":
    sys.exit(main())