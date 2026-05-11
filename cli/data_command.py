#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspect and validate ΔP HDF5 database contents.
"""

import sys
from pathlib import Path


def cmd_data(args):
    """Inspect HDF5 database contents"""
    
    # Determine which DB to inspect
    use_synthetic = getattr(args, 'synthetic', False)
    db_file = Path('delta_db_synthetic.h5') if use_synthetic else Path('delta_db.h5')
    
    # Allow custom DB path
    if hasattr(args, 'database') and args.database:
        db_file = Path(args.database)
    
    if not db_file.exists():
        print(f"❌ Database not found: {db_file}")
        print()
        if use_synthetic:
            print("Generate synthetic data with: dp populate")
        else:
            print("Import real data with: dp import <module>")
        return 1
    
    # Import h5py
    try:
        import h5py
    except ImportError:
        print("Error: h5py not installed")
        print("Install with: pip install h5py")
        return 1
    
    verbose = getattr(args, 'verbose', False)
    show_samples = getattr(args, 'samples', 3)  # Default: 3 sample rows
    
    try:
        with h5py.File(db_file, 'r') as f:
            print(f"{'='*60}")
            print(f"Database: {db_file}")
            print(f"{'='*60}")
            print()
            
            if len(f.keys()) == 0:
                print("⚠️  Database is empty (no predicates)")
                return 0
            
            print(f"Found {len(f.keys())} predicate(s):")
            print()
            
            total_rows = 0
            
            for pred_name in sorted(f.keys()):
                ds = f[pred_name]
                arity = len([n for n in ds.dtype.names if n.startswith('arg')])
                row_count = len(ds)
                total_rows += row_count
                
                # Count true/false/other
                true_count = sum(1 for row in ds if row['value'] == 1.0)
                false_count = sum(1 for row in ds if row['value'] == 0.0)
                other_count = row_count - true_count - false_count
                
                # Calculate probability
                prob = true_count / row_count if row_count > 0 else 0.0
                
                print(f"  📊 {pred_name}")
                print(f"     Arity: {arity}")
                print(f"     Rows: {row_count:,}")
                print(f"     True: {true_count:,} ({prob:.1%})")
                print(f"     False: {false_count:,}")
                if other_count > 0:
                    print(f"     Other: {other_count:,}")
                
                # Show sample rows in verbose mode
                if verbose and row_count > 0:
                    print(f"     Samples (first {min(show_samples, row_count)}):")
                    for i, row in enumerate(ds[:show_samples]):
                        args = [row[f'arg{j}'] for j in range(arity)]
                        value = row['value']
                        print(f"       {tuple(args)} → {value}")
                
                print()
            
            print(f"{'='*60}")
            print(f"Total rows across all predicates: {total_rows:,}")
            print(f"{'='*60}")
            
            return 0
            
    except FileNotFoundError:
        print(f"❌ Database file not found: {db_file}")
        return 1
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inspect ΔP HDF5 database contents"
    )
    parser.add_argument(
        "--database", 
        help="Path to HDF5 database (default: delta_db.h5)"
    )
    parser.add_argument(
        "--synthetic", "-s",
        action="store_true",
        help="Inspect synthetic database (delta_db_synthetic.h5)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show sample rows for each predicate"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=3,
        help="Number of sample rows to show (default: 3)"
    )
    
    args = parser.parse_args()
    return cmd_data(args)


if __name__ == "__main__":
    sys.exit(main())