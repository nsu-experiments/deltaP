#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List installed ΔP packages.
"""

import sys
from pathlib import Path


def cmd_list(args):
    """List installed packages"""
    modules_dir = Path.cwd() / "dp_modules"
    
    if not modules_dir.exists():
        print("No packages installed (dp_modules/ directory not found)")
        return 0
    
    packages = [d for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not packages:
        print("No packages installed")
        return 0
    
    print(f"Installed packages in {modules_dir}:\n")
    
    for pkg_dir in sorted(packages):
        # Try to read version from dp.toml
        toml_file = pkg_dir / "dp.toml"
        version = "unknown"
        description = ""
        
        if toml_file.exists():
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    tomllib = None
            
            if tomllib:
                with open(toml_file, "rb") as f:
                    data = tomllib.load(f)
                    version = data.get("package", {}).get("version", "unknown")
                    description = data.get("package", {}).get("description", "")
        
        print(f"  • {pkg_dir.name} ({version})")
        if description:
            print(f"    {description}")
    
    print(f"\nTotal: {len(packages)} package(s)")
    return 0


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="List installed ΔP packages")
    
    args = parser.parse_args()
    return cmd_list(args)


if __name__ == "__main__":
    sys.exit(main())