#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Join tier CSV files into a single combined CSV.
"""

import sys
import csv
from pathlib import Path


# Domain shortcuts
DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}


def cmd_join(args):
    """Join tier CSV files into a single combined file"""
    module = args.module if hasattr(args, 'module') else None
    mode = args.mode if hasattr(args, 'mode') else None
    
    if not module or not mode:
        print("Error: Module and mode required")
        print("Usage: dp join <module> <mode>")
        print("Example: dp join mf decision")
        return 1
    
    # Resolve shortcuts
    module = DOMAIN_SHORTCUTS.get(module, module)
    
    # Find latest results directory
    base_results = Path('results') / module / mode
    latest_link = base_results / 'latest'
    
    if not latest_link.exists():
        print(f"Error: No results found for {module}/{mode}")
        print(f"Run 'dp run {module} {mode}' first")
        return 1
    
    results_dir = latest_link.resolve()
    
    # Find tier CSV files
    tier_files = {
        'basic': results_dir / f'{mode}_basic.csv',
        'advanced': results_dir / f'{mode}_advanced.csv',
        'excellence': results_dir / f'{mode}_excellence.csv',
    }
    
    # Check which files exist
    existing_tiers = {tier: path for tier, path in tier_files.items() if path.exists()}
    
    if not existing_tiers:
        print(f"Error: No tier CSV files found in {results_dir}")
        print("Expected files: decision_basic.csv, decision_advanced.csv, decision_excellence.csv")
        return 1
    
    print(f"📊 Joining tier CSVs for {module}/{mode}...")
    print(f"   Source: {results_dir}")
    print(f"   Found tiers: {', '.join(existing_tiers.keys())}")
    print()
    
    # Read all tier data
    tier_data = {}
    key_column = None  # Will be 'country' or similar
    
    for tier, path in existing_tiers.items():
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                continue
            
            # Detect key column (country, hour, route, etc.)
            if key_column is None:
                possible_keys = ['country', 'hour', 'route', 'scenario']
                for key in possible_keys:
                    if key in rows[0]:
                        key_column = key
                        break
            
            # Check if temporal data (has 'year' column) - simulation mode
            has_year = 'year' in rows[0]
            
            # Store by key (or composite key for simulation)
            if has_year:
                # Simulation: key by (country, year)
                tier_data[tier] = {(row[key_column], row['year']): row for row in rows}
            else:
                # Decision: key by country only
                tier_data[tier] = {row[key_column]: row for row in rows}
    
    if not tier_data or not key_column:
        print("Error: Could not parse tier CSV files")
        return 1
    
    # Get all unique keys
    all_keys = set()
    for tier_rows in tier_data.values():
        all_keys.update(tier_rows.keys())
    
    # Check if temporal (tuple keys)
    is_temporal = isinstance(next(iter(all_keys)), tuple) if all_keys else False

    # Build joined data    
    joined_rows = []
    
    for key in sorted(all_keys, key=lambda x: (int(x[0]), int(x[1])) if is_temporal else (int(x) if x.isdigit() else x)):
        if is_temporal:
            row = {key_column: key[0], 'year': key[1]}
        else:
            row = {key_column: key}
        
        # Add efficiency from each tier
        for tier in ['basic', 'advanced', 'excellence']:
            if tier in tier_data and key in tier_data[tier]:
                tier_row = tier_data[tier][key]
                
                # Add efficiency column for this tier
                eff_col = f'efficiency_{tier}'
                if eff_col in tier_row:
                    row[eff_col] = tier_row[eff_col]
                
                # Add composite for this tier
                comp_col = f'composite_{tier}'
                if comp_col in tier_row:
                    row[comp_col] = tier_row[comp_col]
                
                # Add shared columns (service, sustainability) only once
                if 'service' not in row and 'service' in tier_row:
                    row['service'] = tier_row['service']
                if 'sustainability' not in row and 'sustainability' in tier_row:
                    row['sustainability'] = tier_row['sustainability']
    
        joined_rows.append(row)
    
    # Write joined CSV
    output_file = results_dir / f'{mode}_joined.csv'
    
    if joined_rows:
        fieldnames = [key_column]
        if is_temporal:
            fieldnames.append('year')
        
        # Add tier efficiency columns
        for tier in ['basic', 'advanced', 'excellence']:
            if any(f'efficiency_{tier}' in row for row in joined_rows):
                fieldnames.append(f'efficiency_{tier}')
        
        # Add shared columns
        if any('service' in row for row in joined_rows):
            fieldnames.append('service')
        if any('sustainability' in row for row in joined_rows):
            fieldnames.append('sustainability')
        
        # Add tier composite columns
        for tier in ['basic', 'advanced', 'excellence']:
            if any(f'composite_{tier}' in row for row in joined_rows):
                fieldnames.append(f'composite_{tier}')
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(joined_rows)
        
        print(f"✓ Created joined CSV: {output_file.name}")
        print(f"  Rows: {len(joined_rows)}")
        print(f"  Columns: {', '.join(fieldnames)}")
        print()
        print(f"View with: cat {output_file}")
    else:
        print("Error: No data to join")
        return 1
    
    return 0


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Join tier CSV files into single combined CSV"
    )
    parser.add_argument("module", help="Module name (e.g., mf, lg)")
    parser.add_argument("mode", help="Mode (decision or simulation)")
    
    args = parser.parse_args()
    return cmd_join(args)


if __name__ == "__main__":
    sys.exit(main())