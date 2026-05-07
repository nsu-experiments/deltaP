#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run ΔP programs with various options.
"""

import sys
import os
import subprocess
from pathlib import Path


# Domain shortcuts
DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}


def cmd_run(args):
    """Run a ΔP program"""
    target = args.target
    
    # Resolve domain shortcuts
    target = DOMAIN_SHORTCUTS.get(target, target)
    
    verbose = args.verbose or args.debug
    quiet = args.quiet
    save_output = args.output if hasattr(args, 'output') else True  # Default: save

    # Resolve target to .dp file
    if target.endswith('.dp'):
        dp_file = Path(target)
    else:
        # Search in src/
        dp_file = Path('src') / target / 'decision.dp'
        if not dp_file.exists():
            dp_file = Path('src') / target / 'main.dp'
        if not dp_file.exists():
            dp_file = Path('src') / f'{target}.dp'
    
    if not dp_file.exists():
        print(f"Error: Could not find '{target}'")
        print(f"Tried:")
        print(f"  - {target} (if .dp file)")
        print(f"  - src/{target}/decision.dp")
        print(f"  - src/{target}/main.dp")
        print(f"  - src/{target}.dp")
        return 1
    
    # Run with interpreter
    env = os.environ.copy()
    if verbose:
        env['DELTAP_DEBUG'] = '1'
    if quiet:
        env['DELTAP_QUIET'] = '1'
    
    result = subprocess.run(
        ['deltap', str(dp_file)],
        env=env,
        capture_output=True,  
        text=True
    )
    
    # Show output in terminal
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)

    # Save output to results/
    if save_output and result.returncode == 0 and result.stdout:
        from datetime import datetime
        
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = Path(target).stem if target.endswith('.dp') else target
        output_file = results_dir / f'{module_name}_{timestamp}.txt'
        
        output_file.write_text(result.stdout)
        print(f"\n💾 Output saved to: {output_file}")

    return result.returncode


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a ΔP program")
    parser.add_argument("target", help="Module name or .dp file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output (show debug messages)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress warnings")
    
    args = parser.parse_args()
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())