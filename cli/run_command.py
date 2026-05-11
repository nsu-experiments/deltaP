#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run ΔP programs with various options.
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime


# Domain shortcuts
DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}
# Mode shortcuts
MODE_SHORTCUTS = {
    'sim': 'simulation',
    's': 'simulation',
    'dec': 'decision',
    'd': 'decision',      
    'pop': 'populate',
    'p': 'populate',
    'imp': 'import',
    'i': 'import',
}
def cmd_run(args):
    """Run a ΔP program"""
    run_single_mode = False
    
    use_synthetic = getattr(args, 'synthetic', False)

    # Handle both "dp run logistics" and "dp run simulation logistics"
    if isinstance(args.target, list):
        if len(args.target) == 2:
            module, mode = args.target
            # Resolve shortcuts
            mode = MODE_SHORTCUTS.get(mode, mode)
            module = DOMAIN_SHORTCUTS.get(module, module)
            run_modes = [mode]
            run_single_mode = True
        else:
            module = DOMAIN_SHORTCUTS.get(args.target[0], args.target[0])
            run_modes = ['simulation', 'decision']
    else:
        module = DOMAIN_SHORTCUTS.get(args.target, args.target)
        run_modes = ['simulation', 'decision']
    
    verbose = args.verbose or args.debug
    quiet = args.quiet
    save_output = args.output if hasattr(args, 'output') else True

    # NEW: Create timestamp once
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    env = os.environ.copy()

    db_file = 'delta_db_synthetic.h5' if use_synthetic else 'delta_db.h5'
    env['DELTAP_DB'] = db_file

    if verbose:
        env['DELTAP_DEBUG'] = '1'
    if quiet:
        env['DELTAP_QUIET'] = '1'

    # Run each mode
    success_count = 0
    for mode in run_modes:
        dp_file = Path('src') / module / f'{mode}.dp'
        
        if not dp_file.exists():
            if run_single_mode:
                print(f"❌ Error: Could not find 'src/{module}/{mode}.dp'")
                return 1
            else:
                print(f"⚠️  Skipping {mode}.dp (not found)")
                continue
        
        if not run_single_mode:
            print(f"\n{'='*60}")
            print(f"🔄 Running {mode}...")
            print(f"{'='*60}")
        
        # NEW: Create mode-specific timestamped directory
        if save_output:
            base_results = os.environ.get('DELTAP_RESULTS_DIR', 'results')
            results_dir = Path(base_results) / module / mode / timestamp
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Tell interpreter where to save CSVs
            env['DELTAP_RESULTS_DIR'] = str(results_dir)
            
            # Create/update mode-specific 'latest' symlink
            latest_link = Path(base_results) / module / mode / 'latest'
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(timestamp, target_is_directory=True)
        
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
        
        # Save output and extract CSV
        if save_output and result.returncode == 0 and result.stdout:
            # Save full output
            output_file = results_dir / f'{mode}_output.txt'
            output_file.write_text(result.stdout)
            
            # Extract CSV data from output - handle multiple tiers
            lines = result.stdout.split('\n')
            tier_csvs = {}  # {tier_name: [csv_lines]}
            current_tier = None
            current_csv = []
            found_header = False
            
            for line in lines:
                # Check for tier markers
                if line.startswith('TIER:'):
                    # Save previous tier if exists
                    if current_tier and current_csv:
                        tier_csvs[current_tier] = current_csv
                    # Start new tier
                    current_tier = line.split(':')[1].strip().lower()
                    current_csv = []
                    found_header = False
                    continue
                
                # Skip empty lines and section headers
                if not line.strip() or line.startswith('==='):
                    continue
                
                # Look for CSV lines (either in tier or regular output)
                if ',' in line:
                    stripped = line.strip()
                    
                    if not found_header:
                        first_field = stripped.split(',')[0].strip()
                        if (first_field.lower() in ['weather', 'hour', 'scenario', 'route', 'country', 'risk'] or
                            first_field.replace('_', '').isalnum()):
                            found_header = True
                            cleaned = ','.join(part.strip() for part in line.split(','))
                            if current_tier:
                                current_csv.append(cleaned)
                            else:
                                # Regular CSV (non-tiered)
                                if 'csv_lines' not in locals():
                                    csv_lines = []
                                csv_lines.append(cleaned)
                    else:
                        cleaned = ','.join(part.strip() for part in line.split(','))
                        if current_tier:
                            current_csv.append(cleaned)
                        else:
                            if 'csv_lines' not in locals():
                                csv_lines = []
                            csv_lines.append(cleaned)
            
            # Save last tier
            if current_tier and current_csv:
                tier_csvs[current_tier] = current_csv
            
            # Write tier-specific CSV files
            files_created = 0
            if tier_csvs:
                for tier_name, tier_lines in tier_csvs.items():
                    csv_file = results_dir / f'{mode}_{tier_name}.csv'
                    csv_file.write_text('\n'.join(tier_lines) + '\n')
                    files_created += 1
                if run_single_mode:
                    print(f"\n💾 Generated {files_created} tier files in: {results_dir}")
            
            # Also save non-tiered CSV if exists
            if 'csv_lines' in locals() and csv_lines:
                csv_file = results_dir / f'{mode}_results.csv'
                csv_file.write_text('\n'.join(csv_lines) + '\n')
                files_created += 1
            
            if run_single_mode and files_created == 0:
                print(f"\n💾 Output saved to: {results_dir}")
        
        if result.returncode == 0:
            success_count += 1
    
    if not run_single_mode and success_count > 0:
        print(f"\n{'='*60}")
        print(f"✅ Completed {success_count}/{len(run_modes)} mode(s)")
        if save_output:
            print(f"💾 Results saved to: results/{module}/{{decision,simulation}}/{timestamp}")
        print(f"{'='*60}")
    
    return 0 if success_count > 0 else 1

def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a ΔP program")
    parser.add_argument("module", help="Module name (e.g., logistics, lg)")
    parser.add_argument("mode", nargs='?', help="Mode to run (decision, simulation, etc.)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output (show debug messages)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress warnings")
    parser.add_argument("--synthetic", "-s", action="store_true", 
                       help="Use synthetic database (delta_db_synthetic.h5) instead of real data")
    
    args = parser.parse_args()
    
    # Convert to target list format for cmd_run
    if args.mode:
        args.target = [args.module, args.mode]
    else:
        args.target = args.module
    
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())