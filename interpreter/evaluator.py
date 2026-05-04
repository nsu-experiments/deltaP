#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main interpreter/evaluator for DeltaP programs.
"""

import sys
import random
from typing import Dict, Any, Callable, Tuple
from .ast_nodes import *
from .exceptions import *
from .hdf5_manager import HDF5Manager
from .predicate_manager import PredicateManager
from .csv_exporter import CSVExporter
from datetime import datetime

class Interpreter:
    """DeltaP program interpreter"""
    
    def __init__(self, db_filename: str):
        self.hdf5 = HDF5Manager(db_filename)
        self.vars: Dict[str, Any] = {}
        self.predicates = PredicateManager(self)
        
        # For backward compatibility
        self.sp_defs = self.predicates.static_preds
        self.dp_defs = self.predicates.dynamic_preds
        
        # Evaluation mode and semantic functions
        self.mode: str = 'decision'
        self.not_func: Callable[[float], float] = lambda x: 1 - x
        self.and_func: Callable[[float, float], float] = lambda x, y: x * y
        self.or_func: Callable[[float, float], float] = lambda x, y: x + y - x * y
        self.imply_func: Callable[[float, float], float] = lambda x, y: 1 - x + x * y
        
        self.warnings_enabled: bool = True
        self.csv_exporter = None 
        self.program_name = None  
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self) -> None:
        """Close database connection"""
        self.hdf5.close()

    def set_warnings(self, enabled: bool) -> None:
        """Enable or disable warning messages"""
        self.warnings_enabled = enabled

    def eval_expr(self, expr: Expr, local: Dict[str, Any]) -> Any:
        """Evaluate an expression in given context"""
        if isinstance(expr, ConstExpr):
            return expr.value
        
        if isinstance(expr, VarExpr):
            if expr.name in local:
                return local[expr.name]
            if expr.name in self.vars:
                return self.vars[expr.name]
            raise DeltaPNameError(f"Undefined variable '{expr.name}'", expr.lineno)
        
        if isinstance(expr, UnaryExpr):
            arg = self.eval_expr(expr.arg, local)
            if expr.op == '-':
                return -arg
            if expr.op == '~':
                return self.not_func(arg)
            raise RuntimeError(f"Unknown unary op {expr.op}")
        
        if isinstance(expr, BinaryExpr):
            left = self.eval_expr(expr.left, local)
            right = self.eval_expr(expr.right, local)
            if expr.op == '+':
                return left + right
            if expr.op == '-':
                return left - right
            if expr.op == '*':
                return left * right
            if expr.op == '/':
                if right == 0:
                    raise DeltaPTypeError("Division by zero", expr.lineno)
                return left / right
            if expr.op == '%':
                return left % right
            if expr.op == '&':
                return self.and_func(left, right)
            if expr.op == '|':
                return self.or_func(left, right)
            if expr.op == '->':
                return self.imply_func(left, right)
            raise RuntimeError(f"Unknown binary op {expr.op}")
        
        if isinstance(expr, CompareExpr):
            left = self.eval_expr(expr.left, local)
            right = self.eval_expr(expr.right, local)
            if expr.op == '=':
                return 1.0 if left == right else 0.0
            if expr.op == '!=':
                return 1.0 if left != right else 0.0
            if expr.op == '<':
                return 1.0 if left < right else 0.0
            if expr.op == '<=':
                return 1.0 if left <= right else 0.0
            if expr.op == '>':
                return 1.0 if left > right else 0.0
            if expr.op == '>=':
                return 1.0 if left >= right else 0.0
            if expr.op == 'in':
                if isinstance(right, (list, range)):
                    return 1.0 if left in right else 0.0
                raise RuntimeError(
                    f"'in' operator requires list or range on right side at line {expr.lineno}"
                )
        
        if isinstance(expr, ListExpr):
            return [self.eval_expr(e, local) for e in expr.elements]
        
        if isinstance(expr, RangeExpr):
            s = self.eval_expr(expr.start, local)
            e = self.eval_expr(expr.end, local)
            if not isinstance(s, int) or not isinstance(e, int):
                raise DeltaPTypeError(
                    f"Range bounds must be integers, got {type(s).__name__} and {type(e).__name__}", 
                    expr.lineno
                )
            return list(range(s, e + 1))
        
        if isinstance(expr, QuantExpr):
            domain = self.eval_expr(expr.domain, local)
            if not isinstance(domain, list):
                raise RuntimeError(
                    f"Quantifier domain must be a list at line {expr.lineno}, got {type(domain).__name__}"
                )
            vals = []
            for val in domain:
                new_local = local.copy()
                new_local[expr.var] = val
                vals.append(self.eval_expr(expr.body, new_local))
            
            if expr.quant == '!':  # forall
                res = 1.0
                for v in vals:
                    res = self.and_func(res, v)
                return res
            else:  # exists
                res = 0.0
                for v in vals:
                    res = self.or_func(res, v)
                return res
        
        if isinstance(expr, PredicateExpr):
            name = expr.name
            args = [self.eval_expr(a, local) for a in expr.args]
            
            # Static predicate
            if name in self.sp_defs:
                params, body = self.sp_defs[name]
                if len(params) != len(args):
                    raise DeltaPArityError(
                        f"Static predicate '{name}' expects {len(params)} arguments, got {len(args)}", 
                        expr.lineno
                    )
                new_local = local.copy()
                for p, a in zip(params, args):
                    new_local[p] = a
                return self.eval_expr(body, new_local)
            
            # Dynamic predicate
            if name in self.dp_defs:
                params, domain = self.dp_defs[name]
                if len(params) != len(args):
                    raise DeltaPArityError(
                        f"Dynamic predicate '{name}' expects {len(params)} arguments, got {len(args)}", 
                        expr.lineno
                    )
                new_local = local.copy()
                for p, a in zip(params, args):
                    new_local[p] = a
                
                domain_val = self.eval_expr(domain, new_local)
                if domain_val < 0.5:
                    if self.warnings_enabled:
                        print(
                            f"WARNING: Predicate '{name}{tuple(args)}' called outside its domain "
                            f"at line {expr.lineno}, using default probability 0.5", 
                            file=sys.stderr
                        )
                    if self.mode == 'decision':
                        return 0.5
                    else:
                        return 1.0 if random.random() < 0.5 else 0.0
                
                prob = self.compute_dynamic_prob(name, tuple(args))
                if self.mode == 'decision':
                    return prob
                else:
                    return 1.0 if random.random() < prob else 0.0
            
            # Built-in type predicates
            if name == 'nat':
                return 1.0 if isinstance(args[0], int) and args[0] >= 0 else 0.0
            if name == 'int':
                return 1.0 if isinstance(args[0], int) else 0.0
            if name == 'float':
                return 1.0 if isinstance(args[0], float) else 0.0
            if name == 'bool':
                return 1.0 if isinstance(args[0], bool) else 0.0
            if name == 'string':
                return 1.0 if isinstance(args[0], str) else 0.0
            if name == 'list':
                return 1.0 if isinstance(args[0], list) else 0.0
            if name == 'range':
                return 1.0 if isinstance(args[0], range) else 0.0
            
            raise DeltaPNameError(f"Undefined predicate '{name}'", expr.lineno)
        
        raise DeltaPError(
            f"Unknown expression type {type(expr).__name__}", 
            getattr(expr, 'lineno', 0)
        )
    
    def compute_dynamic_prob(self, pred: str, args: Tuple[int, ...]) -> float:
        """Compute probability for dynamic predicate from stored data"""
        params, domain = self.dp_defs[pred]
        entries = self.hdf5.get_all_entries(pred)
        pos = neg = 0
        
        for entry_args, value in entries:
            if len(entry_args) != len(params):
                continue
            if entry_args != args:
                continue
            bind = {p: a for p, a in zip(params, entry_args)}
            if self.eval_expr(domain, bind) > 0.5:
                if value == 1:
                    pos += 1
                else:
                    neg += 1
        
        total = pos + neg
        
        if total == 0:
            if self.warnings_enabled:
                print(
                    f"WARNING: No data for predicate '{pred}{args}', using default probability 0.5", 
                    file=sys.stderr
                )
            return 0.5
        elif total < 5:
            if self.warnings_enabled:
                print(
                    f"WARNING: Only {total} data point(s) for predicate '{pred}{args}', "
                    f"probability may be unreliable", 
                    file=sys.stderr
                )
        
        return pos / total

    def execute_statement(self, stmt: Statement) -> None:
        """Execute a single statement"""
        if isinstance(stmt, AssignStmt):
            self.vars[stmt.var] = self.eval_expr(stmt.expr, {})
        
        elif isinstance(stmt, DPSemDecl):
            if stmt.mode not in ('decision', 'simulation'):
                raise RuntimeError(
                    f"Invalid dpSem mode '{stmt.mode}' at line {stmt.lineno}. "
                    f"Must be 'decision' or 'simulation'"
                )
            self.mode = stmt.mode
        
        elif isinstance(stmt, AndSemDecl):
            expr = stmt.expr
            self.and_func = lambda x, y: self.eval_expr(expr, {'x': x, 'y': y})
        
        elif isinstance(stmt, OrSemDecl):
            expr = stmt.expr
            self.or_func = lambda x, y: self.eval_expr(expr, {'x': x, 'y': y})
        
        elif isinstance(stmt, ImplySemDecl):
            expr = stmt.expr
            self.imply_func = lambda x, y: self.eval_expr(expr, {'x': x, 'y': y})
        
        elif isinstance(stmt, NotSemDecl):
            expr = stmt.expr
            self.not_func = lambda x: self.eval_expr(expr, {'x': x})
        
        elif isinstance(stmt, InputStmt):
            for v in stmt.vars:
                try:
                    val = input(f"Enter {v}: ")
                    try:
                        val = int(val) if '.' not in val else float(val)
                    except:
                        pass
                    self.vars[v] = val
                except EOFError:
                    raise RuntimeError(
                        f"Input interrupted at line {stmt.lineno} while reading variable '{v}'"
                    )
        
        elif isinstance(stmt, OutputStmt):
            vals = [self.eval_expr(e, {}) for e in stmt.exprs]
            output_line = ' '.join(str(v) for v in vals)
            print(output_line)
            
            # Collect for CSV export - save raw line without quotes
            if self.csv_exporter:
                # Check if this looks like CSV data (contains commas)
                if ',' in output_line and not output_line.startswith('==='):
                    # Write raw to file, not as pandas row
                    with open(self.csv_exporter.filename, 'a') as f:
                        f.write(output_line.replace(' ', '') + '\n')
        elif isinstance(stmt, IfStmt):
            cond_val = self.eval_expr(stmt.cond, {})
            if cond_val >= 0.5:
                self.execute_statement(stmt.then_stmt)
            elif stmt.else_stmt:
                self.execute_statement(stmt.else_stmt)
        
        elif isinstance(stmt, ForStmt):
            coll = self.eval_expr(stmt.collection, {})
            if not isinstance(coll, list):
                raise RuntimeError(
                    f"For loop collection must be a list at line {stmt.lineno}, "
                    f"got {type(coll).__name__}"
                )
            for val in coll:
                self.vars[stmt.var] = val
                self.execute_statement(stmt.body)
        
        elif isinstance(stmt, BlockStmt):
            for s in stmt.statements:
                self.execute_statement(s)
        
        elif isinstance(stmt, DynamicAssignStmt):
            pred = stmt.pred
            if pred not in self.dp_defs:
                raise RuntimeError(
                    f"Dynamic predicate '{pred}' not declared at line {stmt.lineno}"
                )
            params, _ = self.dp_defs[pred]
            args = [self.eval_expr(a, {}) for a in stmt.args]
            if len(args) != len(params):
                raise RuntimeError(
                    f"Predicate '{pred}' expects {len(params)} arguments, "
                    f"got {len(args)} at line {stmt.lineno}"
                )
            for i, a in enumerate(args):
                if not isinstance(a, int):
                    raise RuntimeError(
                        f"Dynamic predicate '{pred}' argument {i+1} must be integer "
                        f"at line {stmt.lineno}, got {type(a).__name__}"
                    )
            code = {'true': 1, 'false': 0, 'undef': 2}[stmt.value]
            self.hdf5.set_value(pred, tuple(args), code)
        
        elif isinstance(stmt, StaticPredDecl):
            if stmt.name in self.vars:
                raise RuntimeError(
                    f"Static predicate '{stmt.name}' conflicts with existing variable "
                    f"at line {stmt.lineno}"
                )
            if stmt.name in self.dp_defs:
                raise RuntimeError(
                    f"Static predicate '{stmt.name}' conflicts with existing dynamic predicate "
                    f"at line {stmt.lineno}"
                )
            self.sp_defs[stmt.name] = (stmt.params, stmt.body)
        
        elif isinstance(stmt, DynamicPredDecl):
            if stmt.name in self.vars:
                raise RuntimeError(
                    f"Dynamic predicate '{stmt.name}' conflicts with existing variable "
                    f"at line {stmt.lineno}"
                )
            if stmt.name in self.sp_defs:
                raise RuntimeError(
                    f"Dynamic predicate '{stmt.name}' conflicts with existing static predicate "
                    f"at line {stmt.lineno}"
                )
            if stmt.name in self.dp_defs:
                old_arity = len(self.dp_defs[stmt.name][0])
                new_arity = len(stmt.params)
                if old_arity != new_arity:
                    raise RuntimeError(
                        f"Cannot change arity of dynamic predicate '{stmt.name}' "
                        f"from {old_arity} to {new_arity} at line {stmt.lineno}"
                    )
            self.dp_defs[stmt.name] = (stmt.params, stmt.domain)
            self.hdf5.create_predicate(stmt.name, len(stmt.params))
        
        else:
            raise RuntimeError(
                f"Unknown statement type {type(stmt).__name__} at line {getattr(stmt, 'lineno', 0)}"
            )

    def run_program(self, prog: Program):
        # Initialize CSV exporter based on mode
        for stmt in prog.statements:
            if isinstance(stmt, DPSemDecl):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.csv_exporter = CSVExporter(f"{stmt.mode}_results_{timestamp}")
                break
        
        # Execute program
        for stmt in prog.statements:
            self.execute_statement(stmt)
        
        # Export CSV if enabled
        if self.csv_exporter:
            self.csv_exporter.write()
