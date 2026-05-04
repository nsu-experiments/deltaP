#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract Syntax Tree node definitions for DeltaP.
"""

from dataclasses import dataclass
from typing import List, Any, Optional


# ----------------------------------------------------------------------
#                           EXPRESSION NODES
# ----------------------------------------------------------------------

class Expr:
    """Base class for all expressions"""
    lineno: int = 0


@dataclass
class ConstExpr(Expr):
    """Constant literal: 42, 3.14, "hello" """
    value: Any


@dataclass
class VarExpr(Expr):
    """Variable reference: x, myVar"""
    name: str


@dataclass
class UnaryExpr(Expr):
    """Unary operation: -x, ~p"""
    op: str
    arg: Expr


@dataclass
class BinaryExpr(Expr):
    """Binary operation: x + y, p & q"""
    op: str
    left: Expr
    right: Expr


@dataclass
class ListExpr(Expr):
    """List literal: [1, 2, 3]"""
    elements: List[Expr]


@dataclass
class RangeExpr(Expr):
    """Range expression: [1:10]"""
    start: Expr
    end: Expr


@dataclass
class CompareExpr(Expr):
    """Comparison: x = y, a < b, v in Set"""
    op: str
    left: Expr
    right: Expr


@dataclass
class QuantExpr(Expr):
    """Quantified expression: !x:[1:10](p(x)), ?y:Domain(q(y))"""
    quant: str  # '!' (forall) or '?' (exists)
    var: str
    domain: Expr
    body: Expr


@dataclass
class PredicateExpr(Expr):
    """Predicate call: incident(d, m, sh)"""
    name: str
    args: List[Expr]


# ----------------------------------------------------------------------
#                           STATEMENT NODES
# ----------------------------------------------------------------------

class Statement:
    """Base class for all statements"""
    lineno: int = 0


@dataclass
class DPSemDecl(Statement):
    """dpSem mode declaration: dpSem decision;"""
    mode: str


@dataclass
class AndSemDecl(Statement):
    """andSem declaration: andSem x y := expr;"""
    x: str
    y: str
    expr: Expr


@dataclass
class OrSemDecl(Statement):
    """orSem declaration: orSem x y := expr;"""
    x: str
    y: str
    expr: Expr


@dataclass
class NotSemDecl(Statement):
    """notSem declaration: notSem x := expr;"""
    x: str
    expr: Expr


@dataclass
class ImplySemDecl(Statement):
    """implySem declaration: implySem x y := expr;"""
    x: str
    y: str
    expr: Expr


@dataclass
class StaticPredDecl(Statement):
    """Static predicate: sp winter(m) := m = 12 | m = 1 | m = 2;"""
    name: str
    params: List[str]
    body: Expr


@dataclass
class DynamicPredDecl(Statement):
    """Dynamic predicate: dp incident(d, m, sh, w, s) : d in District & ...;"""
    name: str
    params: List[str]
    domain: Expr


@dataclass
class AssignStmt(Statement):
    """Variable assignment: x := 42;"""
    var: str
    expr: Expr


@dataclass
class InputStmt(Statement):
    """Input statement: input(x, y, z);"""
    vars: List[str]


@dataclass
class OutputStmt(Statement):
    """Output statement: output("Result: ", x);"""
    exprs: List[Expr]


@dataclass
class IfStmt(Statement):
    """Conditional: if(cond) then stmt else stmt"""
    cond: Expr
    then_stmt: Statement
    else_stmt: Optional[Statement]


@dataclass
class ForStmt(Statement):
    """For loop: for x in Set do stmt"""
    var: str
    collection: Expr
    body: Statement


@dataclass
class BlockStmt(Statement):
    """Block of statements: { stmt1; stmt2; }"""
    statements: List[Statement]


@dataclass
class DynamicAssignStmt(Statement):
    """Dynamic predicate assignment: incident(1, 1, 1, 1, 1) := true;"""
    pred: str
    args: List[Expr]
    value: str  # 'true', 'false', or 'undef'


@dataclass
class Program:
    """Root program node"""
    statements: List[Statement]