#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add new analysis modules to ΔP projects.
"""

import sys
from pathlib import Path
from typing import Optional
import shutil


# Domain shortcuts mapping
DOMAIN_SHORTCUTS = {
    'lg': 'logistics',
    'fi': 'finance',
    'hc': 'healthcare',
    'mf': 'manufacturing',
    'en': 'energy',
}


def resolve_module_name(name: str) -> str:
    """Resolve domain shortcuts to full names"""
    return DOMAIN_SHORTCUTS.get(name, name)


def render_template(template_path: Path, context: dict) -> str:
    """Simple template rendering (replace {{var}} with values)"""
    content = template_path.read_text()
    
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    
    return content


def cmd_add(args):
    """Add a new analysis module to the current project"""
    input_name = args.module_name
        
    # Check if input is a domain shortcut
    if input_name in DOMAIN_SHORTCUTS:
        module_name = DOMAIN_SHORTCUTS[input_name]  # lg → logistics
        template = module_name                       # Use logistics template
    else:
        module_name = input_name                     # Use as-is
        template = getattr(args, 'template', None) or 'generic'
    
    # Check if we're in a ΔP project
    if not Path("deltap.toml").exists():
        print("Error: Not in a ΔP project.")
        print("Run 'dp init' first to create a project.")
        return 1
    
    # Determine target directory
    src_dir = Path("src")
    if not src_dir.exists():
        print("Error: src/ directory not found.")
        return 1
    
    # Check if domain module already exists (only for non-generic templates)
    if template != 'generic':
        domain_module = src_dir / template
        if domain_module.exists():
            print(f"Error: Domain module '{template}' already exists at {domain_module}")
            print(f"Tip: Use a different name or remove existing module:")
            print(f"     rm -rf src/{template}")
            return 1
    
    # Create module directory
    module_dir = src_dir / module_name
    if module_dir.exists():
        print(f"Error: Module '{module_name}' already exists at {module_dir}")
        return 1
    
    module_dir.mkdir(parents=True)
    
    # NEW: Create module-specific data and results folders
    project_root = Path("deltap.toml").parent.resolve()
    
    root_data_dir = project_root / "data"
    root_results_dir = project_root / "results"
    
    # Ensure root directories exist
    if not root_data_dir.exists():
        root_data_dir.mkdir()
        print(f"✓ Created root data/ directory")
    
    if not root_results_dir.exists():
        root_results_dir.mkdir()
        print(f"✓ Created root results/ directory")
    
    # Create module-specific folders
    module_data_dir = root_data_dir / module_name
    module_results_dir = root_results_dir / module_name
    
    if not module_data_dir.exists():
        module_data_dir.mkdir(parents=True)
        (module_data_dir / "_synthetic").mkdir(exist_ok=True)
        print(f"✓ Created data/{module_name}/ and data/{module_name}/_synthetic/")
    
    if not module_results_dir.exists():
        module_results_dir.mkdir(parents=True)
        print(f"✓ Created results/{module_name}/")
    
    # Get module templates
    base_template_dir = Path(__file__).parent / "templates" / "module"
    
    # Try domain-specific template first, fall back to generic
    template_dir = base_template_dir / template
    if not template_dir.exists():
        if template != 'generic':
            print(f"Warning: Template '{template}' not found, using generic template")
        template_dir = base_template_dir / "generic"
    
    if not template_dir.exists():
        # Fall back to old flat structure
        template_dir = base_template_dir
    
    if not template_dir.exists():
        print(f"Error: Module templates not found at {base_template_dir}")
        return 1
    
    # Context for template rendering
    context = {
        "module_name": module_name,
    }
    
    # Detect template file naming pattern
    # Try new pattern (config.dp.template) first, fall back to old (module_config.dp.template)
    template_files = list(template_dir.glob("*.template"))
    
    if any('module_' in f.name for f in template_files):
        # Old naming pattern
        templates = [
            ("module_config.dp.template", "config.dp"),
            ("module_decision.dp.template", "decision.dp"),
            ("module_simulation.dp.template", "simulation.dp"),
            ("module_populate.dp.template", "populate.dp"),
            ("module_visualize.toml.template", "visualize.toml"),
        ]
    else:
        # New naming pattern
        templates = [
            ("config.dp.template", "config.dp"),
            ("decision.dp.template", "decision.dp"),
            ("simulation.dp.template", "simulation.dp"),
            ("populate.dp.template", "populate.dp"),
            ("visualize.toml.template", "visualize.toml"),
        ]
    
    created_files = []
    
    for template_name, output_name in templates:
        template_path = template_dir / template_name
        
        if not template_path.exists():
            print(f"Warning: Template {template_name} not found, skipping...")
            continue
        
        # Render template
        content = render_template(template_path, context)
        
        # Write to module directory
        output_path = module_dir / output_name
        output_path.write_text(content)
        created_files.append(output_name)
    
    # Success message
    domain_hint = f" ({template} domain)" if template != 'generic' else ""
    print(f"✓ Created module: src/{module_name}/{domain_hint}")
    for file in created_files:
        print(f"  - {file}")
    print()
    print(f"Next steps:")
    print(f"  1. Place your CSV in data/{module_name}/")
    print(f"  2. Edit src/{module_name}/config.dp to define your domains")
    
    # Show shortcut if applicable
    shortcut = next((k for k, v in DOMAIN_SHORTCUTS.items() if v == module_name), None)
    if shortcut:
        print(f"  3. Run: dp import {shortcut}  (or: dp import {module_name})")
        print(f"  4. Run: dp run {shortcut} decision  (or: dp run {module_name} decision)")
    else:
        print(f"  3. Run: dp import {module_name}")
        print(f"  4. Run: dp run {module_name} decision")
    
    return 0


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add a new analysis module"
    )
    parser.add_argument("module_name", help="Name of the module to create (or domain shortcut: lg, fi, hc, mf, en)")
    parser.add_argument("--template", "-t", help="Module template to use (generic, logistics, finance, healthcare, manufacturing, energy)")
    
    args = parser.parse_args()
    return cmd_add(args)


if __name__ == "__main__":
    sys.exit(main())