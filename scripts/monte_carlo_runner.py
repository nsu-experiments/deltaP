#!/usr/bin/env python3
"""
Simulation Driver for ΔP Logistics Examples
============================================

This script runs supply_chain_simulation.dp multiple times to generate
statistically valid results, then computes summary statistics.

Usage:
    python examples/run_logistics_simulation.py --iterations 100
    python examples/run_logistics_simulation.py --iterations 1000 --output results/
"""

import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import sys


class DeltaPSimulationRunner:
    """Manages multiple runs of a ΔP simulation program."""
    
    def __init__(self, dp_file: str, interpreter: str = "python3 interpreter.py"):
        self.dp_file = Path(dp_file)
        self.interpreter = interpreter
        self.results = []
        
        if not self.dp_file.exists():
            raise FileNotFoundError(f"ΔP file not found: {self.dp_file}")
    
    def run_single_iteration(self, iteration: int) -> dict:
        """Run the ΔP interpreter once and parse CSV output."""
        try:
            # Run the interpreter
            result = subprocess.run(
                f"{self.interpreter} {self.dp_file}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"⚠️  Iteration {iteration} failed: {result.stderr}")
                return None
            
            # Parse CSV output from stdout
            output_lines = result.stdout.strip().split('\n')
            csv_data = []
            
            in_csv_section = False
            for line in output_lines:
                # Detect CSV header
                if 'iteration,route' in line.lower():
                    in_csv_section = True
                    continue  # Skip the header itself
                
                # Once in CSV section, collect data lines
                if in_csv_section and ',' in line and line.strip():
                    # Stop if we hit a non-CSV line (like "=== Testing...")
                    if '===' in line or 'Result:' in line:
                        break
                    csv_data.append(line)
            if not csv_data:
                print(f"⚠️  Iteration {iteration}: No CSV data found")
                return None
            
            # Parse the CSV lines
            iteration_results = []
            for line in csv_data:
                parts = line.split(',')
                if len(parts) >= 4:
                    try:
                        iteration_results.append({
                            'iteration': iteration,
                            'route': parts[1].strip(),
                            'scenario': int(parts[2].strip()),
                            'month': int(parts[3].strip()),
                            'meets_efficiency': float(parts[4].strip()),
                            'meets_service': float(parts[5].strip()),
                            'meets_carbon': float(parts[6].strip()),
                            'composite_success': float(parts[7].strip())
                        })
                    except (ValueError, IndexError) as e:
                        print(f"⚠️  Parse error in iteration {iteration}: {e}")
                        continue
            
            return iteration_results
            
        except subprocess.TimeoutExpired:
            print(f"⚠️  Iteration {iteration} timed out")
            return None
        except Exception as e:
            print(f"⚠️  Iteration {iteration} error: {e}")
            return None
    
    def run_multiple_iterations(self, n_iterations: int, verbose: bool = True):
        """Run simulation n times and collect results."""
        print(f"🚀 Starting {n_iterations} simulation iterations...")
        print(f"📄 Program: {self.dp_file}")
        print()
        
        successful_runs = 0
        
        for i in range(1, n_iterations + 1):
            if verbose and i % 10 == 0:
                print(f"Progress: {i}/{n_iterations} iterations ({i/n_iterations*100:.0f}%)")
            
            iteration_data = self.run_single_iteration(i)
            if iteration_data:
                self.results.extend(iteration_data)
                successful_runs += 1
        
        print(f"\n✅ Completed {successful_runs}/{n_iterations} successful runs")
        print(f"📊 Total data points: {len(self.results)}")
        
        if successful_runs == 0:
            raise RuntimeError("No successful iterations - check interpreter path and DP file")
        
        return pd.DataFrame(self.results)


class StatisticalAnalyzer:
    """Computes statistics and generates reports from simulation data."""
    
    @staticmethod
    def compute_statistics(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate mean, std, confidence intervals for each route/scenario."""
        
        # Group by route and scenario
        grouped = df.groupby(['route', 'scenario'])
        
        stats = grouped.agg({
            'composite_success': ['mean', 'std', 'count'],
            'meets_efficiency': 'mean',
            'meets_service': 'mean',
            'meets_carbon': 'mean'
        }).reset_index()
        
        # Flatten column names
        stats.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                        for col in stats.columns.values]
        
        # Rename for clarity
        stats.rename(columns={
            'composite_success_mean': 'success_rate',
            'composite_success_std': 'std_dev',
            'composite_success_count': 'n_samples',
            'meets_efficiency_mean': 'efficiency_rate',
            'meets_service_mean': 'service_rate',
            'meets_carbon_mean': 'carbon_rate'
        }, inplace=True)
        
        # Calculate 95% confidence intervals
        stats['ci_lower'] = stats['success_rate'] - 1.96 * (
            stats['std_dev'] / np.sqrt(stats['n_samples'])
        )
        stats['ci_upper'] = stats['success_rate'] + 1.96 * (
            stats['std_dev'] / np.sqrt(stats['n_samples'])
        )
        
        # Clamp CI to [0, 1]
        stats['ci_lower'] = stats['ci_lower'].clip(0, 1)
        stats['ci_upper'] = stats['ci_upper'].clip(0, 1)
        
        return stats
    
    @staticmethod
    def generate_report(stats: pd.DataFrame, output_path: Path):
        """Generate a human-readable text report."""
        
        route_names = {
            '1': 'Kazakhstan (R1)',
            '2': 'Kyrgyzstan (R2)', 
            '3': 'Hybrid (R3)',
            'Kazakhstan': 'Kazakhstan (R1)',
            'Kyrgyzstan': 'Kyrgyzstan (R2)',
            'Hybrid': 'Hybrid (R3)'
        }
        
        scenario_names = {
            1: 'Baseline',
            2: 'Carbon Strict',
            3: 'Border Tight',
            4: 'Carbon & Border'
        }
        
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("Russian-Chinese Bioethanol Logistics - Simulation Results\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total iterations: {stats['n_samples'].iloc[0]}\n")
            f.write("\n")
            
            for scenario_id in sorted(stats['scenario'].unique()):
                scenario_data = stats[stats['scenario'] == scenario_id]
                scenario_name = scenario_names.get(scenario_id, f"Scenario {scenario_id}")
                
                f.write(f"\n{'='*80}\n")
                f.write(f"SCENARIO: {scenario_name}\n")
                f.write(f"{'='*80}\n\n")
                
                for _, row in scenario_data.iterrows():
                    route_name = route_names.get(str(row['route']), row['route'])
                    
                    f.write(f"--- {route_name} ---\n")
                    f.write(f"  Success Rate:       {row['success_rate']:.3f}\n")
                    f.write(f"  Std Deviation:      {row['std_dev']:.3f}\n")
                    f.write(f"  95% CI:             [{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]\n")
                    f.write(f"  Sample Size:        {int(row['n_samples'])}\n")
                    f.write(f"\n")
                    f.write(f"  Component Rates:\n")
                    f.write(f"    Efficiency:       {row['efficiency_rate']:.3f}\n")
                    f.write(f"    Service Quality:  {row['service_rate']:.3f}\n")
                    f.write(f"    Carbon Limit:     {row['carbon_rate']:.3f}\n")
                    f.write(f"\n")
                
                # Route ranking for this scenario
                scenario_sorted = scenario_data.sort_values('success_rate', ascending=False)
                f.write(f"Route Ranking (by success rate):\n")
                for rank, (_, row) in enumerate(scenario_sorted.iterrows(), 1):
                    route_name = route_names.get(str(row['route']), row['route'])
                    f.write(f"  {rank}. {route_name}: {row['success_rate']:.3f}\n")
                f.write("\n")
        
        print(f"📝 Report saved to: {output_path}")
    
    @staticmethod
    def generate_csv(df: pd.DataFrame, stats: pd.DataFrame, output_dir: Path):
        """Save raw data and statistics to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Raw simulation data
        raw_file = output_dir / f"simulation_raw_{timestamp}.csv"
        df.to_csv(raw_file, index=False)
        print(f"💾 Raw data saved to: {raw_file}")
        
        # Statistical summary
        stats_file = output_dir / f"simulation_stats_{timestamp}.csv"
        stats.to_csv(stats_file, index=False)
        print(f"📊 Statistics saved to: {stats_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Run ΔP logistics simulation with statistical analysis'
    )
    parser.add_argument(
        '--iterations', '-n',
        type=int,
        default=100,
        help='Number of simulation iterations (default: 100)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='results',
        help='Output directory for results (default: results/)'
    )
    parser.add_argument(
        '--dp-file',
        type=str,
        default='supply_chain_simulation.dp',
        help='Path to ΔP simulation file'
    )
    parser.add_argument(
        '--interpreter',
        type=str,
        default='python3 -m interpreter',
        help='Command to run ΔP interpreter'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Run simulations
        runner = DeltaPSimulationRunner(args.dp_file, args.interpreter)
        df = runner.run_multiple_iterations(args.iterations, verbose=not args.quiet)
        
        if df.empty:
            print("❌ No data collected. Check your ΔP program output format.")
            sys.exit(1)
        
        # Compute statistics
        print("\n📈 Computing statistics...")
        stats = StatisticalAnalyzer.compute_statistics(df)
        
        # Generate outputs
        print("\n💾 Generating outputs...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_dir / f"simulation_report_{timestamp}.txt"
        
        StatisticalAnalyzer.generate_report(stats, report_file)
        StatisticalAnalyzer.generate_csv(df, stats, output_dir)
        
        print("\n✅ Analysis complete!")
        print(f"\n📁 All files saved to: {output_dir.absolute()}")
        
        # Print quick summary to console
        print("\n" + "="*80)
        print("QUICK SUMMARY (Baseline Scenario)")
        print("="*80)
        baseline = stats[stats['scenario'] == 1].sort_values('success_rate', ascending=False)
        for _, row in baseline.iterrows():
            print(f"{row['route']:15s} Success: {row['success_rate']:.3f} "
                  f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    main()