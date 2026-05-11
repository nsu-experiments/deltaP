#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync CSV/JSON data to HDF5 database for ΔP modules.
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


def detect_predicates_from_csv(csv_path: Path) -> dict:
    """Analyze CSV structure to infer predicate names and arities"""
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Identify argument columns vs value columns
        # Convention: lowercase args (route, scenario, month), value cols are predicate names
        arg_cols = []
        value_cols = []
        
        for col in headers:
            col_clean = col.strip()
            # Common argument column names
            if col_clean in ['route', 'scenario', 'month', 'year', 'period', 'asset', 'id']:
                arg_cols.append(col_clean)
            else:
                value_cols.append(col_clean)
        
        return {
            'arg_cols': arg_cols,
            'value_cols': value_cols,
            'arity': len(arg_cols)
        }


def sync_csv_to_hdf5(csv_path: Path, db_manager, verbose=False):
    """Sync a CSV file to HDF5 database"""
    if verbose:
        print(f"  Reading: {csv_path}")
    
    # Detect structure
    structure = detect_predicates_from_csv(csv_path)
    arg_cols = structure['arg_cols']
    value_cols = structure['value_cols']
    arity = structure['arity']
    
    if verbose:
        print(f"    Arguments: {', '.join(arg_cols)} (arity={arity})")
        print(f"    Predicates: {', '.join(value_cols)}")
    
    # Create predicates
    for pred_name in value_cols:
        try:
            db_manager.create_predicate(pred_name, arity)
        except Exception:
            pass  # Already exists
    
    # Insert data
    row_count = 0
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract arguments
            args = tuple(int(float(row[col].strip())) for col in arg_cols)
            
            # Set values for each predicate
            for pred_name in value_cols:
                value = float(row[pred_name].strip())
                db_manager.set_value(pred_name, args, value)
            
            row_count += 1
    
    if verbose:
        print(f"    Synced {row_count} rows")
    
    return row_count


def cmd_sync(args):
    """Sync CSV/JSON data to HDF5 database"""
    module = args.module if hasattr(args, 'module') and args.module else None
    use_synthetic = getattr(args, 'synthetic', False) 

    # Resolve shortcuts
    if module:
        module = DOMAIN_SHORTCUTS.get(module, module)
    
    # Import HDF5Manager
    try:
        import sys
        from pathlib import Path
        
        # Try to import from installed package
        try:
            from interpreter.hdf5_manager import HDF5Manager
        except ImportError:
            # Try relative import for development
            sys.path.insert(0, str(Path(__file__).parent.parent / 'interpreter'))
            from hdf5_manager import HDF5Manager
    except ImportError as e:
        print(f"Error: Could not import HDF5Manager: {e}")
        print("Make sure the interpreter module is installed.")
        return 1
    
    db_file = Path('delta_db_synthetic.h5') if use_synthetic else Path('delta_db.h5')
    
    print(f"🔄 Syncing data to {db_file}...")
    print()
    
    with HDF5Manager(str(db_file)) as db:
        total_synced = 0
        
        if module:
            # Sync specific module
            module_dir = Path('src') / module
            
            if not module_dir.exists():
                print(f"Error: Module '{module}' not found at {module_dir}")
                return 1
            
            # Look for data files
            data_dir = module_dir / 'data'
            synthetic_dir = data_dir / '_synthetic'
            
            csv_files = []
            
            # Priority: real data, then synthetic
            if data_dir.exists():
                csv_files.extend(data_dir.glob('*.csv'))
            if synthetic_dir.exists():
                csv_files.extend(synthetic_dir.glob('*.csv'))
            
            if not csv_files:
                print(f"No CSV files found in {data_dir}")
                return 1
            
            print(f"Module: {module}")
            for csv_file in csv_files:
                rows = sync_csv_to_hdf5(csv_file, db, verbose=True)
                total_synced += rows
            
        else:
            # Sync all modules
            src_dir = Path('src')
            
            if not src_dir.exists():
                print("Error: src/ directory not found.")
                return 1
            
            # Find all modules with data
            modules_synced = 0
            
            for module_path in src_dir.iterdir():
                if module_path.is_dir() and not module_path.name.startswith('_'):
                    data_dir = module_path / 'data'
                    synthetic_dir = data_dir / '_synthetic'
                    
                    csv_files = []
                    if data_dir.exists():
                        csv_files.extend(data_dir.glob('*.csv'))
                    if synthetic_dir.exists():
                        csv_files.extend(synthetic_dir.glob('*.csv'))
                    
                    if csv_files:
                        print(f"Module: {module_path.name}")
                        for csv_file in csv_files:
                            rows = sync_csv_to_hdf5(csv_file, db, verbose=True)
                            total_synced += rows
                        modules_synced += 1
                        print()
            
            if modules_synced == 0:
                print("No modules with data found.")
                return 0
        
        print()
        print(f"✓ Synced {total_synced} total rows to {db_file}")
        return 0


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sync CSV/JSON data to HDF5 database"
    )
    parser.add_argument(
        "module", 
        nargs='?', 
        help="Module name (omit to sync all modules)"
    )
    
    args = parser.parse_args()
    return cmd_sync(args)


if __name__ == "__main__":
    sys.exit(main())