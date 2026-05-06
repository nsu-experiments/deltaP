#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module resolution system for ΔP package management.
Handles auto-discovery of dplib/ and dp_modules/ directories.
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import sys


@dataclass
class PackageInfo:
    """Metadata for a ΔP package."""
    name: str
    version: str
    path: Path
    modules: List[str]


class ModuleResolver:
    """
    Resolves module paths like 'dplib.logistics.transport' to file paths.
    Auto-discovers packages in current directory and dp_modules/.
    """
    
    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or [Path.cwd()]
        self.packages: Dict[str, PackageInfo] = {}
        self.module_cache: Dict[str, Path] = {}
        self._discover_packages()
    
    def _discover_packages(self) -> None:
        """Scan for dp.toml files and register packages."""
        for search_path in self.search_paths:
            # Check for dplib/ in current directory
            dplib_path = search_path / "dplib"
            if dplib_path.exists() and dplib_path.is_dir():
                self._scan_dplib(dplib_path)
            
            # Check for dp_modules/ directory
            dp_modules = search_path / "dp_modules"
            if dp_modules.exists() and dp_modules.is_dir():
                for package_dir in dp_modules.iterdir():
                    if package_dir.is_dir():
                        toml_file = package_dir / "dp.toml"
                        if toml_file.exists():
                            self._load_package_toml(toml_file, package_dir)
                        else:
                            # Fallback: scan directory structure
                            self._scan_package_dir(package_dir)
    
    def _scan_dplib(self, dplib_path: Path) -> None:
        """Scan dplib/ directory structure and build module map."""
        modules = []
        for dp_file in dplib_path.rglob("*.dp"):
            # Convert path to module notation: dplib/core/math.dp -> dplib.core.math
            relative = dp_file.relative_to(dplib_path.parent)
            module_path = str(relative.with_suffix("")).replace("/", ".")
            modules.append(module_path)
            self.module_cache[module_path] = dp_file
        
        # Register dplib package
        self.packages["dplib"] = PackageInfo(
            name="dplib",
            version="0.1.0",
            path=dplib_path,
            modules=modules
        )
    
    def _scan_package_dir(self, package_dir: Path) -> None:
        """Scan a package directory without dp.toml."""
        package_name = package_dir.name
        modules = []
        
        for dp_file in package_dir.rglob("*.dp"):
            relative = dp_file.relative_to(package_dir.parent)
            module_path = str(relative.with_suffix("")).replace("/", ".")
            modules.append(module_path)
            self.module_cache[module_path] = dp_file
        
        self.packages[package_name] = PackageInfo(
            name=package_name,
            version="unknown",
            path=package_dir,
            modules=modules
        )
    
    def _load_package_toml(self, toml_file: Path, package_dir: Path) -> None:
        """Load package metadata from dp.toml."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # Fallback for older Python
        
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
        
        package = data.get("package", {})
        lib = data.get("lib", {})
        
        package_name = package.get("name", package_dir.name)
        modules = lib.get("modules", [])
        
        # If modules list is empty, auto-scan the package directory
        if not modules:
            for dp_file in package_dir.rglob("*.dp"):
                relative = dp_file.relative_to(package_dir)
                module_path = str(relative.with_suffix("")).replace("/", ".")
                modules.append(module_path)
                full_module = f"{package_name}.{module_path}"
                self.module_cache[full_module] = dp_file
        else:
            # Register modules with their file paths
            for module in modules:
                # Convert module notation to file path: dplib.core.math -> dplib/core/math.dp
                file_path = package_dir / module.replace(".", "/")
                file_path = file_path.with_suffix(".dp")
                
                if file_path.exists():
                    full_module = f"{package_name}.{module}" if not module.startswith(package_name) else module
                    self.module_cache[full_module] = file_path
        
        self.packages[package_name] = PackageInfo(
            name=package_name,
            version=package.get("version", "unknown"),
            path=package_dir,
            modules=modules
        )
        
    def resolve(self, module_path: str) -> Optional[Path]:
        """
        Resolve a module path to a file.
        
        Args:
            module_path: Dotted module path (e.g., 'dplib.logistics.transport')
        
        Returns:
            Path to .dp file, or None if not found
        """
        # Check cache first
        if module_path in self.module_cache:
            return self.module_cache[module_path]
        
        # Try to find it in package directories
        parts = module_path.split(".")
        
        for search_path in self.search_paths:
            # Try direct path: dplib.core.math -> dplib/core/math.dp
            file_path = search_path / "/".join(parts)
            file_path = file_path.with_suffix(".dp")
            
            if file_path.exists():
                self.module_cache[module_path] = file_path
                return file_path
        
        return None
    
    def get_module_predicates(self, module_path: str) -> List[str]:
        """
        Get list of predicates defined in a module.
        (Placeholder - requires parsing the .dp file)
        """
        # TODO: Parse .dp file and extract predicate names
        return []
    
    def list_modules(self) -> List[str]:
        """List all available modules."""
        return list(self.module_cache.keys())
    
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get metadata for a package."""
        return self.packages.get(package_name)


def find_module_file(module_path: str, base_path: Optional[Path] = None) -> Optional[Path]:
    """
    Convenience function to resolve a module path.
    
    Args:
        module_path: Dotted module path (e.g., 'dplib.logistics.transport')
        base_path: Base directory to search from (defaults to current directory)
    
    Returns:
        Path to .dp file, or None if not found
    """
    search_paths = [base_path] if base_path else [Path.cwd()]
    resolver = ModuleResolver(search_paths)
    return resolver.resolve(module_path)