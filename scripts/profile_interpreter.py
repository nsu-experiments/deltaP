#!/usr/bin/env python3
"""Profile DeltaP interpreter to find performance bottlenecks"""

import cProfile
import pstats
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interpreter.parser import DeltaParser
from interpreter.evaluator import Interpreter


def profile_program(file: str, db: str):
    """Profile a single program execution"""
    with open(file, 'r', encoding='utf-8-sig') as f:
        source = f.read()
    
    parser = DeltaParser()
    prog = parser.parse(source)
    
    # Mock input
    import builtins
    builtins.input = lambda prompt="": "1"
    
    # Profile execution
    profiler = cProfile.Profile()
    
    interp = Interpreter(db)
    interp.set_warnings(False)
    
    profiler.enable()
    interp.run_program(prog)
    profiler.disable()
    
    interp.close()
    
    # Generate report
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    
    return s.getvalue()


if __name__ == '__main__':
    print("="*70)
    print("PROFILING: examples/logistics_decision.dp")
    print("="*70)
    report = profile_program('examples/logistics_decision.dp', 'delta_db_synthetic.h5')
    print(report)
    
    # Save to file
    os.makedirs('tests/performance', exist_ok=True)
    with open('tests/performance/profile_logistics.txt', 'w') as f:
        f.write(report)
    print("\nProfile saved to tests/performance/profile_logistics.txt")