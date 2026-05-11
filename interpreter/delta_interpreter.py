#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeltaP interpreter main entry point.
"""

import sys
import os
from pathlib import Path
from .parser import DeltaParser
from .evaluator import Interpreter


def main():
    """Main entry point for DeltaP interpreter"""
    # Handle --help
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print("Usage: deltap <program.dp> [database.h5]")
        print("\nΔP Probabilistic Programming Language Interpreter")
        print("\nArguments:")
        print("  program.dp    ΔP source file to execute")
        print("  database.h5   HDF5 database file (default: delta_db.h5)")
        return 0
    
    prog_file = sys.argv[1]
    db_file = os.environ.get('DELTAP_DB') or (sys.argv[2] if len(sys.argv) > 2 else "delta_db.h5")
    
    base_path = Path.cwd()

    # Read source file
    with open(prog_file, 'r', encoding='utf-8-sig') as f:
        source = f.read()
    
    # Parse
    parser = DeltaParser()
    try:
        prog = parser.parse(source)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        sys.exit(1)
    
    # Execute
    interp = Interpreter(db_file, base_path=base_path)
    try:
        interp.run_program(prog)
    except Exception as e:
        print(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        interp.close()


if __name__ == '__main__':
    main()