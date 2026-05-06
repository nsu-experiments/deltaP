#!/usr/bin/env python3
import sys
sys.path.insert(0, 'interpreter')

from pathlib import Path
from evaluator import Interpreter

# Create interpreter
interp = Interpreter('test_db.h5', base_path=Path.cwd())

# Test the resolution
dotted_name = 'dplib.core.math.abs'
print(f"Testing: {dotted_name}")

# Check if resolve works
resolved = interp.predicates.resolve_name(dotted_name)
print(f"PredicateManager.resolve_name returned: {resolved}")

# Try the full resolution
try:
    result = interp._resolve_module_predicate(dotted_name)
    print(f"_resolve_module_predicate returned: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Check what's in sp_defs after
print(f"\nStatic predicates registered: {list(interp.sp_defs.keys())[:10]}")

interp.close()