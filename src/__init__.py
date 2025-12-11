"""
MiniSQL Compiler - Phase 1 (Lexer)
A SQL lexical analyzer that tokenizes SQL statements
"""

__version__ = "1.0.0"
__author__ = "Omar"

from .lexer import Lexer, LexerError, Token

__all__ = ['Lexer', 'LexerError', 'Token']
