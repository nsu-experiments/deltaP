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

    if module:
        module = DOMAIN_SHORTCUTS.get(module, module)
    
    if module:
        # Populate specific module
        module_dir = Path('src') / module
        
        if not module_dir.exists():
            print(f"Error: Module '{module}' not found at {module_dir}")
            return 1
        
        populate_script = module_dir / 'populate.dp'
        
        if not populate_script.exists():
            print(f"Error: No populate.dp found in {module_dir}")
            print(f"Create one with: dp add {module}")
            return 1
        
        # Output directory for this module
        output_dir = module_dir / 'data' / '_synthetic'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'{module}.csv'
        
        print(f"🔧 Generating synthetic data for '{module}'...")
        print(f"   Script: {populate_script}")
        print(f"   Output: {output_file}")
        
        # Run populate.dp and capture output
        try:
            result = subprocess.run(
                ['deltap', str(populate_script)],
                stdout=subprocess.PIPE,  # ← Capture to pipe, not file
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                # Write captured output to file
                output_file.write_text(result.stdout)
                
                # Show file size
                file_size = output_file.stat().st_size
                if file_size > 0:
                    print(f"✓ Generated {output_file}")
                    print(f"  File size: {file_size} bytes")
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
                modules_with_populate.append(module_name)
        
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
                module = str(module_name)
            
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
        help="Module name (omit to populate all modules)"
    )
    
    args = parser.parse_args()
    return cmd_populate(args)


if __name__ == "__main__":
    sys.exit(main())