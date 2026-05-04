#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom exception hierarchy for DeltaP interpreter.
"""

class DeltaPError(Exception):
    """Base exception for DeltaP interpreter"""
    def __init__(self, message: str, lineno: int = 0):
        self.lineno = lineno
        super().__init__(f"{message} at line {lineno}" if lineno else message)


class DeltaPTypeError(DeltaPError):
    """Type-related errors"""
    pass


class DeltaPNameError(DeltaPError):
    """Name/variable errors"""
    pass


class DeltaPArityError(DeltaPError):
    """Arity mismatch errors"""
    pass


class DeltaPDomainError(DeltaPError):
    """Domain-related errors"""
    pass