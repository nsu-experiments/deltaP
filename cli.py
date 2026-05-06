#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for ΔP package management.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def cmd_init(args):
    """Initialize a new ΔP package in the current directory"""
    cwd = Path.cwd()
    toml_path = cwd / "dp.toml"
    
    if toml_path.exists() and not args.force:
        print(f"Error: dp.toml already exists. Use --force to overwrite.")
        return 1
    
    # Get package info
    name = args.name or cwd.name
    version = args.version or "0.1.0"
    author = input("Author name (optional): ").strip() or "Unknown"
    description = input("Description (optional): ").strip() or ""
    
    # Create dp.toml
    toml_content = f"""[package]
name = "{name}"
version = "{version}"
authors = ["{author}"]
description = "{description}"
license = "MIT"

[dependencies]
# Add dependencies here, e.g.:
# dplib-core = "0.1.0"

[lib]
type = "library"
modules = []
"""
    
    toml_path.write_text(toml_content)
    print(f"✓ Created dp.toml for package '{name}'")
    
    # Create basic directory structure
    src_dir = cwd / "src"
    if not src_dir.exists():
        src_dir.mkdir()
        (src_dir / "main.dp").write_text("// Main ΔP source file\n")
        print(f"✓ Created src/ directory with main.dp")
    
    print(f"\nPackage '{name}' initialized successfully!")
    return 0


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
        
        # Copy directory (or clone if it's a git repo)
        import subprocess
        import shutil
        
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
        import subprocess
        import shutil
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


def cmd_publish(args):
    """Publish package to registry (future feature)"""
    print("Error: Publishing to registry is not yet implemented.")
    print("This feature is planned for a future release.")
    return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="dp",
        description="ΔP package manager - manage probabilistic programming packages"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # dp init
    init_parser = subparsers.add_parser("init", help="Initialize a new package")
    init_parser.add_argument("--name", help="Package name (default: directory name)")
    init_parser.add_argument("--version", default="0.1.0", help="Package version")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing dp.toml")
    init_parser.set_defaults(func=cmd_init)
    
    # dp install
    install_parser = subparsers.add_parser("install", help="Install a package")
    install_parser.add_argument("package", help="Package name or git URL")
    install_parser.add_argument("--force", action="store_true", help="Reinstall if exists")
    install_parser.set_defaults(func=cmd_install)
    
    # dp list
    list_parser = subparsers.add_parser("list", help="List installed packages")
    list_parser.set_defaults(func=cmd_list)
    
    # dp publish
    publish_parser = subparsers.add_parser("publish", help="Publish package (not implemented)")
    publish_parser.set_defaults(func=cmd_publish)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())