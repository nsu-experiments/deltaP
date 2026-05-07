#!/usr/bin/env python3
"""
Consistency Validator for ΔP Simulation and Decision Modes
==========================================================

Compares results from simulation mode (stochastic sampling) with
decision mode (probability computation) to ensure they agree within
statistical tolerance.

Usage:
    python validate_consistency.py \
        --simulation results/simulation_stats_*.csv \
        --decision results/decision_output.txt
"""

import pandas as pd
import argparse
import re
from pathlib import Path
import sys


def parse_decision_output(decision_file: Path) -> pd.DataFrame:
    """Parse the text output from logistics_decision.dp."""
    
    with open(decision_file, 'r') as f:
        content = f.read()
    
    # Look for CSV section in decision output
    csv_pattern = r'route_id,route_name,scenario.*?\n((?:\d+,.*?\n)+)'
    matches = re.findall(csv_pattern, content, re.MULTILINE)
    
    if not matches:
        print("⚠️  No CSV data found in decision output")
        return pd.DataFrame()
    
    # Parse the CSV content
    csv_lines = []
    for match in matches:
        csv_lines.extend(match.strip().split('\n'))
    
    if not csv_lines:
        return pd.DataFrame()
    
    # Parse into DataFrame
    rows = []
    for line in csv_lines:
        parts = line.split(',')
        if len(parts) >= 10:
            try:
                rows.append({
                    'route_id': int(parts[0]),
                    'route_name': parts[1],
                    'scenario': parts[2],
                    'weight_scheme': parts[3],
                    'prob_efficiency': float(parts[4]),
                    'prob_service': float(parts[5]),
                    'prob_carbon': float(parts[6]),
                    'composite_score': float(parts[9])
                })
            except (ValueError, IndexError):
                continue
    
    return pd.DataFrame(rows)


def compare_results(sim_stats: pd.DataFrame, decision_df: pd.DataFrame, 
                   tolerance: float = 0.15) -> dict:
    """
    Compare simulation and decision mode results.
    
    Returns dict with validation results.
    """
    
    results = {
        'passed': True,
        'comparisons': [],
        'warnings': []
    }
    
    route_map = {
        1: 'Kazakhstan',
        2: 'Kyrgyzstan',
        3: 'Hybrid',
        'Kazakhstan': 'Kazakhstan',
        'Kyrgyzstan': 'Kyrgyzstan',
        'Hybrid': 'Hybrid'
    }
    
    scenario_map = {
        1: 'baseline',
        'baseline': 'baseline',
        3: 'border_tight',
        'border_tight': 'border_tight'
    }
    
    # Normalize names
    sim_stats['route_normalized'] = sim_stats['route'].map(
        lambda x: route_map.get(x, route_map.get(str(x), str(x)))
    )
    sim_stats['scenario_normalized'] = sim_stats['scenario'].map(
        lambda x: scenario_map.get(x, str(x))
    )
    
    # Compare each route/scenario combination
    for _, dec_row in decision_df.iterrows():
        route_name = dec_row['route_name']
        scenario = dec_row['scenario']
        
        # Find matching simulation data
        sim_match = sim_stats[
            (sim_stats['route_normalized'] == route_name) &
            (sim_stats['scenario_normalized'] == scenario)
        ]
        
        if sim_match.empty:
            results['warnings'].append(
                f"No simulation data for {route_name}/{scenario}"
            )
            continue
        
        sim_row = sim_match.iloc[0]
        
        # Compare success rates
        sim_rate = sim_row['success_rate']
        dec_score = dec_row['composite_score']
        delta = abs(sim_rate - dec_score)
        
        comparison = {
            'route': route_name,
            'scenario': scenario,
            'simulation_rate': sim_rate,
            'decision_score': dec_score,
            'delta': delta,
            'within_tolerance': delta <= tolerance,
            'ci_lower': sim_row['ci_lower'],
            'ci_upper': sim_row['ci_upper']
        }
        
        results['comparisons'].append(comparison)
        
        if delta > tolerance:
            results['passed'] = False
            results['warnings'].append(
                f"{route_name}/{scenario}: Large discrepancy (Δ={delta:.3f})"
            )
    
    return results


def print_validation_report(results: dict, output_file: Path = None):
    """Print (and optionally save) validation report."""
    
    lines = []
    
    lines.append("=" * 80)
    lines.append("ΔP Simulation vs Decision Mode - Consistency Validation")
    lines.append("=" * 80)
    lines.append("")
    
    if results['passed']:
        lines.append("✅ VALIDATION PASSED")
    else:
        lines.append("❌ VALIDATION FAILED")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("Detailed Comparisons")
    lines.append("=" * 80)
    lines.append("")
    
    for comp in results['comparisons']:
        lines.append(f"Route: {comp['route']}, Scenario: {comp['scenario']}")
        lines.append(f"  Simulation:    {comp['simulation_rate']:.3f} "
                    f"[{comp['ci_lower']:.3f}, {comp['ci_upper']:.3f}]")
        lines.append(f"  Decision:      {comp['decision_score']:.3f}")
        lines.append(f"  Delta:         {comp['delta']:.3f}")
        
        if comp['within_tolerance']:
            lines.append(f"  Status:        ✅ Within tolerance")
        else:
            lines.append(f"  Status:        ❌ Exceeds tolerance")
        
        lines.append("")
    
    if results['warnings']:
        lines.append("=" * 80)
        lines.append("Warnings")
        lines.append("=" * 80)
        lines.append("")
        for warning in results['warnings']:
            lines.append(f"⚠️  {warning}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("Summary")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total comparisons: {len(results['comparisons'])}")
    
    passed = sum(1 for c in results['comparisons'] if c['within_tolerance'])
    lines.append(f"Passed: {passed}/{len(results['comparisons'])}")
    
    avg_delta = sum(c['delta'] for c in results['comparisons']) / len(results['comparisons'])
    lines.append(f"Average delta: {avg_delta:.3f}")
    lines.append("")
    
    # Print to console
    report = "\n".join(lines)
    print(report)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate consistency between simulation and decision modes'
    )
    parser.add_argument(
        '--simulation',
        required=True,
        help='Path to simulation statistics CSV'
    )
    parser.add_argument(
        '--decision',
        required=True,
        help='Path to decision mode output text file'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=0.15,
        help='Maximum acceptable difference (default: 0.15)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save validation report to file'
    )
    
    args = parser.parse_args()
    
    # Load data
    sim_file = Path(args.simulation)
    dec_file = Path(args.decision)
    
    if not sim_file.exists():
        print(f"❌ Simulation file not found: {sim_file}")
        sys.exit(1)
    
    if not dec_file.exists():
        print(f"❌ Decision file not found: {dec_file}")
        sys.exit(1)
    
    print(f"📂 Loading simulation data from: {sim_file}")
    sim_stats = pd.read_csv(sim_file)
    
    print(f"📂 Loading decision data from: {dec_file}")
    decision_df = parse_decision_output(dec_file)
    
    if decision_df.empty:
        print("❌ Could not parse decision output")
        sys.exit(1)
    
    print(f"\n📊 Found {len(sim_stats)} simulation entries")
    print(f"📊 Found {len(decision_df)} decision entries")
    print("")
    
    # Perform comparison
    results = compare_results(sim_stats, decision_df, args.tolerance)
    
    # Print report
    output_path = Path(args.output) if args.output else None
    print_validation_report(results, output_path)
    
    # Exit with appropriate code
    sys.exit(0 if results['passed'] else 1)


if __name__ == '__main__':
    main()