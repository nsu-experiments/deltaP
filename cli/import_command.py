#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import real datasets into ΔP HDF5 database.
Refactored from sync_command.py to handle external CSV data.
"""

import sys
import csv
import json
from pathlib import Path


# Domain shortcuts
DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}


def parse_dp_config(config_path: Path) -> dict:
    """Parse config.dp to extract mappings and thresholds."""
    config = {
        'route_names': {},
        'country_map': {},
        'thresholds': {},
        'domains': {},
        'constants': {}
    }
    
    if not config_path.exists():
        return config
    
    import re
    
    with open(config_path) as f:
        for line in f:
            line = line.split('//')[0].strip()
            
            # Match: r1 := 1;
            route_match = re.match(r'(r\d+)\s*:=\s*(\d+);', line)
            if route_match:
                name, val = route_match.groups()
                config['route_names'][int(val)] = name
            
            # Match: usa := 1; china := 2; etc. (FIXED INDENTATION)
            country_match = re.match(r'(usa|china|germany|india|brazil)\s*:=\s*(\d+);', line, re.IGNORECASE)
            if country_match:  # ADD THIS CHECK
                name, val = country_match.groups()
                # Store both capitalized and uppercase
                config['country_map'][name.capitalize()] = int(val)
                config['country_map'][name.upper()] = int(val)
            
            # Match: theta_high := 0.7; or threshold := 0.7;
            threshold_match = re.match(r'(theta_\w+|threshold)\s*:=\s*([\d.]+);', line)
            if threshold_match:
                name, val = threshold_match.groups()
                config['thresholds'][name] = float(val)
            
            # Match any constant: name := value;
            const_match = re.match(r'(\w+)\s*:=\s*([\d.]+);', line)
            if const_match:
                name, val = const_match.groups()
                config['constants'][name] = float(val)
    
    return config

def map_csv_to_predicates(csv_path: Path, module: str, verbose=False) -> dict:
    """Generic CSV to ΔP predicates mapper."""
    import csv
    from datetime import datetime
    
    # Load module config
    config_path = Path('src') / module / 'config.dp'
    dp_config = parse_dp_config(config_path)
    
    predicates = {}
    
    # Domain-specific argument columns
    if module == 'logistics':
        # Supply chain: will extract hour from timestamp, categorize weather/traffic/risk
        argument_columns = ['timestamp', 'weather_condition_severity', 'traffic_congestion_level', 'risk_classification']
    elif module == 'manufacturing':
        argument_columns = ['Year', 'Country', 'Govt_Incentive']
    else:
        # Generic fallback
        argument_columns = ['Year', 'Country', 'Govt_Incentive', 'Scenario', 'Month', 'Route']
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        
        # Classify columns
        arg_column_names = []
        value_column_mappings = {}
        
        for col in headers:
            if col in argument_columns:
                arg_column_names.append(col)
            else:
                pred_name = column_to_predicate_name(col, module)
                if pred_name:  # Only add if mapping exists
                    value_column_mappings[col] = pred_name
                    predicates[pred_name] = []

                    if module == 'manufacturing' and pred_name == 'meets_efficiency':
                        predicates['meets_efficiency_basic'] = []
                        predicates['meets_efficiency_advanced'] = []
                        predicates['meets_efficiency_excellence'] = []
        
        if verbose:
            print(f"    Detected argument columns: {arg_column_names}")
            print(f"    Detected value columns → predicates:")
            for csv_col, pred_name in value_column_mappings.items():
                print(f"      {csv_col} → {pred_name}")
            print(f"    Thresholds from config.dp: {dp_config['thresholds']}")
        
        # Get thresholds
        if module == 'logistics':
            delay_threshold = dp_config['thresholds'].get('theta_delay', 0.5)
            fuel_threshold = dp_config['thresholds'].get('theta_fuel', 7.0)
            delivery_deviation_threshold = dp_config['thresholds'].get('theta_delivery_deviation', 5.0)
        else:
            default_threshold = dp_config['thresholds'].get('theta_high', 0.7)
            sustainability_threshold = dp_config['thresholds'].get('theta_sustainability', 5.0)
            demand_threshold = dp_config['thresholds'].get('theta_demand', 120.0)
            capacity_threshold = dp_config['thresholds'].get('theta_capacity', 150.0)

            basic_threshold = dp_config['thresholds'].get('theta_basic', 0.7)
            advanced_threshold = dp_config['thresholds'].get('theta_advanced', 0.8)
            excellence_threshold = dp_config['thresholds'].get('theta_excellence', 0.9)
        country_map = dp_config.get('country_map', {})
        
        # Process rows
        row_count = 0
        processed = 0
        
        for row in reader:
            row_count += 1
            if row_count % 1000 == 0:
                print(f"    Processing row {row_count}...", end='\r')
            
            # Build argument tuple
            args_list = []
            skip_row = False
            
            for arg_col in arg_column_names:
                val = row.get(arg_col, '').strip()
                
                if module == 'logistics':
                    if arg_col == 'timestamp':
                        # Extract hour (0-23) from timestamp
                        try:
                            dt = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                            args_list.append(dt.hour)
                        except ValueError:
                            skip_row = True
                            break
                    elif arg_col == 'weather_condition_severity':
                        # Categorize: 0-0.33 → 1 (clear), 0.33-0.66 → 2 (cloudy), 0.66-1.0 → 3 (stormy)
                        severity = float(val)
                        if severity < 0.33:
                            args_list.append(1)
                        elif severity < 0.66:
                            args_list.append(2)
                        else:
                            args_list.append(3)
                    elif arg_col == 'traffic_congestion_level':
                        # Categorize: 0-3 → 1 (light), 3-6 → 2 (moderate), 6-10 → 3 (heavy)
                        traffic = float(val)
                        if traffic < 3:
                            args_list.append(1)
                        elif traffic < 6:
                            args_list.append(2)
                        else:
                            args_list.append(3)
                    elif arg_col == 'risk_classification':
                        # Map string to int: Low → 1, Moderate → 2, High → 3
                        risk_map = {'Low Risk': 1, 'Moderate Risk': 2, 'High Risk': 3}
                        args_list.append(risk_map.get(val, 2))
                
                elif module == 'manufacturing':
                    if arg_col == 'Country':
                        country = row[arg_col].strip()
                        route = country_map.get(country)
                        if route is None:
                            skip_row = True
                            break
                        args_list.append(route)
                    elif arg_col == 'Govt_Incentive':
                        args_list.append(int(val) + 1)
                    else:
                        try:
                            args_list.append(int(val))
                        except ValueError:
                            args_list.append(val)
            
            if skip_row or not args_list:
                continue
            
            args = tuple(args_list)
            
            # Evaluate value columns against thresholds
            for csv_col, pred_name in value_column_mappings.items():
                try:
                    value = float(row[csv_col])
                    
                    if module == 'logistics':
                        # Logistics-specific thresholds
                        if 'on_time' in pred_name or 'delay' in pred_name:
                            meets = 1.0 if value < delay_threshold else 0.0
                        elif 'fuel' in pred_name:
                            meets = 1.0 if value < fuel_threshold else 0.0
                        elif 'cargo' in pred_name or 'quality' in pred_name:
                            meets = 1.0 if value > 0.5 else 0.0
                        else:
                            meets = 1.0 if value > 0.5 else 0.0
                    else:
                        # Manufacturing thresholds
                        if 'sustainability' in pred_name or 'emission' in pred_name:
                            meets = 1.0 if value < sustainability_threshold else 0.0
                        elif 'demand' in pred_name or 'service' in pred_name:
                            meets = 1.0 if value > demand_threshold else 0.0
                        elif 'capacity' in pred_name:
                            meets = 1.0 if value > capacity_threshold else 0.0
                        elif pred_name == 'meets_efficiency':
                            # For efficiency, create three tier predicates
                            # Basic tier (70%+)
                            meets_basic = 1.0 if value > basic_threshold else 0.0
                            predicates['meets_efficiency_basic'].append((args, meets_basic))
                            
                            # Advanced tier (80%+)
                            meets_adv = 1.0 if value > advanced_threshold else 0.0
                            predicates['meets_efficiency_advanced'].append((args, meets_adv))
                            
                            # Excellence tier (90%+)
                            meets_exc = 1.0 if value > excellence_threshold else 0.0
                            predicates['meets_efficiency_excellence'].append((args, meets_exc))
                            
                            # Also keep the default (basic) as meets_efficiency
                            meets = meets_basic
                        else:
                            meets = 1.0 if value > default_threshold else 0.0
                    
                    predicates[pred_name].append((args, meets))
                except (ValueError, KeyError):
                    continue
            
            processed += 1
        
        if verbose:
            print(f"\n    Processed {row_count} CSV rows → {processed} imported")
    
    return predicates


def column_to_predicate_name(column_name: str, module: str = None) -> str:
    """Convert CSV column name to ΔP predicate name."""
    
    # Manufacturing domain mappings
    manufacturing_mapping = {
        'Processing_Tech_Efficiency': 'meets_efficiency',
        'Market_Demand': 'meets_service',
        'Carbon_Emissions': 'meets_sustainability',
        'Feedstock_Yield': 'meets_feedstock_yield',
        'Production_Capacity': 'meets_capacity',
        'Energy_Consumption': 'meets_energy_efficiency',
    }
    
    # Logistics domain mappings - ONLY meaningful KPI columns
    logistics_mapping = {
        'delay_probability': 'meets_on_time_delivery',
        'fuel_consumption_rate': 'meets_fuel_efficiency',
        'cargo_condition_status': 'meets_cargo_quality',
        'delivery_time_deviation': 'meets_on_time_delivery',
    }
    
    if module == 'manufacturing':
        return manufacturing_mapping.get(column_name, None)
    elif module == 'logistics':
        return logistics_mapping.get(column_name, None)
    else:
        return None

def import_csv_to_hdf5(csv_path: Path, db_manager, module: str, verbose=False):
    """Import real CSV data into HDF5 database"""
    if verbose:
        print(f"  Reading: {csv_path}")
    
    # Generic CSV mapping (works for any module)
    predicates = map_csv_to_predicates(csv_path, module, verbose)
    
    # Detect arity from first predicate's first entry
    first_pred = next(iter(predicates.values()))
    arity = len(first_pred[0][0]) if first_pred else 3
    
    # Create predicates in HDF5
    for pred_name in predicates.keys():
        try:
            db_manager.create_predicate(pred_name, arity)
            if verbose:
                print(f"    Created predicate: {pred_name} (arity={arity})")
        except Exception:
            if verbose:
                print(f"    Predicate exists: {pred_name}")
    
    # Deduplicate entries (same args → keep last value)
    deduped_predicates = {}
    for pred_name, entries in predicates.items():
        unique_entries = {}
        for args, value in entries:
            unique_entries[args] = value
        deduped_predicates[pred_name] = list(unique_entries.items())
        
        if verbose:
            print(f"    Deduplicating {pred_name}: {len(entries)} → {len(unique_entries)} unique entries")
    
    # Insert deduplicated data
    total_rows = 0
    for pred_name, entries in deduped_predicates.items():
        if verbose:
            print(f"    Writing {len(entries)} entries for {pred_name}...")
        for args, value in entries:
            db_manager.set_value(pred_name, args, value)
            total_rows += 1
            if total_rows % 100 == 0:
                print(f"      Written {total_rows}...", end='\r')
    
    if verbose:
        print(f"\n    Imported {total_rows} predicate values")
        for pred_name in deduped_predicates.keys():
            print(f"      {pred_name}: {len(deduped_predicates[pred_name])} unique entries")
    
    return total_rows

def cmd_import(args):
    """Import real dataset into HDF5 database"""
    module = args.module if hasattr(args, 'module') and args.module else None
    
    if not module:
        print("Error: Module name required for import")
        print("Usage: dp import <module>")
        return 1
    
    # Resolve shortcuts
    module = DOMAIN_SHORTCUTS.get(module, module)
    
    # Import HDF5Manager
    try:
        import sys
        from pathlib import Path
        
        try:
            from interpreter.hdf5_manager import HDF5Manager
        except ImportError:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'interpreter'))
            from hdf5_manager import HDF5Manager
    except ImportError as e:
        print(f"Error: Could not import HDF5Manager: {e}")
        print("Make sure the interpreter module is installed.")
        return 1
    
    # Real data goes to default DB
    db_file = Path('delta_db.h5')
    
    print(f"📥 Importing real data for '{module}'...")
    print(f"   Target DB: {db_file}")
    print()
    
    # NEW: Look in module-specific data folder first
    module_data_dir = Path('data') / module
    root_data_dir = Path('data')
    
    # Priority 1: Module-specific folder
    if module_data_dir.exists():
        csv_files = list(module_data_dir.glob('*.csv'))
        search_location = module_data_dir
    else:
        # Priority 2: Root data folder (fallback)
        csv_files = list(root_data_dir.glob('*.csv'))
        search_location = root_data_dir
    
    # Filter out _synthetic folder
    csv_files = [f for f in csv_files if '_synthetic' not in str(f)]
    
    if not csv_files:
        print(f"Error: No CSV files found in {search_location}")
        print()
        print(f"Expected location: data/{module}/your_dataset.csv")
        print()
        print(f"Place your CSV file in the module-specific data folder:")
        print(f"  mkdir -p data/{module}")
        print(f"  cp your_data.csv data/{module}/")
        return 1
    
    # Use first matching CSV
    csv_path = csv_files[0]
    
    if len(csv_files) > 1:
        print(f"Warning: Multiple CSV files found, using: {csv_path.name}")
        print(f"Other files will be ignored:")
        for f in csv_files[1:]:
            print(f"  - {f.name}")
        print()
    
    print(f"Found dataset: {csv_path.name}")
    print(f"Location: {csv_path.parent}")
    print()
    
    with HDF5Manager(str(db_file)) as db:
        rows = import_csv_to_hdf5(csv_path, db, module, verbose=True)
    
    print()
    print(f"✓ Imported {rows} entries to {db_file}")
    print()
    print(f"Next steps:")
    print(f"  Run decision analysis: dp run {module} decision")
    print(f"  Run simulation: dp run {module} simulation")
    print()
    print(f"To use synthetic data instead:")
    print(f"  dp run {module} decision --synthetic")
    
    return 0

def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import real datasets into HDF5 database"
    )
    parser.add_argument(
        "module", 
        help="Module name (e.g., logistics, finance)"
    )
    
    args = parser.parse_args()
    return cmd_import(args)


if __name__ == "__main__":
    sys.exit(main())