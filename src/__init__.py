"""
MiniSQL Compiler - Phase 01 & 02
Lexical Analyzer (Phase 01) and Syntax Analyzer (Phase 02) for SQL-like language
"""

__version__ = "2.0.0"
__author__ = "Omar"

from .lexer import Lexer, LexerError, Token
from .parser import Parser, parse_sql, ParseTreeNode, NodeType, SyntaxErrorInfo, ParseError

__all__ = [
    # Lexer exports
    'Lexer',
    'Token',
    'LexerError',
    
    # Parser exports
    'Parser',
    'parse_sql',
    'ParseTreeNode',
    'NodeType',
    'SyntaxErrorInfo',
    'ParseError',
]

__all__ = ['Lexer', 'LexerError', 'Token']
