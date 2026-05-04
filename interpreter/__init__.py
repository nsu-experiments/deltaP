#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeltaP Interpreter Package

A modular probabilistic programming language interpreter combining
imperative, logical, and probabilistic capabilities.
"""

from .exceptions import (
    DeltaPError,
    DeltaPTypeError,
    DeltaPNameError,
    DeltaPArityError,
    DeltaPDomainError
)
from .ast_nodes import (
    Expr, Statement, Program,
    ConstExpr, VarExpr, UnaryExpr, BinaryExpr, CompareExpr,
    ListExpr, RangeExpr, QuantExpr, PredicateExpr
)
from .lexer import lexer, tokens
from .parser import DeltaParser
from .hdf5_manager import HDF5Manager
from .csv_exporter import CSVExporter
from .predicate_manager import PredicateManager
from .evaluator import Interpreter
from .delta_interpreter import main

__version__ = '1.0.0'
__author__ = 'Janne'

__all__ = [
    # Main entry point
    'main',
    
    # Core classes
    'Interpreter',
    'DeltaParser',
    'HDF5Manager',
    'CSVExporter',
    'PredicateManager',
    
    # Exceptions
    'DeltaPError',
    'DeltaPTypeError',
    'DeltaPNameError',
    'DeltaPArityError',
    'DeltaPDomainError',
    
    # AST nodes (for tooling/analysis)
    'Expr',
    'Statement',
    'Program',
]