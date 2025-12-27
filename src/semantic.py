from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from parser import ParseTreeNode, NodeType
from constants import VALID_DATA_TYPES

# Import Parser classes to avoid circular imports if possible, or use typing.TYPE_CHECKING
# But since we use ParseTreeNode and NodeType, we need to import them.
# Note: Ensure ParseTreeNode and NodeType are available. Assuming they are in parser.py

class SemanticError(Exception):
    """Custom exception for semantic errors"""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Semantic Error at line {line}, column {column}: {message}")

@dataclass
class ColumnInfo:
    """Metadata for a column in the symbol table"""
    name: str
    data_type: str
    constraints: List[str]

@dataclass
class TableInfo:
    """Metadata for a table in the symbol table"""
    name: str
    columns: Dict[str, ColumnInfo]

class SymbolTable:
    """
    Manages metadata about tables and columns.
    """
    def __init__(self):
        self.tables: Dict[str, TableInfo] = {}

    def create_table(self, table_name: str, columns: List[ColumnInfo]) -> None:
        """Register a new table definition"""
        if table_name.upper() in self.tables:
            raise ValueError(f"Table '{table_name}' already exists")
        
        self.tables[table_name.upper()] = TableInfo(
            name=table_name,
            columns={col.name.upper(): col for col in columns}
        )

    def get_table(self, table_name: str) -> Optional[TableInfo]:
        """Look up a table by name"""
        return self.tables.get(table_name.upper())

    def get_column(self, table_name: str, column_name: str) -> Optional[ColumnInfo]:
        """Look up a column definition"""
        table = self.get_table(table_name)
        if not table:
            return None
        return table.columns.get(column_name.upper())

    def drop_table(self, table_name: str) -> bool:
        """Remove a table"""
        if table_name.upper() in self.tables:
            del self.tables[table_name.upper()]
            return True
        return False
    
    def __str__(self) -> str:
        """Dump symbol table for display"""
        result = "Symbol Table:\n"
        result += "=" * 50 + "\n"
        if not self.tables:
            result += "  (Empty)\n"
        
        for table_name, info in self.tables.items():
            result += f"Table: {table_name}\n"
            for col_name, col_info in info.columns.items():
                constraints = ", ".join(col_info.constraints) if col_info.constraints else "None"
                result += f"  - {col_name}: {col_info.data_type} (Constraints: {constraints})\n"
            result += "-" * 50 + "\n"
        return result


