#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced predicate manager for handling static and dynamic predicates.
Now supports module namespaces for package system.
"""

from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from .ast_nodes import Expr
from .exceptions import DeltaPNameError, DeltaPArityError

if TYPE_CHECKING:
    from .evaluator import Interpreter


class PredicateManager:
    """Manages static and dynamic predicates with module namespace support"""
    
    def __init__(self, interpreter: 'Interpreter'):
        self.interp = interpreter
        self.static_preds: Dict[str, Tuple[List[str], Expr]] = {}
        self.dynamic_preds: Dict[str, Tuple[List[str], Expr]] = {}
        self.module_namespace: Dict[str, str] = {}  # predicate_name -> module_path
    
    def define_static(self, name: str, params: List[str], body: Expr, lineno: int = 0, 
                     module: Optional[str] = None) -> None:
        """Define a static predicate with validation and optional module namespace"""
        # Add module prefix if provided
        full_name = f"{module}::{name}" if module else name
        
        if name in self.interp.vars and not module:
            raise DeltaPNameError(
                f"Static predicate '{name}' conflicts with existing variable", 
                lineno
            )
        if full_name in self.dynamic_preds:
            raise DeltaPNameError(
                f"Static predicate '{name}' conflicts with existing dynamic predicate", 
                lineno
            )
        
        self.static_preds[full_name] = (params, body)
        if module:
            self.module_namespace[full_name] = module
    
    def define_dynamic(self, name: str, params: List[str], domain: Expr, lineno: int = 0,
                      module: Optional[str] = None) -> None:
        """Define a dynamic predicate with validation and optional module namespace"""
        # Add module prefix if provided
        full_name = f"{module}::{name}" if module else name
        
        if name in self.interp.vars and not module:
            raise DeltaPNameError(
                f"Dynamic predicate '{name}' conflicts with existing variable", 
                lineno
            )
        if full_name in self.static_preds:
            raise DeltaPNameError(
                f"Dynamic predicate '{name}' conflicts with existing static predicate", 
                lineno
            )
        if full_name in self.dynamic_preds:
            old_arity = len(self.dynamic_preds[full_name][0])
            new_arity = len(params)
            if old_arity != new_arity:
                raise DeltaPArityError(
                    f"Cannot change arity of '{name}' from {old_arity} to {new_arity}", 
                    lineno
                )
        
        self.dynamic_preds[full_name] = (params, domain)
        if module:
            self.module_namespace[full_name] = module
        
        # Use simple name for HDF5 (no module prefix in database)
        db_name = name if module else full_name
        self.interp.hdf5.create_predicate(db_name, len(params))
    
    def resolve_name(self, name: str) -> str:
        """
        Resolve a predicate name, checking both local and module namespaces.
        Returns the full internal name (with :: prefix if from module).
        """
        # First check if it's already a fully qualified name
        if "::" in name:
            return name
        
        # Check local predicates first
        if name in self.static_preds or name in self.dynamic_preds:
            return name
        
        # If it's a dotted name, it might be a module reference
        # e.g., dplib.logistics.transport.route_optimal
        if "." in name:
            parts = name.split(".")
            # Try different splits: dplib.logistics.transport::route_optimal, etc.
            for i in range(len(parts) - 1, 0, -1):
                module_path = ".".join(parts[:i])
                pred_name = ".".join(parts[i:])
                full_name = f"{module_path}::{pred_name}"
                
                if full_name in self.static_preds or full_name in self.dynamic_preds:
                    return full_name
        
        # Not found in modules, return as-is
        return name
    
    def get_static(self, name: str) -> Optional[Tuple[List[str], Expr]]:
        """Get static predicate definition, resolving module names"""
        resolved = self.resolve_name(name)
        return self.static_preds.get(resolved)
    
    def get_dynamic(self, name: str) -> Optional[Tuple[List[str], Expr]]:
        """Get dynamic predicate definition, resolving module names"""
        resolved = self.resolve_name(name)
        return self.dynamic_preds.get(resolved)