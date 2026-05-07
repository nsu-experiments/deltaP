#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install ΔP packages from various sources.
"""

import sys
import subprocess
import shutil
from pathlib import Path


def cmd_install(args):
    """Install a ΔP package from git, local path, or registry"""
    package = args.package
    
    # Create dp_modules directory if it doesn't exist
    modules_dir = Path.cwd() / "dp_modules"
    modules_dir.mkdir(exist_ok=True)
    
    # Check if it's a local filesystem path
    package_path = Path(package).expanduser().resolve()
    if package_path.exists() and package_path.is_dir():
        print(f"Installing from local path: {package_path}")
        
        # Get package name from directory or dp.toml
        pkg_name = package_path.name
        toml_file = package_path / "dp.toml"
        
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
                    pkg_name = data.get("package", {}).get("name", pkg_name)
        
        target_dir = modules_dir / pkg_name
        
        if target_dir.exists() and not args.force:
            print(f"Error: Package '{pkg_name}' already installed. Use --force to reinstall.")
            return 1
        
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            # Check if source is a git repo
            if (package_path / ".git").exists():
                result = subprocess.run(
                    ["git", "clone", str(package_path), str(target_dir)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Error cloning repository: {result.stderr}")
                    return 1
            else:
                shutil.copytree(package_path, target_dir, symlinks=True)
            
            print(f"✓ Installed {pkg_name} to dp_modules/{pkg_name}")
            return 0
            
        except Exception as e:
            print(f"Error installing package: {e}")
            return 1
    
    # Check if it's a git URL
    elif package.startswith("http") or package.startswith("git@") or package.startswith("file://"):
        print(f"Installing from git: {package}")
        
        # Extract package name from URL
        pkg_name = package.rstrip('/').split('/')[-1].replace('.git', '')
        target_dir = modules_dir / pkg_name
        
        if target_dir.exists() and not args.force:
            print(f"Error: Package '{pkg_name}' already installed. Use --force to reinstall.")
            return 1
        
        # Clone repository
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            result = subprocess.run(
                ["git", "clone", package, str(target_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                return 1
            
            print(f"✓ Installed {pkg_name} to dp_modules/{pkg_name}")
            return 0
            
        except FileNotFoundError:
            print("Error: git command not found. Please install git.")
            return 1
    
    else:
        # Registry install (not implemented yet)
        print(f"Error: Registry-based install not yet implemented.")
        print(f"Please provide a git URL or local path, e.g.:")
        print(f"  dp install https://github.com/user/package")
        print(f"  dp install /path/to/local/package")
        return 1


def main():
    """Entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install a ΔP package")
    parser.add_argument("package", help="Package name or git URL")
    parser.add_argument("--force", action="store_true", help="Reinstall if exists")
    
    args = parser.parse_args()
    return cmd_install(args)


if __name__ == "__main__":
    sys.exit(main())