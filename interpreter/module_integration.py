#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration of module resolution into the ΔP interpreter.
Handles loading and caching of external modules.
"""

from pathlib import Path
from typing import Dict, Set, Optional
from .module_resolver import ModuleResolver


class ModuleLoader:
    """
    Loads and caches ΔP modules.
    Integrates with the parser to support dotted predicate calls.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.resolver = ModuleResolver([self.base_path])
        self.loaded_modules: Dict[str, str] = {}  # module_path -> source code
        self.loading: Set[str] = set()  # Track circular dependencies
    
    def load_module(self, module_path: str) -> Optional[str]:
        """
        Load a module's source code.
        
        Args:
            module_path: Dotted module path (e.g., 'dplib.logistics.transport')
        
        Returns:
            Source code as string, or None if not found
        
        Raises:
            RuntimeError: If circular dependency detected
        """
        # Check cache
        if module_path in self.loaded_modules:
            return self.loaded_modules[module_path]
        
        # Check for circular dependency
        if module_path in self.loading:
            raise RuntimeError(f"Circular dependency detected: {module_path}")
        
        # Resolve to file
        file_path = self.resolver.resolve(module_path)
        if not file_path:
            return None
        
        # Load source
        self.loading.add(module_path)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                source = f.read()
            
            self.loaded_modules[module_path] = source
            return source
        finally:
            self.loading.remove(module_path)
    
    def resolve_predicate_call(self, dotted_name: str) -> tuple[str, str]:
        """
        Resolve a dotted predicate call like 'dplib.logistics.transport.route_optimal'.
        
        Args:
            dotted_name: Full dotted path to predicate
        
        Returns:
            Tuple of (module_path, predicate_name)
            e.g., ('dplib.logistics.transport', 'route_optimal')
        """
        parts = dotted_name.split(".")
        
        # Try progressively longer module paths
        for i in range(len(parts) - 1, 0, -1):
            module_path = ".".join(parts[:i])
            predicate_name = ".".join(parts[i:])
            
            if self.resolver.resolve(module_path):
                return module_path, predicate_name
        
        # Not a module path, return as-is
        return "", dotted_name
    
    def list_available_modules(self) -> list[str]:
        """List all discoverable modules."""
        return self.resolver.list_modules()
    
    def get_loaded_modules(self) -> list[str]:
        """List currently loaded modules."""
        return list(self.loaded_modules.keys())


class ModuleAwareInterpreter:
    """
    Wrapper to add module support to existing Interpreter.
    This is a mixin/helper that can be integrated into your Interpreter class.
    """
    
    def __init__(self, db_file: str, base_path: Optional[Path] = None):
        self.module_loader = ModuleLoader(base_path)
        # Your existing Interpreter.__init__ code here
    
    def load_external_module(self, module_path: str) -> bool:
        """
        Load an external module and parse its predicates.
        
        Args:
            module_path: Module to load (e.g., 'dplib.logistics.transport')
        
        Returns:
            True if loaded successfully, False otherwise
        """
        source = self.module_loader.load_module(module_path)
        if not source:
            return False
        
        # Parse the module (requires parser integration)
        # This would parse predicates and add them to the predicate registry
        # with a namespace prefix
        
        # TODO: Integrate with your existing parser
        # parser = DeltaParser()
        # module_ast = parser.parse(source)
        # self.register_module_predicates(module_path, module_ast)
        
        return True
    
    def resolve_predicate(self, dotted_name: str) -> str:
        """
        Resolve a dotted predicate call and ensure the module is loaded.
        
        Args:
            dotted_name: e.g., 'dplib.logistics.transport.route_optimal'
        
        Returns:
            Fully qualified predicate name for internal use
        """
        module_path, predicate_name = self.module_loader.resolve_predicate_call(dotted_name)
        
        if module_path:
            # Ensure module is loaded
            if not self.load_external_module(module_path):
                raise RuntimeError(f"Could not load module: {module_path}")
            
            # Return namespaced predicate name
            return f"{module_path}::{predicate_name}"
        
        return predicate_name