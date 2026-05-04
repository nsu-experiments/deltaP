#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser for DeltaP language using PLY yacc.
"""

from ply import yacc
from .lexer import tokens, lexer
from .ast_nodes import *


# ----------------------------------------------------------------------
#                              PARSER
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
            p[0].lineno = p.lineno(2)
        # Parentheses
        elif p[1] == '(':
            p[0] = p[2]
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