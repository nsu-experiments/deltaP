#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Predicate manager for handling static and dynamic predicates.
"""

from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from .ast_nodes import Expr
from .exceptions import DeltaPNameError, DeltaPArityError

if TYPE_CHECKING:
    from .evaluator import Interpreter


class PredicateManager:
    """Manages static and dynamic predicates"""
    
    def __init__(self, interpreter: 'Interpreter'):
        self.interp = interpreter
        self.static_preds: Dict[str, Tuple[List[str], Expr]] = {}
        self.dynamic_preds: Dict[str, Tuple[List[str], Expr]] = {}
    
    def define_static(self, name: str, params: List[str], body: Expr, lineno: int = 0) -> None:
        """Define a static predicate with validation"""
        if name in self.interp.vars:
            raise DeltaPNameError(
                f"Static predicate '{name}' conflicts with existing variable", 
                lineno
            )
        if name in self.dynamic_preds:
            raise DeltaPNameError(
                f"Static predicate '{name}' conflicts with existing dynamic predicate", 
                lineno
            )
        self.static_preds[name] = (params, body)
    
    def define_dynamic(self, name: str, params: List[str], domain: Expr, lineno: int = 0) -> None:
        """Define a dynamic predicate with validation"""
        if name in self.interp.vars:
            raise DeltaPNameError(
                f"Dynamic predicate '{name}' conflicts with existing variable", 
                lineno
            )
        if name in self.static_preds:
            raise DeltaPNameError(
                f"Dynamic predicate '{name}' conflicts with existing static predicate", 
                lineno
            )
        if name in self.dynamic_preds:
            old_arity = len(self.dynamic_preds[name][0])
            new_arity = len(params)
            if old_arity != new_arity:
                raise DeltaPArityError(
                    f"Cannot change arity of '{name}' from {old_arity} to {new_arity}", 
                    lineno
                )
        self.dynamic_preds[name] = (params, domain)
        self.interp.hdf5.create_predicate(name, len(params))
    
    def get_static(self, name: str) -> Optional[Tuple[List[str], Expr]]:
        """Get static predicate definition"""
        return self.static_preds.get(name)
    
    def get_dynamic(self, name: str) -> Optional[Tuple[List[str], Expr]]:
        """Get dynamic predicate definition"""
        return self.dynamic_preds.get(name)