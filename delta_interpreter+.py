#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Callable

import h5py
import numpy as np
from ply import lex, yacc

# ----------------------------------------------------------------------
#                                   TOKENS
# -----------------------------------------orSem-----------------------------
tokens = (
    'SP', 'DP', 'IF', 'THEN', 'ELSE', 'FOR', 'DO',
    'INPUT', 'OUTPUT', 'TRUE', 'FALSE', 'UNDEF',
    'DPSEM', 'ANDSEM', 'ORSEM', 'NOTSEM', 'IMPLYSEM',
    'ASSIGN', 'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT', 'IMPLIES', 'INOP',
    'FORALL', 'EXISTS',
    'COLON', 'SEMICOLON', 'COMMA',
    'LPAREN', 'RPAREN', 'LBRACK', 'RBRACK', 'LBRACE', 'RBRACE',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'NUMBER', 'STRING', 'ID'
)

# Reserved words – must be defined before lexing
reserved = {
    'sp': 'SP', 'dp': 'DP', 'if': 'IF', 'then': 'THEN', 'else': 'ELSE',
    'for': 'FOR', 'in': 'INOP', 'do': 'DO', 'input': 'INPUT', 'output': 'OUTPUT',
    'true': 'TRUE', 'false': 'FALSE', 'undef': 'UNDEF',
    'dpSem': 'DPSEM', 'andSem': 'ANDSEM', 'orSem': 'ORSEM',
    'notSem': 'NOTSEM', 'implySem': 'IMPLYSEM',
    '!': 'FORALL', '?': 'EXISTS'
}

# Simple tokens
t_ASSIGN = r':='
t_EQ = r'='
t_NEQ = r'!='
t_LT = r'<'
t_LE = r'<='
t_GT = r'>'
t_GE = r'>='
t_AND = r'&'
t_OR = r'\|'
t_NOT = r'~'
t_IMPLIES = r'->'
t_INOP = r'in'
t_COLON = r':'
t_SEMICOLON = r';'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACK = r'\['
t_RBRACK = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

def t_NUMBER(t):
    r'-?\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_STRING(t):
    r'"[^"\\]*(\\.[^"\\]*)*"'
    t.value = t.value[1:-1]  # remove quotes
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# def t_comment(t):
#    r';.*'
#    pass

