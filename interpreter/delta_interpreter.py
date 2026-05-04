#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeltaP interpreter main entry point.
"""

import sys
from .parser import DeltaParser
from .evaluator import Interpreter


def main():
    """Main entry point for DeltaP interpreter"""
    if len(sys.argv) < 2:
        print("Usage: python -m interpreter program.dp [database.h5]")
        sys.exit(1)
    
    prog_file = sys.argv[1]
    db_file = sys.argv[2] if len(sys.argv) > 2 else "delta_db.h5"
    
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
    interp = Interpreter(db_file)
    try:
        interp.run_program(prog)
    except Exception as e:
        print(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        interp.close()


if __name__ == '__main__':
    main()