#!/usr/bin/env python3
"""
Performance benchmarking for ΔP interpreter optimizations.
Tracks execution time, cache hits, and memory usage over time.
"""

import time
import sys
import os
from datetime import datetime
from typing import Dict, List
import json

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from interpreter.parser import DeltaParser
from interpreter.evaluator import Interpreter


def benchmark_program(file: str, db: str, iterations: int = 10, enable_memo: bool = True, enable_lazy: bool = True) -> Dict:
    """Run benchmark on a single program"""
    with open(file, 'r', encoding='utf-8-sig') as f:
        source = f.read()
    
    parser = DeltaParser()
    prog = parser.parse(source)
    
    times = []
    cache_sizes = []
    
    for i in range(iterations):
        interp = Interpreter(db)
        interp.set_warnings(False)
        # Configure optimizations
        interp.enable_memoization = enable_memo   # ADD HERE
        interp.enable_lazy_eval = enable_lazy     # ADD HERE
        # Mock input for non-interactive benchmarking
        import builtins
        original_input = builtins.input
        builtins.input = lambda prompt="": "1"  # Default value for all inputs
        
        start = time.perf_counter()
        interp.run_program(prog)
        end = time.perf_counter()
        # Restore input
        builtins.input = original_input
        times.append(end - start)
        cache_sizes.append(len(interp._memo_cache))
        
        interp.close()
    
    return {
        'file': file,
        'iterations': iterations,
        'avg_time_ms': sum(times) / len(times) * 1000,
        'min_time_ms': min(times) * 1000,
        'max_time_ms': max(times) * 1000,
        'avg_cache_size': sum(cache_sizes) / len(cache_sizes),
        'times_ms': [t * 1000 for t in times]
    }


def run_benchmarks(enable_memo: bool = True, enable_lazy: bool = True) -> Dict:    
    """Run all benchmarks and return results"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'optimizations': {
            'memoization': enable_memo,
            'lazy_eval': enable_lazy,
            'parallel': False
        },
        'programs': []
    }
    
    
    # Test programs
    programs = [
        ('v1/traffic_simulation.dp', 'traffic_test.h5'),
        ('v1/emergency_decision.dp', 'emergency_test.h5'),
        ('examples/logistics_decision.dp', 'delta_db.h5'),
        ('examples/supply_chain_simulation.dp', 'delta_db.h5')
    ]
    
    for prog_file, db_file in programs:
        if os.path.exists(prog_file):
            print(f"Benchmarking {prog_file}...", flush=True)
            result = benchmark_program(prog_file, db_file, iterations=5, enable_memo=enable_memo, enable_lazy=enable_lazy)
            results['programs'].append(result)
            print(f"  Avg: {result['avg_time_ms']:.2f}ms, Cache: {result['avg_cache_size']:.1f} entries")
    
    return results


def save_results(results: Dict) -> str:
    """Save results to timestamped JSON file"""
    # Ensure performance directory exists
    os.makedirs('tests/performance', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tests/performance/benchmark_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    return filename


def print_summary(results: Dict):
    """Print human-readable summary"""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Optimizations: {results['optimizations']}")
    print("\nResults:")
    
    for prog in results['programs']:
        print(f"\n{prog['file']}:")
        print(f"  Average: {prog['avg_time_ms']:.2f}ms")
        print(f"  Range: {prog['min_time_ms']:.2f}ms - {prog['max_time_ms']:.2f}ms")
        print(f"  Cache hits: {prog['avg_cache_size']:.1f} entries")


if __name__ == '__main__':
    results = run_benchmarks(enable_memo=False, enable_lazy=False)
    save_results(results)
    print_summary(results)
