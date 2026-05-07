#!/usr/bin/env python3
"""
check_database.py - Inspect delta_db.h5 contents
"""

import h5py
import sys

db_file = sys.argv[1] if len(sys.argv) > 1 else 'delta_db.h5'

try:
    with h5py.File(db_file, 'r') as f:
        print(f"Database: {db_file}")
        print("=" * 60)
        print()
        
        print("Predicates in database:")
        for pred_name in f.keys():
            ds = f[pred_name]
            print(f"\n  {pred_name}:")
            print(f"    Arity: {len([n for n in ds.dtype.names if n.startswith('arg')])}")
            print(f"    Total rows: {len(ds)}")
            
            # Count true/false
            true_count = sum(1 for row in ds if row['value'] == 1)
            false_count = sum(1 for row in ds if row['value'] == 0)
            print(f"    True: {true_count}, False: {false_count}")
            
            # Show sample rows
            if len(ds) > 0:
                print(f"    Sample rows (first 3):")
                for i, row in enumerate(ds[:3]):
                    args = [row[f'arg{j}'] for j in range(len([n for n in ds.dtype.names if n.startswith('arg')]))]
                    print(f"      {args} -> {row['value']}")
        
        print()
        print("=" * 60)

except FileNotFoundError:
    print(f"ERROR: Database file '{db_file}' not found!")
    print("Run: python populate_logistics_data.py")
except Exception as e:
    print(f"ERROR: {e}")