def t_error(t):
    raise SyntaxError(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")

lexer = lex.lex()

# ----------------------------------------------------------------------
#                                   AST
# ----------------------------------------------------------------------

class Expr:
    lineno: int = 0

@dataclass
class ConstExpr(Expr):
    value: Any

@dataclass
class VarExpr(Expr):
    name: str

@dataclass
class UnaryExpr(Expr):
    op: str
    arg: Expr

@dataclass
class BinaryExpr(Expr):
    op: str
    left: Expr
    right: Expr

@dataclass
class ListExpr(Expr):
    elements: List[Expr]

@dataclass
class RangeExpr(Expr):
    start: Expr
    end: Expr

@dataclass
class CompareExpr(Expr):
    op: str
    left: Expr
    right: Expr

@dataclass
class QuantExpr(Expr):
    quant: str  # '!' or '?'
    var: str
    domain: Expr
    body: Expr

@dataclass
class PredicateExpr(Expr):
    name: str
    args: List[Expr]

class Statement:
    lineno: int = 0

@dataclass
class DPSemDecl(Statement):
    mode: str

@dataclass
class AndSemDecl(Statement):
    x: str
    y: str
    expr: Expr

@dataclass
class OrSemDecl(Statement):
    x: str
    y: str
    expr: Expr

@dataclass
class NotSemDecl(Statement):
    x: str
    expr: Expr

@dataclass
class ImplySemDecl(Statement):
    x: str
    y: str
    expr: Expr

@dataclass
class StaticPredDecl(Statement):
    name: str
    params: List[str]
    body: Expr

@dataclass
class DynamicPredDecl(Statement):
    name: str
    params: List[str]
    domain: Expr

@dataclass
class AssignStmt(Statement):
    var: str
    expr: Expr

@dataclass
class InputStmt(Statement):
    vars: List[str]

@dataclass
class OutputStmt(Statement):
    exprs: List[Expr]

@dataclass
class IfStmt(Statement):
    cond: Expr
    then_stmt: Statement
    else_stmt: Optional[Statement]

@dataclass
class ForStmt(Statement):
    var: str
    collection: Expr
    body: Statement

@dataclass
class BlockStmt(Statement):
    statements: List[Statement]

@dataclass
class DynamicAssignStmt(Statement):
    pred: str
    args: List[Expr]
    value: str  # 'true', 'false', 'undef'

@dataclass
class Program:
    statements: List[Statement]

# ----------------------------------------------------------------------
#                                   PARSER
# ----------------------------------------------------------------------
class DeltaParser:
    tokens = tokens
    precedence = (
        ('left', 'AND', 'OR', 'IMPLIES'),
        ('right', 'NOT'),
        ('nonassoc', 'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE', 'INOP'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD'),
        ('right', 'UMINUS'),
    )

    def __init__(self):
        self.parser = yacc.yacc(module=self, start='program', debug=False, write_tables=False)

    # Program
    def p_program(self, p):
        '''program : statements'''
        p[0] = Program(p[1])

    # Statements
    def p_statement(self, p):
        '''statement : dpSem_decl
                     | andSem_decl
                     | orSem_decl
                     | notSem_decl
                     | implySem_decl
                     | sp_decl
                     | dp_decl
                     | assign_stmt
                     | input_stmt
                     | output_stmt
                     | if_stmt
                     | for_stmt
                     | block_stmt
                     | dynamic_assign_stmt'''
        p[0] = p[1]

    def p_dpSem_decl(self, p):
        '''dpSem_decl : DPSEM ID SEMICOLON'''
        p[0] = DPSemDecl(p[2])
        p[0].lineno = p.lineno(1)

    def p_andSem_decl(self, p):
        '''andSem_decl : ANDSEM ID ID ASSIGN expr SEMICOLON'''
        p[0] = AndSemDecl(p[2], p[3], p[5])
        p[0].lineno = p.lineno(1)

    def p_orSem_decl(self, p):
        '''orSem_decl : ORSEM ID ID ASSIGN expr SEMICOLON'''
        p[0] = OrSemDecl(p[2], p[3], p[5])
        p[0].lineno = p.lineno(1)

    def p_notSem_decl(self, p):
        '''notSem_decl : NOTSEM ID ASSIGN expr SEMICOLON'''
        p[0] = NotSemDecl(p[2], p[4])
        p[0].lineno = p.lineno(1)

    def p_implySem_decl(self, p):
        '''implySem_decl : IMPLYSEM ID ID ASSIGN expr SEMICOLON'''
        p[0] = ImplySemDecl(p[2], p[3], p[5])
        p[0].lineno = p.lineno(1)

    def p_sp_decl(self, p):
        '''sp_decl : SP ID LPAREN param_list RPAREN ASSIGN expr SEMICOLON'''
        p[0] = StaticPredDecl(p[2], p[4], p[7])
        p[0].lineno = p.lineno(1)

    def p_dp_decl(self, p):
        '''dp_decl : DP ID LPAREN param_list RPAREN COLON expr SEMICOLON'''
        p[0] = DynamicPredDecl(p[2], p[4], p[7])
        p[0].lineno = p.lineno(1)

    def p_assign_stmt(self, p):
        '''assign_stmt : ID ASSIGN expr SEMICOLON'''
        p[0] = AssignStmt(p[1], p[3])
        p[0].lineno = p.lineno(1)

    def p_input_stmt(self, p):
        '''input_stmt : INPUT LPAREN id_list RPAREN SEMICOLON'''
        p[0] = InputStmt(p[3])
        p[0].lineno = p.lineno(1)

    def p_output_stmt(self, p):
        '''output_stmt : OUTPUT LPAREN expr_list RPAREN SEMICOLON'''
        p[0] = OutputStmt(p[3])
        p[0].lineno = p.lineno(1)

    def p_if_stmt(self, p):
        '''if_stmt : IF LPAREN expr RPAREN THEN statement ELSE statement
                | IF LPAREN expr RPAREN THEN statement'''
        if len(p) == 9:
            p[0] = IfStmt(p[3], p[6], p[8])
        else:
            p[0] = IfStmt(p[3], p[6], None)
        p[0].lineno = p.lineno(1)

    def p_for_stmt(self, p):
        '''for_stmt : FOR ID INOP expr DO statement'''
        p[0] = ForStmt(p[2], p[4], p[6])
        p[0].lineno = p.lineno(1)

    def p_block_stmt(self, p):
        '''block_stmt : LBRACE statements RBRACE'''
        p[0] = BlockStmt(p[2])
        p[0].lineno = p.lineno(1)

    def p_dynamic_assign_stmt(self, p):
        '''dynamic_assign_stmt : ID LPAREN expr_list RPAREN ASSIGN TRUE SEMICOLON
                            | ID LPAREN expr_list RPAREN ASSIGN FALSE SEMICOLON
                            | ID LPAREN expr_list RPAREN ASSIGN UNDEF SEMICOLON'''
        value_str = p[6].value if hasattr(p[6], 'value') else p[6]
        p[0] = DynamicAssignStmt(p[1], p[3], value_str)
        p[0].lineno = p.lineno(1)
    # Helpers
    def p_param_list(self, p):
        '''param_list : ID
                    | ID COMMA param_list'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_statements(self, p):
        '''statements : statement statements
                    | empty'''
        if len(p) == 3:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = []
    def p_id_list(self, p):
        '''id_list : ID
                   | ID COMMA id_list'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_expr_list(self, p):
        '''expr_list : expr
                     | expr COMMA expr_list'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

        # Expressions
    def p_expr(self, p):
        '''expr : NUMBER
                | STRING
                | TRUE
                | FALSE
                | ID
                | MINUS expr %prec UMINUS
                | expr PLUS expr
                | expr MINUS expr
                | expr TIMES expr
                | expr DIVIDE expr
                | expr MOD expr
                | expr EQ expr
                | expr NEQ expr
                | expr LT expr
                | expr LE expr
                | expr GT expr
                | expr GE expr
                | expr INOP expr %prec INOP
                | NOT expr
                | expr AND expr
                | expr OR expr
                | expr IMPLIES expr
                | LPAREN expr RPAREN
                | FORALL ID COLON expr LPAREN expr RPAREN
                | EXISTS ID COLON expr LPAREN expr RPAREN
                | ID LPAREN expr_list RPAREN
                | LBRACK expr_list RBRACK
                | LBRACK expr COLON expr RBRACK'''
        # Constant or variable
        if len(p) == 2:
            tok_type = p.slice[1].type
            if tok_type == 'NUMBER':
                p[0] = ConstExpr(p[1])
                p[0].lineno = p.lineno(1)
            elif tok_type == 'STRING':
                p[0] = ConstExpr(p[1])
                p[0].lineno = p.lineno(1)
            elif tok_type == 'TRUE':
                p[0] = ConstExpr(1.0)
                p[0].lineno = p.lineno(1)
            elif tok_type == 'FALSE':
                p[0] = ConstExpr(0.0)
                p[0].lineno = p.lineno(1)
            elif tok_type == 'ID':
                p[0] = VarExpr(p[1])
                p[0].lineno = p.lineno(1)
            else:
                p[0] = ConstExpr(p[1]) if not isinstance(p[1], str) else VarExpr(p[1])
                p[0].lineno = p.lineno(1)
        # Unary operators
        elif p[1] == '-':
            p[0] = UnaryExpr('-', p[2])
            p[0].lineno = p.lineno(1)
        elif p[1] == '~':
            p[0] = UnaryExpr('~', p[2])
            p[0].lineno = p.lineno(1)
        # Binary operators
        elif p[2] in ('+', '-', '*', '/', '%', '=', '!=', '<', '<=', '>', '>=', 'in', '&', '|', '->'):
            if p[2] in ('&', '|', '->'):
                p[0] = BinaryExpr(p[2], p[1], p[3])
            elif p[2] in ('=', '!=', '<', '<=', '>', '>=', 'in'):
                p[0] = CompareExpr(p[2], p[1], p[3])
            else:
                p[0] = BinaryExpr(p[2], p[1], p[3])
            p[0].lineno = p.lineno(2)  # Use operator position
        # Parentheses
        elif p[1] == '(':
            p[0] = p[2]  # Inherit lineno from inner expr
        # Quantifiers
        elif p[1] == '!':
            p[0] = QuantExpr('!', p[2], p[4], p[6])
            p[0].lineno = p.lineno(1)
        elif p[1] == '?':
            p[0] = QuantExpr('?', p[2], p[4], p[6])
            p[0].lineno = p.lineno(1)
        # Predicate call
        elif len(p) == 5 and p[2] == '(':
            p[0] = PredicateExpr(p[1], p[3])
            p[0].lineno = p.lineno(1)
        # List
        elif p[1] == '[' and len(p) == 4:
            p[0] = ListExpr(p[2])
            p[0].lineno = p.lineno(1)
        # Range
        elif p[1] == '[' and p[3] == ':':
            p[0] = RangeExpr(p[2], p[4])
            p[0].lineno = p.lineno(1)

    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        if p:
            raise SyntaxError(f"Syntax error at '{p.value}', line {p.lineno}")
        else:
            raise SyntaxError("Syntax error at EOF")

    def parse(self, text):
        return self.parser.parse(text, lexer=lexer)


# ----------------------------------------------------------------------
#                           HDF5 MANAGER
# ----------------------------------------------------------------------
class HDF5Manager:
    def __init__(self, filename: str):
        self.filename = filename
        self.h5file = h5py.File(filename, 'a')

    def close(self):
        self.h5file.close()

    def create_predicate(self, name: str, arity: int):
        if name in self.h5file:
            return
        fields = [(f'arg{i}', 'int64') for i in range(arity)] + [('value', 'int8')]
        self.h5file.create_dataset(name, shape=(0,), dtype=np.dtype(fields), maxshape=(None,))

    def set_value(self, pred: str, args: Tuple[int, ...], value: int):
        ds = self.h5file[pred]
        arity = len([f for f in ds.dtype.names if f.startswith('arg')])
        idx = None
        for i, row in enumerate(ds):
            if all(row[f'arg{j}'] == args[j] for j in range(arity)):
                idx = i
                break
        if value == 2:  # undef -> delete
            if idx is not None:
                new_data = np.delete(ds[:], idx, axis=0)
                ds.resize((len(new_data),))
                ds[:] = new_data
            return
        row = tuple(args) + (value,)
        if idx is not None:
            ds[idx] = row
        else:
            ds.resize((ds.shape[0] + 1,))
            ds[-1] = row

    def get_all_entries(self, pred: str) -> List[Tuple[Tuple[int, ...], int]]:
        ds = self.h5file[pred]
        arity = len([f for f in ds.dtype.names if f.startswith('arg')])
        result = []
        for row in ds:
            if row['value'] in (0, 1):
                args = tuple(row[f'arg{i}'] for i in range(arity))
                result.append((args, int(row['value'])))
        return result


# ----------------------------------------------------------------------
#                           INTERPRETER
# ----------------------------------------------------------------------
class Interpreter:
    def __init__(self, db_filename: str):
        self.hdf5 = HDF5Manager(db_filename)
        self.vars = {}
        self.sp_defs = {}
        self.dp_defs = {}
        self.mode = 'decision'
        self.not_func = lambda x: 1 - x
        self.and_func = lambda x, y: x * y
        self.or_func = lambda x, y: x + y - x * y
        self.imply_func = lambda x, y: 1 - x + x * y
        self.warnings_enabled = True 

    def close(self):
        self.hdf5.close()

    def eval_expr(self, expr: Expr, local: Dict) -> Any:
        if isinstance(expr, ConstExpr):
            return expr.value
        if isinstance(expr, VarExpr):
            if expr.name in local:
                return local[expr.name]
            if expr.name in self.vars:
                return self.vars[expr.name]
            raise RuntimeError(f"Undefined variable {expr.name}")
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
                        # ENHANCED ERROR:
                    raise RuntimeError(f"'in' operator requires list or range on right side at line {expr.lineno}")
        if isinstance(expr, ListExpr):
            return [self.eval_expr(e, local) for e in expr.elements]
        if isinstance(expr, RangeExpr):
            s = self.eval_expr(expr.start, local)
            e = self.eval_expr(expr.end, local)
            if not isinstance(s, int) or not isinstance(e, int):
                # ENHANCED ERROR:
                raise RuntimeError(f"Range bounds must be integers at line {expr.lineno}, got {type(s).__name__} and {type(e).__name__}")
            return list(range(s, e + 1))
        if isinstance(expr, QuantExpr):
            domain = self.eval_expr(expr.domain, local)
            if not isinstance(domain, list):
                # ENHANCED ERROR:
                raise RuntimeError(f"Quantifier domain must be a list at line {expr.lineno}, got {type(domain).__name__}")
            vals = []
            for val in domain:
                new_local = local.copy()
                new_local[expr.var] = val
                vals.append(self.eval_expr(expr.body, new_local))
            if expr.quant == '!':
                res = 1.0
                for v in vals:
                    res = self.and_func(res, v)
                return res
            else:  # '?'
                res = 0.0
                for v in vals:
                    res = self.or_func(res, v)
                return res
        if isinstance(expr, PredicateExpr):
            name = expr.name
            args = [self.eval_expr(a, local) for a in expr.args]
            # static predicate
            if name in self.sp_defs:
                params, body = self.sp_defs[name]
                if len(params) != len(args):
                    # ENHANCED ERROR:
                    raise RuntimeError(f"Static predicate '{name}' expects {len(params)} arguments, got {len(args)} at line {expr.lineno}")
                new_local = local.copy()
                for p, a in zip(params, args):
                    new_local[p] = a
                return self.eval_expr(body, new_local)
            # dynamic predicate
            if name in self.dp_defs:
                params, domain = self.dp_defs[name]
                if len(params) != len(args):
                    raise RuntimeError(f"Dynamic predicate '{name}' expects {len(params)} arguments, got {len(args)} at line {expr.lineno}")
                new_local = local.copy()
                for p, a in zip(params, args):
                    new_local[p] = a
                domain_val = self.eval_expr(domain, new_local)
                if domain_val < 0.5:
                    # ENHANCED: Warn about out-of-domain call
                    if self.warnings_enabled:
                        print(f"WARNING: Predicate '{name}{tuple(args)}' called outside its domain at line {expr.lineno}, using default probability 0.5", file=sys.stderr)
                    if self.mode == 'decision':
                        return 0.5
                    else:
                        return 1.0 if random.random() < 0.5 else 0.0
                prob = self.compute_dynamic_prob(name, tuple(args))
                if self.mode == 'decision':
                    return prob
                else:
                    return 1.0 if random.random() < prob else 0.0
            # built-in predicates (keep existing checks)
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
            # ENHANCED ERROR:
            raise RuntimeError(f"Undefined predicate '{name}' at line {expr.lineno}")
        # ENHANCED ERROR:
        raise RuntimeError(f"Unknown expression type {type(expr).__name__} at line {getattr(expr, 'lineno', 0)}")

    def compute_dynamic_prob(self, pred: str, args: Tuple) -> float:
        params, domain = self.dp_defs[pred]
        entries = self.hdf5.get_all_entries(pred)
        pos = neg = 0
        for entry_args, value in entries:
            if len(entry_args) != len(params):
                continue
            bind = {p: a for p, a in zip(params, entry_args)}
            if self.eval_expr(domain, bind) > 0.5:
                if value == 1:
                    pos += 1
                else:
                    neg += 1
        total = pos + neg
        
        # ENHANCED: Warn about insufficient data
        if total == 0:
            if self.warnings_enabled:
                print(f"WARNING: No data for predicate '{pred}{args}', using default probability 0.5", file=sys.stderr)
            return 0.5
        elif total < 5:  # Warn if very few data points
            if self.warnings_enabled:
                print(f"WARNING: Only {total} data point(s) for predicate '{pred}{args}', probability may be unreliable", file=sys.stderr)
        
        return pos / total
    
    def set_warnings(self, enabled: bool):
        """Enable or disable warning messages"""
        self.warnings_enabled = enabled

    def execute_statement(self, stmt: Statement):
        if isinstance(stmt, AssignStmt):
            self.vars[stmt.var] = self.eval_expr(stmt.expr, {})
        elif isinstance(stmt, DPSemDecl):
            # ENHANCED: Validate mode
            if stmt.mode not in ('decision', 'simulation'):
                raise RuntimeError(f"Invalid dpSem mode '{stmt.mode}' at line {stmt.lineno}. Must be 'decision' or 'simulation'")
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
                    # ENHANCED: Handle Ctrl+D gracefully
                    raise RuntimeError(f"Input interrupted at line {stmt.lineno} while reading variable '{v}'")
        elif isinstance(stmt, OutputStmt):
            vals = [str(self.eval_expr(e, {})) for e in stmt.exprs]
            print(' '.join(vals))
        elif isinstance(stmt, IfStmt):
            cond_val = self.eval_expr(stmt.cond, {})
            if cond_val >= 0.5:
                self.execute_statement(stmt.then_stmt)
            elif stmt.else_stmt:
                self.execute_statement(stmt.else_stmt)
        elif isinstance(stmt, ForStmt):
            coll = self.eval_expr(stmt.collection, {})
            if not isinstance(coll, list):
                # ENHANCED ERROR:
                raise RuntimeError(f"For loop collection must be a list at line {stmt.lineno}, got {type(coll).__name__}")
            for val in coll:
                self.vars[stmt.var] = val
                self.execute_statement(stmt.body)
        elif isinstance(stmt, BlockStmt):
            for s in stmt.statements:
                self.execute_statement(s)
        elif isinstance(stmt, DynamicAssignStmt):
            pred = stmt.pred
            if pred not in self.dp_defs:
                # ENHANCED ERROR:
                raise RuntimeError(f"Dynamic predicate '{pred}' not declared at line {stmt.lineno}")
            params, _ = self.dp_defs[pred]
            args = [self.eval_expr(a, {}) for a in stmt.args]
            if len(args) != len(params):
                # ENHANCED ERROR:
                raise RuntimeError(f"Predicate '{pred}' expects {len(params)} arguments, got {len(args)} at line {stmt.lineno}")
            for i, a in enumerate(args):
                if not isinstance(a, int):
                    # ENHANCED ERROR:
                    raise RuntimeError(f"Dynamic predicate '{pred}' argument {i+1} must be integer at line {stmt.lineno}, got {type(a).__name__}")
            code = {'true': 1, 'false': 0, 'undef': 2}[stmt.value]
            self.hdf5.set_value(pred, tuple(args), code)
        elif isinstance(stmt, StaticPredDecl):
            # ENHANCED: Check for name conflicts
            if stmt.name in self.vars:
                raise RuntimeError(f"Static predicate '{stmt.name}' conflicts with existing variable at line {stmt.lineno}")
            if stmt.name in self.dp_defs:
                raise RuntimeError(f"Static predicate '{stmt.name}' conflicts with existing dynamic predicate at line {stmt.lineno}")
            self.sp_defs[stmt.name] = (stmt.params, stmt.body)
        elif isinstance(stmt, DynamicPredDecl):
            # ENHANCED: Check for name conflicts
            if stmt.name in self.vars:
                raise RuntimeError(f"Dynamic predicate '{stmt.name}' conflicts with existing variable at line {stmt.lineno}")
            if stmt.name in self.sp_defs:
                raise RuntimeError(f"Dynamic predicate '{stmt.name}' conflicts with existing static predicate at line {stmt.lineno}")
            if stmt.name in self.dp_defs:
                old_arity = len(self.dp_defs[stmt.name][0])
                new_arity = len(stmt.params)
                if old_arity != new_arity:
                    # ENHANCED ERROR:
                    raise RuntimeError(f"Cannot change arity of dynamic predicate '{stmt.name}' from {old_arity} to {new_arity} at line {stmt.lineno}")
            self.dp_defs[stmt.name] = (stmt.params, stmt.domain)
            self.hdf5.create_predicate(stmt.name, len(stmt.params))
        else:
            # ENHANCED ERROR:
            raise RuntimeError(f"Unknown statement type {type(stmt).__name__} at line {getattr(stmt, 'lineno', 0)}")

    def run_program(self, prog: Program):
        for stmt in prog.statements:
            self.execute_statement(stmt)


# ----------------------------------------------------------------------
#                                   MAIN
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python delta_interpreter.py program.dp [database.h5]")
        sys.exit(1)
    prog_file = sys.argv[1]
    db_file = sys.argv[2] if len(sys.argv) > 2 else "delta_db.h5"
    with open(prog_file, 'r', encoding='utf-8-sig') as f:
        source = f.read()
    parser = DeltaParser()
    try:
        prog = parser.parse(source)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        sys.exit(1)
    interp = Interpreter(db_file)
    try:
        interp.run_program(prog)
    except Exception as e:
        print(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        interp.close()

if __name__ == '__main__':
    main()