class SemanticAnalyzer:
    """
    Traverses the Parse Tree to verify semantic correctness.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[str] = []
        self.current_query_scope: Dict[str, str] = {} # Alias mappings for current query

    def analyze(self, parse_tree: ParseTreeNode) -> Tuple[bool, List[str], SymbolTable]:
        """
        Main entry point for analysis.
        Returns: (success, errors, symbol_table)
        """
        self.errors = []
        try:
            self.visit(parse_tree)
        except SemanticError as e:
            self.errors.append(str(e))
        except Exception as e:
            self.errors.append(f"Unexpected error during analysis: {str(e)}")
        
        return len(self.errors) == 0, self.errors, self.symbol_table

    def visit(self, node: ParseTreeNode) -> Any:
        """Dispatch visit to specific methods based on node type"""
        if node is None:
            return
        
        method_name = f"visit_{node.node_type.name.lower()}"
        visitor = getattr(self, method_name, self.visit_children)
        return visitor(node)

    def visit_children(self, node: ParseTreeNode) -> None:
        """Default fallback: visit all children"""
        for child in node.children:
            self.visit(child)

    # ==================== DDL Visitors ====================

    def visit_create_table(self, node: ParseTreeNode) -> None:
        """Handle CREATE TABLE"""
        # Child 0: Table Name
        # Child 1: Column List
        table_name_node = node.children[0]
        table_name = table_name_node.value
        
        # Check if table already exists
        if self.symbol_table.get_table(table_name):
            self.error(f"Table '{table_name}' already exists", node.line, node.column)
            return

        columns = []
        column_list_node = node.children[1]
        
        for col_def in column_list_node.children:
            # col_def structure: Name, DataType, Constraints...
            col_name = col_def.children[0].value
            type_node = col_def.children[1]
            data_type = type_node.children[0].value # Base type
            
            # Basic type validation
            if data_type.upper() not in VALID_DATA_TYPES:
                 self.error(f"Invalid data type '{data_type}'", type_node.line, type_node.column)
            
            constraints = []
            for i in range(2, len(col_def.children)):
                constraint_node = col_def.children[i]
                if constraint_node.node_type == NodeType.PRIMARY_KEY:
                    constraints.append("PRIMARY KEY")
                elif constraint_node.node_type == NodeType.FOREIGN_KEY:
                    constraints.append("FOREIGN KEY")
                elif constraint_node.value:
                    constraints.append(constraint_node.value)
                else:
                    constraints.append(constraint_node.node_type.name)

            columns.append(ColumnInfo(col_name, data_type, constraints))

        # Register table
        try:
            self.symbol_table.create_table(table_name, columns)
        except ValueError as e:
             self.error(str(e), node.line, node.column)

    def visit_drop_table(self, node: ParseTreeNode) -> None:
        table_name = node.children[0].value
        if not self.symbol_table.get_table(table_name):
             self.error(f"Cannot drop table '{table_name}': Table does not exist", node.line, node.column)
        else:
            self.symbol_table.drop_table(table_name)

    # ==================== DML Visitors ====================

    def visit_insert(self, node: ParseTreeNode) -> None:
        """Handle INSERT INTO"""
        # Child 0: Table Name
        table_name = node.children[0].value
        table_info = self.symbol_table.get_table(table_name)
        
        if not table_info:
            self.error(f"Table '{table_name}' does not exist", node.line, node.column)
            return

        # Handle optional column list vs all columns
        child_idx = 1
        target_columns = list(table_info.columns.values())
        
        if node.children[1].node_type == NodeType.COLUMN_LIST:
            # Specific columns provided
            target_columns = []
            col_list_node = node.children[1]
            for col_node in col_list_node.children:
                col_name = col_node.value
                col_info = self.symbol_table.get_column(table_name, col_name)
                if not col_info:
                    self.error(f"Column '{col_name}' does not exist in table '{table_name}'", 
                               col_node.line, col_node.column)
                    return # Stop checking types if column missing
                target_columns.append(col_info)
            child_idx = 2
        
        # Check values
        value_list_node = node.children[child_idx]
        values = value_list_node.children
        
        if len(values) != len(target_columns):
            self.error(f"Column count mismatch: Expected {len(target_columns)} values but found {len(values)}", 
                       value_list_node.line, value_list_node.column)
            return

        # Type checking logic
        for i, (val_node, col_info) in enumerate(zip(values, target_columns)):
            self.check_type_compatibility(val_node, col_info.data_type, f"Column '{col_info.name}'")

    def visit_select(self, node: ParseTreeNode) -> None:
        # 1. Identify source tables (FROM clause)
        self.current_query_scope = {}
        from_node = self.find_child(node, NodeType.FROM_CLAUSE)
        
        if from_node:
            for child in from_node.children:
                if child.node_type == NodeType.TABLE_NAME:
                    table_name = child.value
                    alias = table_name # Default alias is the name itself
                    
                    if child.children: # Has explicit alias
                        alias = child.children[0].value
                    
                    if not self.symbol_table.get_table(table_name):
                        self.error(f"Table '{table_name}' does not exist", child.line, child.column)
                    
                    self.current_query_scope[alias.upper()] = table_name.upper()
                
                elif child.node_type == NodeType.JOIN:
                     # Join structure: Type, TableRef [alias], ON condition
                     # TableRef is index 1
                     table_ref = child.children[1] 
                     table_name = table_ref.value
                     alias = table_name
                     if table_ref.children:
                         alias = table_ref.children[0].value
                     
                     if not self.symbol_table.get_table(table_name):
                        self.error(f"Table '{table_name}' does not exist", table_ref.line, table_ref.column)
                     
                     self.current_query_scope[alias.upper()] = table_name.upper()

        # 2. Check all columns in SELECT list, WHERE, etc.
        self.visit_children(node)
        self.current_query_scope = {} # Reset scope

    def visit_column(self, node: ParseTreeNode) -> None:
        """Verify column exists in current scope"""
        col_name = node.value
        if not col_name: # Could be an expression alias
            self.visit_children(node)
            return

        # Simple column name check
        found = False
        for alias, table_name in self.current_query_scope.items():
            if self.symbol_table.get_column(table_name, col_name):
                found = True
                break
        
        if not found and self.current_query_scope:
            self.error(f"Column '{col_name}' does not exist in any of the referenced tables", 
                       node.line, node.column)
        
        self.visit_children(node)

    def visit_qualified_name(self, node: ParseTreeNode) -> None:
        """Handle t1.col_name style references"""
        prefix = node.children[0].value.upper()
        col_name = node.children[1].value
        
        if prefix in self.current_query_scope:
            table_name = self.current_query_scope[prefix]
            if not self.symbol_table.get_column(table_name, col_name):
                self.error(f"Column '{col_name}' does not exist in table '{table_name}'", 
                           node.line, node.column)
        else:
            self.error(f"Table alias or name '{prefix}' not found in current query scope", 
                       node.line, node.column)

    def visit_delete(self, node: ParseTreeNode) -> None:
         table_name = node.children[0].value
         if not self.symbol_table.get_table(table_name):
            self.error(f"Table '{table_name}' does not exist", node.line, node.column)
         
         self.current_query_scope = {table_name.upper(): table_name.upper()}
         # Visit WHERE clause
         if len(node.children) > 1:
             self.visit(node.children[1])
         self.current_query_scope = {}

    def visit_update(self, node: ParseTreeNode) -> None:
         table_name = node.children[0].value
         if not self.symbol_table.get_table(table_name):
            self.error(f"Table '{table_name}' does not exist", node.line, node.column)
         
         self.current_query_scope = {table_name.upper(): table_name.upper()}
         self.visit_children(node) # Will check assignments and WHERE
         self.current_query_scope = {}

    def visit_comparison(self, node: ParseTreeNode) -> None:
        """Type checking for comparisons (e.g. age > '18')"""
        left = node.children[0]
        # op = node.children[1] 
        right = node.children[2]
        
        left_type = self.infer_type(left)
        right_type = self.infer_type(right)
        
        # Annotate types on the tree if possible (adding a 'inferred_type' attribute dynamically)
        left.inferred_type = left_type
        right.inferred_type = right_type

        if left_type and right_type:
            if not self.are_types_compatible(left_type, right_type):
                self.error(f"Type mismatch in comparison: cannot compare {left_type} with {right_type}", 
                           node.line, node.column)
    
    # ==================== Helpers ====================

    def check_type_compatibility(self, value_node: ParseTreeNode, target_type: str, context: str) -> None:
        val_type = self.infer_type(value_node)
        if not val_type:
            return # Could not infer, maybe skip or warning
        
        if not self.are_types_compatible(target_type, val_type):
            self.error(f"{context}: Type mismatch. Expected {target_type} but found {val_type}", 
                       value_node.line, value_node.column)

    def infer_type(self, node: ParseTreeNode) -> Optional[str]:
        """Attempt to guess the type of an expression node"""
        if node.node_type == NodeType.LITERAL:
            # value is a string, check format
            val = node.value
            if val.startswith("'") or val.startswith('"'):
                return "VARCHAR"
            if val.isdigit():
                return "INT"
            try:
                float(val)
                return "FLOAT"
            except ValueError:
                pass
            if val.upper() in ['TRUE', 'FALSE']:
                return "BOOLEAN"
            return "UNKNOWN"
        
        elif node.node_type == NodeType.TERMINAL:
            # Could be a column name or a keyword
            # If it matches a known column in current scope, return its type
            col_name = node.value
            for alias, table_name in self.current_query_scope.items():
                col_info = self.symbol_table.get_column(table_name, col_name)
                if col_info:
                    return col_info.data_type
            
            # Additional check for qualified names e.g. t1.col
            if "." in col_name:
                pass # Simple handling for now
            
            return None # Not a literal, maybe a column we couldn't resolve
            
        elif node.node_type == NodeType.EXPRESSION:
             # Logic for recursive type inference (e.g. Int + Int = Int)
             # For now, just visit children
             return self.infer_type(node.children[0])

        return None

    def are_types_compatible(self, type1: str, type2: str) -> bool:
        t1 = type1.upper()
        t2 = type2.upper()
        
        numerics = ['INT', 'INTEGER', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMBER']
        text = ['VARCHAR', 'TEXT', 'CHAR', 'STRING']
        
        if t1 in numerics and t2 in numerics:
            return True
        if t1 in text and t2 in text:
            return True
        if t1 == t2:
            return True
        
        # Allow loose typing for booleans (e.g. 'true', 1, 0)
        if (t1 == 'BOOLEAN' and (t2 in text or t2 in numerics)) or \
           (t2 == 'BOOLEAN' and (t1 in text or t1 in numerics)):
            return True
            
        return False

    def find_child(self, node: ParseTreeNode, type: NodeType) -> Optional[ParseTreeNode]:
        for child in node.children:
            if child.node_type == type:
                return child
        return None

    def error(self, message: str, line: int = 0, column: int = 0):
        self.errors.append(f"Semantic Error at line {line}, column {column}: {message}")

