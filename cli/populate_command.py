#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate synthetic test data for ΔP modules.
"""

import sys
import subprocess
from pathlib import Path

DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}

def cmd_populate(args):
    """Generate synthetic data using module's populate.dp script"""
    module = args.module if hasattr(args, 'module') else None
    force_synthetic = getattr(args, 'synthetic', False) 

    if module:
        module = DOMAIN_SHORTCUTS.get(module, module)
        # Populate specific module
        module_dir = Path('src') / module
        
        if not module_dir.exists():
            print(f"Error: Module '{module}' not found at {module_dir}")
            return 1
        
        # NEW: Check for real data in module-specific folder
        module_real_data = Path('data') / module / f'{module}_dataset.csv'
        root_real_data = Path('data') / f'{module}_dataset.csv'  # Fallback
        
        populate_real = module_dir / 'populate_real.dp'
        populate_synthetic = module_dir / 'populate.dp'
        
        # Determine which script to use
        real_data_exists = module_real_data.exists() or root_real_data.exists()
        
        if not force_synthetic and real_data_exists and populate_real.exists():
            populate_script = populate_real
            data_source = f"real data"
        else:
            if not populate_synthetic.exists():
                print(f"Error: No populate.dp found in {module_dir}")
                return 1
            populate_script = populate_synthetic
            data_source = "synthetic data"
        
        # NEW: Module-specific synthetic output folder
        output_dir = Path('data') / module / '_synthetic'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'{module}.csv'
        
        print(f"🔧 Generating {data_source} for '{module}'...")
        print(f"   Script: {populate_script}")
        print(f"   Output: {output_file}")
        
        # Run populate.dp and capture output
        try:
            # Set environment variable for synthetic DB
            import os
            os.environ['DELTAP_DB'] = 'delta_db_synthetic.h5'
            
            result = subprocess.run(
                ['deltap', str(populate_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                # Write captured output to file
                output_file.write_text(result.stdout)
                
                # Show file size and row count
                file_size = output_file.stat().st_size
                if file_size > 0:
                    with open(output_file) as f:
                        rows = len(f.readlines()) - 1  # Exclude header
                    
                    print(f"✓ Generated {output_file}")
                    print(f"  {rows} data rows ({file_size} bytes)")
                    print()
                    print(f"Next steps:")
                    print(f"  Import to HDF5: dp import {module} --synthetic")
                    print(f"  Run analysis: dp run {module} decision --synthetic")
                else:
                    print(f"  Warning: Output file is empty")
                
                return 0
            else:
                print(f"❌ Error generating data:")
                print(result.stderr)
                return 1
                
        except FileNotFoundError:
            print("Error: 'deltap' command not found.")
            print("Make sure the ΔP interpreter is installed and in your PATH.")
            return 1
    
    else:
        # Populate all modules
        src_dir = Path('src')
        
        if not src_dir.exists():
            print("Error: src/ directory not found.")
            print("This command requires a Standard or Full project structure.")
            return 1
        
        # Find all modules with populate.dp
        modules_with_populate = []
        
        for item in src_dir.rglob('populate.dp'):
            module_dir = item.parent
            # Skip _examples
            if '_example' not in str(module_dir):
                module_name = module_dir.relative_to(src_dir)
                modules_with_populate.append(str(module_name))
        
        if not modules_with_populate:
            print("No modules with populate.dp found in src/")
            print("Create a module with: dp add <module_name>")
            return 0
        
        print(f"Found {len(modules_with_populate)} module(s) with populate.dp:")
        for mod in modules_with_populate:
            print(f"  - {mod}")
        print()
        
        # Populate each module
        success_count = 0
        for module_name in modules_with_populate:
            print(f"Populating {module_name}...")
            
            # Create args for recursive call
            class ModuleArgs:
                module = module_name
                synthetic = force_synthetic
            
            result = cmd_populate(ModuleArgs())
            if result == 0:
                success_count += 1
            print()
        
        print(f"✓ Populated {success_count}/{len(modules_with_populate)} module(s)")
        return 0 if success_count == len(modules_with_populate) else 1


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for modules"
    )
    parser.add_argument(
        "module", 
        nargs='?', 
        help="Module name (or domain shortcut: lg, fi, hc, mf, en). Omit to populate all modules."
    )
    parser.add_argument(
        "--synthetic", "-s",
        action="store_true",
        help="Force synthetic data generation even if real data exists"
    )
    
    args = parser.parse_args()
    return cmd_populate(args)


if __name__ == "__main__":
    sys.exit(main())