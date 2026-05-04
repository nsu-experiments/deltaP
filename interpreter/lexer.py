#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lexical analyzer for DeltaP language.
"""

from ply import lex


# ----------------------------------------------------------------------
#                              TOKENS
# ----------------------------------------------------------------------

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

# Reserved words
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


def t_comment(t):
    r'//.*'
    pass  # Comments are ignored


def t_error(t):
    raise SyntaxError(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")


# Build the lexer
lexer = lex.lex()