"""
Syntax Analyzer (Parser) for SQL-like Language - Phase 02
Implements Recursive Descent Parsing with Parse Tree generation.
Supports DDL (CREATE, ALTER, DROP) and DML (INSERT, SELECT, UPDATE, DELETE) operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum
from lexer import Lexer, Token, LexerError


class ParseError(Exception):
    """Custom exception for parse errors"""
    pass


class NodeType(Enum):
    """Enumeration for Parse Tree node types"""
    # Top-level
    STATEMENT = "Statement"
    STATEMENT_LIST = "StatementList"
    
    # DDL
    CREATE_TABLE = "CreateTable"
    CREATE_DATABASE = "CreateDatabase"
    CREATE_VIEW = "CreateView"
    CREATE_INDEX = "CreateIndex"
    ALTER_TABLE = "AlterTable"
    DROP_TABLE = "DropTable"
    DROP_DATABASE = "DropDatabase"
    DROP_VIEW = "DropView"
    DROP_INDEX = "DropIndex"
    
    # DML
    SELECT = "Select"
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"
    
    # Clauses
    SELECT_LIST = "SelectList"
    FROM_CLAUSE = "FromClause"
    WHERE_CLAUSE = "WhereClause"
    GROUP_BY_CLAUSE = "GroupByClause"
    HAVING_CLAUSE = "HavingClause"
    ORDER_BY_CLAUSE = "OrderByClause"
    LIMIT_CLAUSE = "LimitClause"
    
    # Sub-components
    COLUMN = "Column"
    COLUMN_LIST = "ColumnList"
    TABLE_NAME = "TableName"
    QUALIFIED_NAME = "QualifiedName"
    CONDITION = "Condition"
    LOGICAL_AND = "LogicalAnd"
    LOGICAL_OR = "LogicalOr"
    LOGICAL_NOT = "LogicalNot"
    COMPARISON = "Comparison"
    BETWEEN = "Between"
    IN_CLAUSE = "InClause"
    LIKE_CLAUSE = "LikeClause"
    IS_NULL = "IsNull"
    
    # Functions and expressions
    FUNCTION_CALL = "FunctionCall"
    AGGREGATE_FUNCTION = "AggregateFunction"
    ARGUMENT_LIST = "ArgumentList"
    EXPRESSION = "Expression"
    TERM = "Term"
    FACTOR = "Factor"
    UNARY = "Unary"
    LITERAL = "Literal"
    
    # Values
    VALUE_LIST = "ValueList"
    
    # Column definitions
    COLUMN_DEF = "ColumnDefinition"
    DATA_TYPE = "DataType"
    CONSTRAINT = "Constraint"
    PRIMARY_KEY = "PrimaryKey"
    FOREIGN_KEY = "ForeignKey"
    UNIQUE_CONSTRAINT = "Unique"
    CHECK_CONSTRAINT = "Check"
    DEFAULT_CONSTRAINT = "Default"
    
    # Joins
    JOIN = "Join"
    JOIN_CONDITION = "JoinCondition"
    
    # Sorting
    SORT_ITEM = "SortItem"
    
    # Terminal
    TERMINAL = "Terminal"


class ParseTreeNode:
    """Represents a node in the Parse Tree"""
    
    def __init__(self, node_type: NodeType, value: Optional[str] = None, 
                 children: Optional[List['ParseTreeNode']] = None,
                 line: Optional[int] = None, column: Optional[int] = None):
        self.node_type = node_type
        self.value = value  # For terminal nodes (lexeme)
        self.children = children if children is not None else []
        self.line = line  # Source line number
        self.column = column  # Source column number
    
    def add_child(self, child: 'ParseTreeNode'):
        self.children.append(child)

    def __repr__(self):
        if self.value:
            return f"({self.node_type.value}: {self.value})"
        return f"({self.node_type.value})"

    def get_node_count(self) -> int:
        """Count total nodes in the subtree"""
        count = 1
        for child in self.children:
            count += child.get_node_count()
        return count

    def get_depth(self) -> int:
        """Calculate maximum tree depth"""
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)

    def get_terminal_count(self) -> int:
        """Count terminal nodes (leaf nodes or specific terminal types)"""
        if not self.children:
            return 1
        return sum(child.get_terminal_count() for child in self.children)

    def get_non_terminal_count(self) -> int:
        """Count non-terminal nodes (internal nodes)"""
        count = 1 if self.children else 0
        for child in self.children:
            count += child.get_non_terminal_count()
        return count

    def to_visual_string(self, level=0, prefix="", is_last_sibling=True) -> List[str]:
        """Generate interactive-style ASCII visualization of the tree"""
        # Get node label
        if self.value:
            label = f"{self.node_type.value}: '{self.value}'"
        else:
            label = self.node_type.value
        
        # Add semantic annotation if present
        if hasattr(self, "inferred_type") and self.inferred_type:
            label += f" <Type: {self.inferred_type}>"
        
        # Add location info
        location = ""
        if self.line or self.column:
            if self.line and self.column:
                location = f" (Line {self.line}, Col {self.column})"
            elif self.line:
                location = f" (Line {self.line})"
        
        # Build current node line
        if level == 0:
            tree_lines = [f"🌳 {label}{location}"]
        else:
            connector = "└── " if is_last_sibling else "├── "
            tree_lines = [f"{prefix}{connector}{label}{location}"]
        
        # Recursively add children
        for i, child in enumerate(self.children):
            is_last_child = (i == len(self.children) - 1)
            if level == 0:
                child_prefix = ""
            else:
                extension = "    " if is_last_sibling else "│   "
                child_prefix = prefix + extension
            
            child_lines = child.to_visual_string(level + 1, child_prefix, is_last_child)
            tree_lines.extend(child_lines)
        
        return tree_lines

    def to_string(self, indent: int = 0):
        """Generate a pretty-printed representation of the tree"""
        result = "  " * indent + str(self) + "\n"
        for child in self.children:
            result += child.to_string(indent + 1)
        return result


@dataclass
class SyntaxErrorInfo:
    """Information about a syntax error"""
    line: int
    column: int
    message: str
    expected: Optional[str] = None
    found: Optional[str] = None
    
    def __str__(self) -> str:
        if self.expected and self.found:
            return (f"Syntax Error at line {self.line}, column {self.column}: "
                    f"Expected '{self.expected}' but found '{self.found}'.")
        return f"Syntax Error at line {self.line}, column {self.column}: {self.message}"


class Parser:
    """
    Recursive Descent Parser for SQL-like Language
    """
    
    # Synchronization tokens for error recovery
    SYNC_TOKENS = {'SEMICOLON', 'KEYWORD', 'EOF'}
    
    # Major statement keywords for sync
    STATEMENT_KEYWORDS = {'CREATE', 'ALTER', 'DROP', 'SELECT', 'INSERT', 
                         'UPDATE', 'DELETE', 'WITH'}
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if tokens else None
        self.errors: List[SyntaxErrorInfo] = []
        self.parse_tree: Optional[ParseTreeNode] = None
    
    def advance(self) -> None:
        """Move to the next token"""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        """Look ahead at future tokens"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def expect(self, expected_type: str, expected_value: Optional[str] = None) -> Token:
        """Consume a token of expected type and value"""
        if self.current_token is None:
            self.error(f"Expected '{expected_value or expected_type}' but reached EOF.")
            raise ParseError("Unexpected EOF")
        
        if self.current_token.type != expected_type:
            self.error(
                f"Expected '{expected_value or expected_type}' but found '{self.current_token.value}'.",
                expected=expected_value or expected_type,
                found=self.current_token.value
            )
            raise ParseError(f"Expected {expected_type}")
        
        if expected_value is not None:
            current_val = self.current_token.value if self.current_token.value else ""
            if isinstance(current_val, str):
                current_val = current_val.upper()
            expected_val = expected_value.upper() if isinstance(expected_value, str) else expected_value
            
            if current_val != expected_val:
                self.error(
                    f"Expected '{expected_value}' but found '{self.current_token.value}'.",
                    expected=expected_value,
                    found=self.current_token.value
                )
                raise ParseError(f"Expected {expected_value}")
        
        token = self.current_token
        self.advance()
        return token
    
    def match(self, *values: str) -> bool:
        """Check if current token matches any of the given values"""
        if self.current_token is None:
            return False
        current_val = self.current_token.value if self.current_token.value else ""
        return isinstance(current_val, str) and current_val.upper() in [v.upper() for v in values]
    
    def match_type(self, *types: str) -> bool:
        """Check if current token type matches any of the given types"""
        if self.current_token is None:
            return False
        return self.current_token.type in types
    
    def error(self, message: str, expected: Optional[str] = None, 
              found: Optional[str] = None) -> None:
        """Record a syntax error"""
        error_info = SyntaxErrorInfo(
            line=self.current_token.line if self.current_token else 0,
            column=self.current_token.column if self.current_token else 0,
            message=message,
            expected=expected,
            found=found
        )
        self.errors.append(error_info)
    
    def recover(self) -> None:
        """Error recovery: skip tokens until a synchronization point is found"""
        while self.current_token is not None:
            # If we hit a semicolon or EOF, try to continue
            if self.match('SEMICOLON') or self.current_token.type == 'EOF':
                self.advance()
                return
            
            # If we hit a major statement keyword, stop here and let the caller handle it
            if self.current_token.type == 'KEYWORD' and \
               self.current_token.value.upper() in self.STATEMENT_KEYWORDS:
                return
            
            self.advance()
    
    def parse(self) -> ParseTreeNode:
        """Main entry point: parse a complete statement or multiple statements"""
        try:
            if self.current_token is None or self.current_token.type == 'EOF':
                # Empty input
                return ParseTreeNode(NodeType.STATEMENT_LIST, line=1, column=1)
            
            # Parse statement list
            statements = []
            while self.current_token is not None and self.current_token.type != 'EOF':
                try:
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                    
                    # Consume semicolon if present (DELIMITER with value ';')
                    if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ';':
                        self.advance()
                except ParseError:
                    self.recover()
                    continue
            
            # Create root node
            if len(statements) == 1:
                self.parse_tree = statements[0]
            else:
                root = ParseTreeNode(NodeType.STATEMENT_LIST, line=1, column=1)
                for stmt in statements:
                    root.add_child(stmt)
                self.parse_tree = root
            
            return self.parse_tree
        
        except Exception as e:
            self.error(f"Critical parsing error: {str(e)}")
            raise ParseError(str(e))
    
    def parse_statement(self) -> Optional[ParseTreeNode]:
        """Parse a single SQL statement"""
        if self.current_token is None or self.current_token.type == 'EOF':
            return None
        
        # Handle SEMICOLON at start
        if self.current_token.type == 'DELIMITER' and self.current_token.value == ';':
            self.advance()
            return None
        
        if not self.match_type('KEYWORD'):
            self.error(f"Expected keyword to start statement but found '{self.current_token.value if self.current_token else 'EOF'}'")
            raise ParseError("Expected statement keyword")
        
        keyword = self.current_token.value.upper() if self.current_token.value else ""
        
        if keyword == 'SELECT':
            return self.parse_select()
        elif keyword == 'INSERT':
            return self.parse_insert()
        elif keyword == 'UPDATE':
            return self.parse_update()
        elif keyword == 'DELETE':
            return self.parse_delete()
        elif keyword == 'CREATE':
            return self.parse_create()
        elif keyword == 'ALTER':
            return self.parse_alter()
        elif keyword == 'DROP':
            return self.parse_drop()
        else:
            self.error(f"Unexpected statement keyword: '{keyword}'")
            raise ParseError(f"Unknown statement: {keyword}")
    
    # ==================== DDL Parsing ====================
    
    def parse_create(self) -> ParseTreeNode:
        """Parse CREATE statement"""
        self.expect('KEYWORD', 'CREATE')
        
        if self.match('TABLE'):
            return self.parse_create_table()
        elif self.match('DATABASE'):
            return self.parse_create_database()
        elif self.match('VIEW'):
            return self.parse_create_view()
        elif self.match('INDEX'):
            return self.parse_create_index()
        else:
            self.error(f"Expected TABLE, DATABASE, VIEW, or INDEX after CREATE but found '{self.current_token.value}'")
            raise ParseError("Expected CREATE object type")
    
    def parse_create_table(self) -> ParseTreeNode:
        """Parse CREATE TABLE statement"""
        node = ParseTreeNode(NodeType.CREATE_TABLE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'TABLE')
        
        # Table name
        table_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_name_token.value,
                                     line=table_name_token.line, column=table_name_token.column))
        
        # Column definitions
        self.expect('DELIMITER', '(')
        
        # Parse column list
        node.add_child(self.parse_column_definitions())
        
        self.expect('DELIMITER', ')')
        
        return node
    
    def parse_column_definitions(self) -> ParseTreeNode:
        """Parse column definitions in CREATE TABLE"""
        node = ParseTreeNode(NodeType.COLUMN_LIST, line=self.current_token.line)
        
        while True:
            # Parse column definition
            col_def = self.parse_column_definition()
            node.add_child(col_def)
            
            if self.match_type('DELIMITER') and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        return node
    
    def parse_column_definition(self) -> ParseTreeNode:
        """Parse a single column definition"""
        node = ParseTreeNode(NodeType.COLUMN_DEF, line=self.current_token.line)
        
        # Column name
        col_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=col_name_token.value,
                                     line=col_name_token.line, column=col_name_token.column))
        
        # Data type
        node.add_child(self.parse_data_type())
        
        # Optional constraints
        while self.match_type('KEYWORD'):
            if self.match('PRIMARY', 'FOREIGN', 'UNIQUE', 'NOT', 'DEFAULT', 'CHECK'):
                node.add_child(self.parse_constraint())
            else:
                break
        
        return node
    
    def parse_data_type(self) -> ParseTreeNode:
        """Parse data type specification"""
        node = ParseTreeNode(NodeType.DATA_TYPE, line=self.current_token.line)
        
        if not self.match_type('KEYWORD', 'IDENTIFIER'):
            self.error(f"Expected data type but found '{self.current_token.value}'")
            raise ParseError("Expected data type")
        
        type_token = self.current_token
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=type_token.value,
                                     line=type_token.line, column=type_token.column))
        self.advance()
        
        # Handle size specifiers like INT(10)
        if self.match_type('DELIMITER') and self.current_token.value == '(':
            self.advance()
            size_token = self.expect('INTEGER')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value=size_token.value,
                                         line=size_token.line, column=size_token.column))
            self.expect('DELIMITER', ')')
        
        return node
    
    def parse_constraint(self) -> ParseTreeNode:
        """Parse table/column constraint"""
        if self.match('PRIMARY'):
            self.expect('KEYWORD', 'PRIMARY')
            self.expect('KEYWORD', 'KEY')
            return ParseTreeNode(NodeType.PRIMARY_KEY, line=self.tokens[self.pos-2].line)
        
        elif self.match('FOREIGN'):
            return self.parse_foreign_key()
        
        elif self.match('UNIQUE'):
            self.expect('KEYWORD', 'UNIQUE')
            return ParseTreeNode(NodeType.UNIQUE_CONSTRAINT, line=self.tokens[self.pos-1].line)
        
        elif self.match('NOT'):
            self.expect('KEYWORD', 'NOT')
            self.expect('KEYWORD', 'NULL')
            return ParseTreeNode(NodeType.CONSTRAINT, value='NOT NULL',
                               line=self.tokens[self.pos-2].line)
        
        elif self.match('DEFAULT'):
            self.expect('KEYWORD', 'DEFAULT')
            default_node = ParseTreeNode(NodeType.DEFAULT_CONSTRAINT, 
                                        line=self.current_token.line)
            # Parse default value (literal or expression)
            default_node.add_child(self.parse_primary_expression())
            return default_node
        
        elif self.match('CHECK'):
            self.expect('KEYWORD', 'CHECK')
            self.expect('DELIMITER', '(')
            check_node = ParseTreeNode(NodeType.CHECK_CONSTRAINT,
                                       line=self.tokens[self.pos-2].line)
            check_node.add_child(self.parse_condition())
            self.expect('DELIMITER', ')')
            return check_node
        
        else:
            self.error(f"Expected constraint keyword but found '{self.current_token.value}'")
            raise ParseError("Expected constraint")
    
    def parse_foreign_key(self) -> ParseTreeNode:
        """Parse FOREIGN KEY constraint"""
        node = ParseTreeNode(NodeType.FOREIGN_KEY, line=self.current_token.line)
        
        self.expect('KEYWORD', 'FOREIGN')
        self.expect('KEYWORD', 'KEY')
        
        # Referencing columns
        self.expect('DELIMITER', '(')
        node.add_child(self.parse_column_list())
        self.expect('DELIMITER', ')')
        
        self.expect('KEYWORD', 'REFERENCES')
        
        # Referenced table
        table_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_token.value,
                                     line=table_token.line, column=table_token.column))
        
        # Referenced columns
        self.expect('DELIMITER', '(')
        node.add_child(self.parse_column_list())
        self.expect('DELIMITER', ')')
        
        return node
    
    def parse_create_database(self) -> ParseTreeNode:
        """Parse CREATE DATABASE statement"""
        node = ParseTreeNode(NodeType.CREATE_DATABASE, line=self.current_token.line)
        self.expect('KEYWORD', 'DATABASE')
        
        db_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=db_name_token.value,
                                     line=db_name_token.line, column=db_name_token.column))
        
        return node
    
    def parse_create_view(self) -> ParseTreeNode:
        """Parse CREATE VIEW statement"""
        node = ParseTreeNode(NodeType.CREATE_VIEW, line=self.current_token.line)
        self.expect('KEYWORD', 'VIEW')
        
        view_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=view_name_token.value,
                                     line=view_name_token.line, column=view_name_token.column))
        
        self.expect('KEYWORD', 'AS')
        node.add_child(self.parse_select())
        
        return node
    
    def parse_create_index(self) -> ParseTreeNode:
        """Parse CREATE INDEX statement"""
        node = ParseTreeNode(NodeType.CREATE_INDEX, line=self.current_token.line)
        self.expect('KEYWORD', 'INDEX')
        
        index_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=index_name_token.value,
                                     line=index_name_token.line, column=index_name_token.column))
        
        self.expect('KEYWORD', 'ON')
        
        table_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_name_token.value,
                                     line=table_name_token.line, column=table_name_token.column))
        
        self.expect('DELIMITER', '(')
        node.add_child(self.parse_column_list())
        self.expect('DELIMITER', ')')
        
        return node
    
    def parse_alter(self) -> ParseTreeNode:
        """Parse ALTER statement"""
        node = ParseTreeNode(NodeType.ALTER_TABLE, line=self.current_token.line)
        self.expect('KEYWORD', 'ALTER')
        
        if self.match('TABLE'):
            self.expect('KEYWORD', 'TABLE')
            table_name_token = self.expect('IDENTIFIER')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_name_token.value,
                                         line=table_name_token.line, column=table_name_token.column))
            
            # Parse ALTER action
            if self.match('ADD'):
                self.expect('KEYWORD', 'ADD')
                node.add_child(self.parse_column_definition())
            elif self.match('DROP'):
                self.expect('KEYWORD', 'DROP')
                self.expect('KEYWORD', 'COLUMN')
                col_token = self.expect('IDENTIFIER')
                node.add_child(ParseTreeNode(NodeType.TERMINAL, value=col_token.value,
                                             line=col_token.line, column=col_token.column))
            else:
                self.error(f"Expected ADD or DROP after ALTER TABLE")
        else:
            self.error(f"Expected TABLE after ALTER but found '{self.current_token.value}'")
        
        return node
    
    def parse_drop(self) -> ParseTreeNode:
        """Parse DROP statement"""
        self.expect('KEYWORD', 'DROP')
        
        if self.match('TABLE'):
            node = ParseTreeNode(NodeType.DROP_TABLE, line=self.tokens[self.pos-1].line)
            self.expect('KEYWORD', 'TABLE')
        elif self.match('DATABASE'):
            node = ParseTreeNode(NodeType.DROP_DATABASE, line=self.tokens[self.pos-1].line)
            self.expect('KEYWORD', 'DATABASE')
        elif self.match('VIEW'):
            node = ParseTreeNode(NodeType.DROP_VIEW, line=self.tokens[self.pos-1].line)
            self.expect('KEYWORD', 'VIEW')
        elif self.match('INDEX'):
            node = ParseTreeNode(NodeType.DROP_INDEX, line=self.tokens[self.pos-1].line)
            self.expect('KEYWORD', 'INDEX')
        else:
            self.error(f"Expected TABLE, DATABASE, VIEW, or INDEX after DROP")
            raise ParseError("Expected DROP object type")
        
        object_name_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=object_name_token.value,
                                     line=object_name_token.line, column=object_name_token.column))
        
        return node
    
    # ==================== DML Parsing ====================
    
    def parse_select(self) -> ParseTreeNode:
        """Parse SELECT statement"""
        node = ParseTreeNode(NodeType.SELECT, line=self.current_token.line)
        
        self.expect('KEYWORD', 'SELECT')
        
        # Handle DISTINCT
        if self.match('DISTINCT'):
            self.expect('KEYWORD', 'DISTINCT')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value='DISTINCT',
                                         line=self.tokens[self.pos-1].line))
        
        # Parse select list
        node.add_child(self.parse_select_list())
        
        # FROM clause
        if self.match('FROM'):
            node.add_child(self.parse_from_clause())
        
        # WHERE clause
        if self.match('WHERE'):
            node.add_child(self.parse_where_clause())
        
        # GROUP BY clause
        if self.match('GROUP'):
            node.add_child(self.parse_group_by_clause())
        
        # HAVING clause
        if self.match('HAVING'):
            node.add_child(self.parse_having_clause())
        
        # ORDER BY clause
        if self.match('ORDER'):
            node.add_child(self.parse_order_by_clause())
        
        # LIMIT clause
        if self.match('LIMIT'):
            node.add_child(self.parse_limit_clause())
        
        return node
    
    def parse_select_list(self) -> ParseTreeNode:
        """Parse SELECT list (columns to select)"""
        node = ParseTreeNode(NodeType.SELECT_LIST, line=self.current_token.line if self.current_token else 0)
        
        # Handle SELECT *
        if self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == '*':
            self.advance()
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value='*',
                                         line=self.tokens[self.pos-1].line))
        else:
            # Parse column expressions
            while True:
                # Parse expression
                expr_node = self.parse_expression()
                
                # Handle alias (AS or implicit)
                if self.match('AS'):
                    self.advance()
                    alias_token = self.expect('IDENTIFIER')
                    select_item = ParseTreeNode(NodeType.COLUMN, line=expr_node.line)
                    select_item.add_child(expr_node)
                    select_item.add_child(ParseTreeNode(NodeType.TERMINAL, value=alias_token.value,
                                                        line=alias_token.line, column=alias_token.column))
                    node.add_child(select_item)
                elif (self.current_token is not None and 
                      self.current_token.type == 'IDENTIFIER' and 
                      not self.match('FROM', 'WHERE', 'GROUP', 'HAVING', 'ORDER', 'LIMIT') and
                      not (self.current_token.type == 'DELIMITER' and self.current_token.value in [';', ',', ')'])):
                    # Implicit alias
                    alias_token = self.expect('IDENTIFIER')
                    select_item = ParseTreeNode(NodeType.COLUMN, line=expr_node.line)
                    select_item.add_child(expr_node)
                    select_item.add_child(ParseTreeNode(NodeType.TERMINAL, value=alias_token.value,
                                                        line=alias_token.line, column=alias_token.column))
                    node.add_child(select_item)
                else:
                    node.add_child(expr_node)
                
                if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ',':
                    self.advance()
                else:
                    break
        
        return node
    
    def parse_from_clause(self) -> ParseTreeNode:
        """Parse FROM clause"""
        node = ParseTreeNode(NodeType.FROM_CLAUSE, line=self.current_token.line if self.current_token else 0)
        
        self.expect('KEYWORD', 'FROM')
        
        # Parse table references (with possible joins)
        while True:
            table_ref = self.parse_table_reference()
            node.add_child(table_ref)
            
            # Check for joins
            if self.current_token and self.match('JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'):
                node.add_child(self.parse_join())
            else:
                break
        
        return node
    
    def parse_table_reference(self) -> ParseTreeNode:
        """Parse a table reference (table name with optional alias)"""
        table_name_token = self.expect('IDENTIFIER')
        node = ParseTreeNode(NodeType.TABLE_NAME, value=table_name_token.value,
                            line=table_name_token.line, column=table_name_token.column)
        
        # Handle alias
        if self.match('AS'):
            self.advance()
            alias_token = self.expect('IDENTIFIER')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value=alias_token.value,
                                         line=alias_token.line, column=alias_token.column))
        elif (self.current_token is not None and 
              self.current_token.type == 'IDENTIFIER' and 
              not self.match('JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 
                           'WHERE', 'GROUP', 'HAVING', 'ORDER', 'LIMIT') and
              not (self.current_token.type == 'DELIMITER' and self.current_token.value in [';', ',', ')'])):
            alias_token = self.expect('IDENTIFIER')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value=alias_token.value,
                                         line=alias_token.line, column=alias_token.column))
        
        return node
    
    def parse_join(self) -> ParseTreeNode:
        """Parse JOIN clause"""
        node = ParseTreeNode(NodeType.JOIN, line=self.current_token.line if self.current_token else 0)
        
        # Parse join type
        join_type = "INNER"
        if self.match('LEFT'):
            self.expect('KEYWORD', 'LEFT')
            join_type = "LEFT"
            if self.current_token and self.match('OUTER'):
                self.expect('KEYWORD', 'OUTER')
        elif self.match('RIGHT'):
            self.expect('KEYWORD', 'RIGHT')
            join_type = "RIGHT"
            if self.current_token and self.match('OUTER'):
                self.expect('KEYWORD', 'OUTER')
        elif self.match('FULL'):
            self.expect('KEYWORD', 'FULL')
            join_type = "FULL"
            if self.current_token and self.match('OUTER'):
                self.expect('KEYWORD', 'OUTER')
        elif self.match('CROSS'):
            self.expect('KEYWORD', 'CROSS')
            join_type = "CROSS"
        elif self.match('INNER'):
            self.expect('KEYWORD', 'INNER')
            join_type = "INNER"
        
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=join_type,
                                     line=self.tokens[self.pos-1].line))
        
        self.expect('KEYWORD', 'JOIN')
        
        # Parse right table reference
        node.add_child(self.parse_table_reference())
        
        # ON condition
        if self.current_token and self.match('ON'):
            self.expect('KEYWORD', 'ON')
            node.add_child(self.parse_condition())
        
        return node
    
    def parse_where_clause(self) -> ParseTreeNode:
        """Parse WHERE clause"""
        node = ParseTreeNode(NodeType.WHERE_CLAUSE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'WHERE')
        node.add_child(self.parse_condition())
        
        return node
    
    def parse_group_by_clause(self) -> ParseTreeNode:
        """Parse GROUP BY clause"""
        node = ParseTreeNode(NodeType.GROUP_BY_CLAUSE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'GROUP')
        self.expect('KEYWORD', 'BY')
        
        # Parse column list
        node.add_child(self.parse_column_list())
        
        return node
    
    def parse_having_clause(self) -> ParseTreeNode:
        """Parse HAVING clause"""
        node = ParseTreeNode(NodeType.HAVING_CLAUSE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'HAVING')
        node.add_child(self.parse_condition())
        
        return node
    
    def parse_order_by_clause(self) -> ParseTreeNode:
        """Parse ORDER BY clause"""
        node = ParseTreeNode(NodeType.ORDER_BY_CLAUSE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'ORDER')
        self.expect('KEYWORD', 'BY')
        
        # Parse sort items
        while True:
            sort_item = self.parse_sort_item()
            node.add_child(sort_item)
            
            if self.match_type('DELIMITER') and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        return node
    
    def parse_sort_item(self) -> ParseTreeNode:
        """Parse a single sort item"""
        expr_node = self.parse_expression()
        
        sort_node = ParseTreeNode(NodeType.SORT_ITEM, line=expr_node.line)
        sort_node.add_child(expr_node)
        
        # Handle ASC/DESC
        if self.match('ASC'):
            self.advance()
            sort_node.add_child(ParseTreeNode(NodeType.TERMINAL, value='ASC',
                                              line=self.tokens[self.pos-1].line))
        elif self.match('DESC'):
            self.advance()
            sort_node.add_child(ParseTreeNode(NodeType.TERMINAL, value='DESC',
                                              line=self.tokens[self.pos-1].line))
        
        return sort_node
    
    def parse_limit_clause(self) -> ParseTreeNode:
        """Parse LIMIT clause"""
        node = ParseTreeNode(NodeType.LIMIT_CLAUSE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'LIMIT')
        
        # Parse limit count
        limit_token = self.expect('INTEGER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=limit_token.value,
                                     line=limit_token.line, column=limit_token.column))
        
        return node
    
    def parse_insert(self) -> ParseTreeNode:
        """Parse INSERT statement"""
        node = ParseTreeNode(NodeType.INSERT, line=self.current_token.line)
        
        self.expect('KEYWORD', 'INSERT')
        self.expect('KEYWORD', 'INTO')
        
        # Table name
        table_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_token.value,
                                     line=table_token.line, column=table_token.column))
        
        # Optional column list
        if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == '(':
            self.advance()
            col_list = ParseTreeNode(NodeType.COLUMN_LIST, line=self.current_token.line if self.current_token else 0)
            
            while True:
                col_token = self.expect('IDENTIFIER')
                col_list.add_child(ParseTreeNode(NodeType.COLUMN, value=col_token.value,
                                                line=col_token.line, column=col_token.column))
                
                if self.current_token and self.current_token.type == 'DELIMITER':
                    if self.current_token.value == ',':
                        self.advance()
                    elif self.current_token.value == ')':
                        break
                else:
                    break
            
            node.add_child(col_list)
            self.expect('DELIMITER', ')')
        
        self.expect('KEYWORD', 'VALUES')
        
        # Value list
        node.add_child(self.parse_value_list())
        
        return node
    
    def parse_update(self) -> ParseTreeNode:
        """Parse UPDATE statement"""
        node = ParseTreeNode(NodeType.UPDATE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'UPDATE')
        
        # Table name
        table_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_token.value,
                                     line=table_token.line, column=table_token.column))
        
        self.expect('KEYWORD', 'SET')
        
        # Parse assignment list
        while True:
            col_token = self.expect('IDENTIFIER')
            col_node = ParseTreeNode(NodeType.COLUMN, value=col_token.value,
                                    line=col_token.line, column=col_token.column)
            
            self.expect('OPERATOR', '=')
            col_node.add_child(self.parse_expression())
            node.add_child(col_node)
            
            if self.match_type('DELIMITER') and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        # Optional WHERE clause
        if self.match('WHERE'):
            node.add_child(self.parse_where_clause())
        
        return node
    
    def parse_delete(self) -> ParseTreeNode:
        """Parse DELETE statement"""
        node = ParseTreeNode(NodeType.DELETE, line=self.current_token.line)
        
        self.expect('KEYWORD', 'DELETE')
        self.expect('KEYWORD', 'FROM')
        
        # Table name
        table_token = self.expect('IDENTIFIER')
        node.add_child(ParseTreeNode(NodeType.TERMINAL, value=table_token.value,
                                     line=table_token.line, column=table_token.column))
        
        # Optional WHERE clause
        if self.match('WHERE'):
            node.add_child(self.parse_where_clause())
        
        return node
    
    # ==================== Expression & Condition Parsing ====================
    
    def parse_condition(self) -> ParseTreeNode:
        """Parse a condition (handles OR at the top level)"""
        return self.parse_or_condition()
    
    def parse_or_condition(self) -> ParseTreeNode:
        """Parse OR condition (lowest precedence)"""
        left = self.parse_and_condition()
        
        while self.match('OR'):
            self.expect('KEYWORD', 'OR')
            or_node = ParseTreeNode(NodeType.LOGICAL_OR, line=self.tokens[self.pos-1].line)
            or_node.add_child(left)
            or_node.add_child(self.parse_and_condition())
            left = or_node
        
        return left
    
    def parse_and_condition(self) -> ParseTreeNode:
        """Parse AND condition (medium precedence)"""
        left = self.parse_not_condition()
        
        while self.match('AND'):
            self.expect('KEYWORD', 'AND')
            and_node = ParseTreeNode(NodeType.LOGICAL_AND, line=self.tokens[self.pos-1].line)
            and_node.add_child(left)
            and_node.add_child(self.parse_not_condition())
            left = and_node
        
        return left
    
    def parse_not_condition(self) -> ParseTreeNode:
        """Parse NOT condition and primary conditions"""
        if self.match('NOT'):
            not_token = self.current_token
            self.expect('KEYWORD', 'NOT')
            not_node = ParseTreeNode(NodeType.LOGICAL_NOT, line=not_token.line)
            not_node.add_child(self.parse_not_condition())
            return not_node
        
        return self.parse_primary_condition()
    
    def parse_primary_condition(self) -> ParseTreeNode:
        """Parse primary condition (comparison, BETWEEN, IN, LIKE, IS NULL, or bare expression for boolean columns)"""
        # Handle parenthesized condition
        if self.match_type('DELIMITER') and self.current_token.value == '(':
            self.advance()
            cond = self.parse_condition()
            self.expect('DELIMITER', ')')
            return cond
        
        # Parse left expression
        left_expr = self.parse_expression()
        
        # Check for special operators
        if self.match('BETWEEN'):
            return self.parse_between_operator(left_expr)
        elif self.match('IN'):
            return self.parse_in_operator(left_expr)
        elif self.match('LIKE'):
            return self.parse_like_operator(left_expr)
        elif self.match('IS'):
            return self.parse_is_null_operator(left_expr)
        elif self.match_type('COMPARISON', 'OPERATOR'):
            return self.parse_comparison(left_expr)
        else:
            # Allow bare expressions (e.g., boolean columns like "Active" or "NOT Active")
            return left_expr
    
    def parse_comparison(self, left_expr: ParseTreeNode) -> ParseTreeNode:
        """Parse comparison operation"""
        comp_node = ParseTreeNode(NodeType.COMPARISON, line=left_expr.line)
        comp_node.add_child(left_expr)
        
        # Operator
        op_token = self.current_token
        if self.match_type('COMPARISON'):
            self.advance()
        elif self.match_type('OPERATOR') and self.current_token.value == '=':
            self.advance()
        else:
            self.error(f"Expected comparison operator")
            raise ParseError("Expected comparison operator")
        
        comp_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=op_token.value,
                                          line=op_token.line, column=op_token.column))
        
        # Right expression
        comp_node.add_child(self.parse_expression())
        
        return comp_node
    
    def parse_between_operator(self, expr: ParseTreeNode) -> ParseTreeNode:
        """Parse BETWEEN expression"""
        node = ParseTreeNode(NodeType.BETWEEN, line=self.current_token.line)
        node.add_child(expr)
        
        self.expect('KEYWORD', 'BETWEEN')
        node.add_child(self.parse_expression())
        
        self.expect('KEYWORD', 'AND')
        node.add_child(self.parse_expression())
        
        return node
    
    def parse_in_operator(self, expr: ParseTreeNode) -> ParseTreeNode:
        """Parse IN operator"""
        node = ParseTreeNode(NodeType.IN_CLAUSE, line=self.current_token.line)
        node.add_child(expr)
        
        self.expect('KEYWORD', 'IN')
        
        self.expect('DELIMITER', '(')
        
        # Parse value list
        values = []
        while True:
            values.append(self.parse_expression())
            
            if self.match_type('DELIMITER') and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        for val in values:
            node.add_child(val)
        
        self.expect('DELIMITER', ')')
        
        return node
    
    def parse_like_operator(self, expr: ParseTreeNode) -> ParseTreeNode:
        """Parse LIKE operator"""
        node = ParseTreeNode(NodeType.LIKE_CLAUSE, line=self.current_token.line)
        node.add_child(expr)
        
        self.expect('KEYWORD', 'LIKE')
        node.add_child(self.parse_expression())
        
        return node
    
    def parse_is_null_operator(self, expr: ParseTreeNode) -> ParseTreeNode:
        """Parse IS NULL / IS NOT NULL"""
        node = ParseTreeNode(NodeType.IS_NULL, line=self.current_token.line)
        node.add_child(expr)
        
        self.expect('KEYWORD', 'IS')
        
        if self.match('NOT'):
            self.expect('KEYWORD', 'NOT')
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value='NOT NULL',
                                         line=self.tokens[self.pos-1].line))
        else:
            node.add_child(ParseTreeNode(NodeType.TERMINAL, value='NULL',
                                         line=self.current_token.line))
        
        self.expect('KEYWORD', 'NULL')
        
        return node
    
    def parse_expression(self) -> ParseTreeNode:
        """Parse expression (handles arithmetic operators with precedence)"""
        return self.parse_additive()
    
    def parse_additive(self) -> ParseTreeNode:
        """Parse addition/subtraction"""
        left = self.parse_multiplicative()
        
        while self.match_type('OPERATOR') and self.current_token.value in ['+', '-']:
            op_token = self.current_token
            self.advance()
            expr_node = ParseTreeNode(NodeType.EXPRESSION, line=op_token.line)
            expr_node.add_child(left)
            expr_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=op_token.value,
                                              line=op_token.line, column=op_token.column))
            expr_node.add_child(self.parse_multiplicative())
            left = expr_node
        
        return left
    
    def parse_multiplicative(self) -> ParseTreeNode:
        """Parse multiplication/division"""
        left = self.parse_unary()
        
        while self.match_type('OPERATOR') and self.current_token.value in ['*', '/', '%']:
            op_token = self.current_token
            self.advance()
            expr_node = ParseTreeNode(NodeType.EXPRESSION, line=op_token.line)
            expr_node.add_child(left)
            expr_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=op_token.value,
                                              line=op_token.line, column=op_token.column))
            expr_node.add_child(self.parse_unary())
            left = expr_node
        
        return left
    
    def parse_unary(self) -> ParseTreeNode:
        """Parse unary expressions"""
        if self.match_type('OPERATOR') and self.current_token.value in ['+', '-']:
            op_token = self.current_token
            self.advance()
            unary_node = ParseTreeNode(NodeType.UNARY, line=op_token.line)
            unary_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=op_token.value,
                                               line=op_token.line, column=op_token.column))
            unary_node.add_child(self.parse_unary())
            return unary_node
        
        return self.parse_primary_expression()
    
    def parse_primary_expression(self) -> ParseTreeNode:
        """Parse primary expression (literals, identifiers, functions, parenthesized expressions)"""
        # Parenthesized expression
        if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == '(':
            # Peek ahead to see if this might be a subquery
            next_tok = self.peek()
            if next_tok and next_tok.type == 'KEYWORD' and next_tok.value.upper() == 'SELECT':
                self.advance()
                expr = self.parse_select()
                self.expect('DELIMITER', ')')
                return expr
            else:
                # Regular parenthesized expression
                self.advance()
                expr = self.parse_expression()
                self.expect('DELIMITER', ')')
                return expr
        
        # Function call or aggregate function
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value.upper() in \
           ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CAST', 'COALESCE', 'SUBSTR', 'LENGTH', 
            'UPPER', 'LOWER', 'ROUND', 'FLOOR', 'CEIL']:
            return self.parse_function_call()
        
        # Identifier (possibly qualified)
        if self.current_token and self.current_token.type == 'IDENTIFIER':
            return self.parse_column_or_function()
        
        # Literals
        if self.current_token and self.current_token.type in ['INTEGER', 'FLOAT', 'STRING']:
            token = self.current_token
            self.advance()
            return ParseTreeNode(NodeType.LITERAL, value=token.value,
                                line=token.line, column=token.column)
        
        # NULL literal
        if self.current_token and self.match('NULL'):
            token = self.current_token
            self.advance()
            return ParseTreeNode(NodeType.LITERAL, value='NULL',
                                line=token.line, column=token.column)
        
        self.error(f"Expected expression but found '{self.current_token.value if self.current_token else 'EOF'}'")
        raise ParseError("Expected expression")
    
    def parse_column_or_function(self) -> ParseTreeNode:
        """Parse column reference or function call"""
        col_token = self.expect('IDENTIFIER')
        
        # Check if it's a qualified name (table.column)
        if self.current_token and self.current_token.type == 'DOT':
            self.advance()
            qual_node = ParseTreeNode(NodeType.QUALIFIED_NAME, line=col_token.line)
            qual_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=col_token.value,
                                              line=col_token.line, column=col_token.column))
            
            # Handle * in SELECT (table.*)
            if self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == '*':
                self.advance()
                qual_node.add_child(ParseTreeNode(NodeType.TERMINAL, value='*',
                                                  line=self.tokens[self.pos-1].line))
                return qual_node
            
            col_part_token = self.expect('IDENTIFIER')
            qual_node.add_child(ParseTreeNode(NodeType.TERMINAL, value=col_part_token.value,
                                              line=col_part_token.line, column=col_part_token.column))
            return qual_node
        
        # Check if it's a function call
        if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == '(':
            self.advance()
            func_node = ParseTreeNode(NodeType.FUNCTION_CALL, value=col_token.value,
                                      line=col_token.line, column=col_token.column)
            
            # Parse arguments
            if not (self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ')'):
                while True:
                    func_node.add_child(self.parse_expression())
                    
                    if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ',':
                        self.advance()
                    else:
                        break
            
            self.expect('DELIMITER', ')')
            return func_node
        
        # Simple column reference
        return ParseTreeNode(NodeType.COLUMN, value=col_token.value,
                            line=col_token.line, column=col_token.column)
    
    def parse_function_call(self) -> ParseTreeNode:
        """Parse built-in function call"""
        func_token = self.current_token
        self.advance()
        
        func_node = ParseTreeNode(NodeType.AGGREGATE_FUNCTION, value=func_token.value,
                                  line=func_token.line, column=func_token.column)
        
        self.expect('DELIMITER', '(')
        
        # Handle COUNT(*) and COUNT(DISTINCT col)
        if func_token.value.upper() == 'COUNT':
            if self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == '*':
                self.advance()
                func_node.add_child(ParseTreeNode(NodeType.TERMINAL, value='*',
                                                  line=self.tokens[self.pos-1].line))
            else:
                if self.current_token and self.match('DISTINCT'):
                    self.advance()
                    func_node.add_child(ParseTreeNode(NodeType.TERMINAL, value='DISTINCT',
                                                      line=self.tokens[self.pos-1].line))
                func_node.add_child(self.parse_expression())
        else:
            # Regular function arguments
            if not (self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ')'):
                while True:
                    func_node.add_child(self.parse_expression())
                    
                    if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ',':
                        self.advance()
                    else:
                        break
        
        self.expect('DELIMITER', ')')
        return func_node
    
    def parse_column_list(self) -> ParseTreeNode:
        """Parse comma-separated column list"""
        node = ParseTreeNode(NodeType.COLUMN_LIST, line=self.current_token.line)
        
        while True:
            col_token = self.expect('IDENTIFIER')
            node.add_child(ParseTreeNode(NodeType.COLUMN, value=col_token.value,
                                         line=col_token.line, column=col_token.column))
            
            if self.match_type('DELIMITER') and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        return node
    
    def parse_value_list(self) -> ParseTreeNode:
        """Parse value list for INSERT"""
        node = ParseTreeNode(NodeType.VALUE_LIST, line=self.current_token.line if self.current_token else 0)
        
        while True:
            self.expect('DELIMITER', '(')
            
            while True:
                node.add_child(self.parse_expression())
                
                if self.current_token and self.current_token.type == 'DELIMITER':
                    if self.current_token.value == ',':
                        self.advance()
                    elif self.current_token.value == ')':
                        break
                else:
                    break
            
            self.expect('DELIMITER', ')')
            
            if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == ',':
                self.advance()
            else:
                break
        
        return node


def parse_sql(text: str) -> Tuple[Optional[ParseTreeNode], List[SyntaxErrorInfo], List[SyntaxErrorInfo]]:
    """
    Main entry point for parsing SQL code.
    
    Args:
        text: SQL source code to parse
    
    Returns:
        Tuple of (parse_tree, lexer_errors, parser_errors)
    """
    lexer = Lexer(text)
    tokens = []
    lexer_errors = []
    
    # Tokenize
    while True:
        try:
            token = lexer.get_next_token()
            if token.type == 'EOF':
                tokens.append(token)
                break
            tokens.append(token)
        except LexerError as e:
            lexer_errors.append(e)
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break
    
    # Parse
    parser = Parser(tokens)
    parse_tree = None
    
    try:
        parse_tree = parser.parse()
    except ParseError as e:
        pass  # Errors are recorded in parser.errors
    
    return parse_tree, lexer_errors, parser.errors
