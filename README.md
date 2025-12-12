# MiniSQL Compiler - Complete Implementation

A comprehensive SQL compiler implementation consisting of:
- **Phase 01**: Lexical Analyzer (Lexer)
- **Phase 02**: Syntax Analyzer (Parser with Parse Tree Generation)

## Overview

This project implements a complete compiler frontend for a SQL-like language, capable of:
1. **Tokenizing** SQL statements into a stream of tokens (Phase 01)
2. **Parsing** tokens into an Abstract Syntax Tree (Phase 02)
3. **Detecting and reporting** syntax errors with precise location information
4. **Recovering** from errors to find multiple issues in one pass

## Features

### Phase 01: Lexical Analysis ✅
- ✅ Tokenizes SQL statements into KEYWORD, IDENTIFIER, OPERATOR, DELIMITER, and more
- ✅ Supports 70+ SQL keywords
- ✅ Handles scientific notation (1.5e-10)
- ✅ Supports escaped string quotes ('O''Brien')
- ✅ Multi-character operators (<>, !=, <=, >=, ||, <<, >>)
- ✅ Proper error handling with line/column reporting
- ✅ Comment support (both -- and ## styles)

### Phase 02: Syntax Analysis ✅
- ✅ **Recursive Descent Parser** - Hand-written, no parser generators
- ✅ **Parse Tree Generation** - Explicit derivation of statements
- ✅ **50+ SQL Constructs** supported
- ✅ **DDL Support**: CREATE/ALTER/DROP TABLE, DATABASE, VIEW, INDEX
- ✅ **DML Support**: SELECT, INSERT, UPDATE, DELETE
- ✅ **Complex Conditions**: AND/OR/NOT with proper precedence
- ✅ **Special Operators**: BETWEEN, IN, LIKE, IS NULL
- ✅ **JOINs**: INNER, LEFT, RIGHT, FULL, CROSS
- ✅ **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX
- ✅ **Error Detection & Recovery**: Panic mode error recovery
- ✅ **Comprehensive Error Reporting**: Line, column, expected vs. found

## Project Structure

```
MiniSQL_Compiler/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── lexer.py                 # Phase 01: Lexer (380 lines)
│   ├── parser.py                # Phase 02: Parser (1800+ lines)
│   ├── app.py                   # Streamlit web interface
│   └── __pycache__/             # Python cache
├── tests/
│   ├── valid_queries.sql        # Valid test cases
│   ├── invalid_queries.sql      # Error handling tests
│   ├── advanced_queries.sql     # Complex queries
│   ├── test_parser.py          # Parser test suite
│   ├── test_input.sql          # General input
│   └── README.md               # Test documentation
├── LICENSE                      # MIT License
├── README.md                    # This file
├── PARSER_DOCUMENTATION.md     # Complete parser API docs
└── PHASE_02_SUMMARY.md        # Implementation summary
```

## Quick Start

### 1. Web Interface (Recommended)
```bash
cd src
streamlit run app.py
```

Open your browser to `http://localhost:8501`

### 2. Command Line Testing
```bash
# Run lexer on SQL file
python src/lexer.py tests/valid_queries.sql

# Run full test suite
python tests/test_parser.py
```

### 3. As a Python Module
```python
from src import Lexer, Parser, parse_sql

# Method 1: Using the convenience function
tree, lex_errors, parse_errors = parse_sql("SELECT * FROM users WHERE age > 18;")

# Method 2: Using individual components
lexer = Lexer(sql_code)
tokens = [token for token in lexer.get_tokens() if token.type != 'EOF']

parser = Parser(tokens)
tree = parser.parse()

if parser.errors:
    for error in parser.errors:
        print(error)
else:
    print(tree.to_string())
```

## Language Support

### Supported SQL Statements

#### DDL (Data Definition Language)
```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(50) NOT NULL);
CREATE DATABASE mydb;
CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active';
CREATE INDEX idx_user_id ON users(id);

ALTER TABLE users ADD COLUMN email VARCHAR(100);
ALTER TABLE users DROP COLUMN age;

DROP TABLE users;
DROP DATABASE mydb;
DROP VIEW active_users;
DROP INDEX idx_user_id;
```

#### DML (Data Manipulation Language)
```sql
-- SELECT with all clauses
SELECT DISTINCT u.id, u.name, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.age > 18 AND u.status = 'active'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC
LIMIT 10;

-- INSERT
INSERT INTO users (id, name, age) VALUES (1, 'John', 25);

-- UPDATE
UPDATE users SET age = 26 WHERE name = 'John';

-- DELETE
DELETE FROM users WHERE id = 1;
```

### Operators and Conditions

#### Logical Operators
```sql
WHERE age > 18 AND status = 'active'
WHERE country = 'USA' OR country = 'Canada'
WHERE NOT deleted
WHERE (age > 18 AND status = 'active') OR premium = 1
```

#### Comparison Operators
```sql
=, <>, !=, <, >, <=, >=
BETWEEN ... AND ...
IN (list, of, values)
LIKE '%pattern%'
IS NULL, IS NOT NULL
```

#### Aggregate Functions
```sql
SELECT COUNT(*), COUNT(DISTINCT user_id), SUM(amount), AVG(price), MIN(date), MAX(total)
```

#### Built-in Functions
```sql
SUBSTR(string, start, length)
LENGTH(string)
UPPER(string), LOWER(string)
ROUND(number, decimals)
FLOOR(number), CEIL(number)
CAST(expr AS type)
COALESCE(expr1, expr2, ...)
```

## Web Interface Features

### Tab 1: Input & Tokens
- Upload SQL files
- View source code
- Display token table (Type, Lexeme, Line, Column)
- Show lexical errors

### Tab 2: Parse Tree
- Display syntax errors with context
- Tree visualization (interactive with proper ASCII formatting)
- JSON representation
- Parse tree structure

### Tab 3: Analysis Summary
- Statistics dashboard
- Token type distribution
- Error summary
- Compilation status

## Error Handling

### Detection
The parser detects:
- ❌ Unexpected tokens
- ❌ Missing required tokens
- ❌ Type mismatches
- ❌ Incomplete clauses
- ❌ Syntax violations

### Reporting
Each error includes:
```
Syntax Error at line 5, column 12: Expected 'FROM' but found 'WHERE'.
```

### Recovery
- Uses **Panic Mode** recovery
- Skips tokens until finding sync point (`;` or major keyword)
- Continues parsing to find more errors
- Reports all errors in one pass

## Examples

### Example 1: Simple SELECT
**Input:**
```sql
SELECT id, name FROM users WHERE age > 18;
```

**Parse Tree:**
```
Select
├── SelectList
│   ├── Column: 'id'
│   └── Column: 'name'
├── FromClause
│   └── TableName: 'users'
└── WhereClause
    └── Comparison
        ├── Column: 'age'
        ├── Terminal: '>'
        └── Literal: '18'
```

### Example 2: JOIN with GROUP BY
**Input:**
```sql
SELECT d.name, COUNT(e.id) FROM departments d 
LEFT JOIN employees e ON d.id = e.dept_id 
GROUP BY d.name;
```

**Parsing Result:** ✅ Success (0 errors)

### Example 3: Error Detection
**Input:**
```sql
SELECT id, name WHERE age > 18;
```

**Errors:**
```
⚠ Syntax Error at line 1, column 18: Missing FROM clause before WHERE
```

## Performance

| Metric | Value |
|--------|-------|
| Time Complexity | O(n) |
| Space Complexity | O(d) |
| Typical Parse Time | < 100ms |
| Max Tested Statements | 1000+ |

## Testing

Run the comprehensive test suite:
```bash
python tests/test_parser.py
```

Tests include:
- ✅ 20+ valid SQL statements
- ✅ 10+ error cases
- ✅ Edge cases
- ✅ Complex nested queries
- ✅ All operator types
- ✅ All statement types

## Documentation

- **[PARSER_DOCUMENTATION.md](PARSER_DOCUMENTATION.md)** - Complete API reference
- **[PHASE_02_SUMMARY.md](PHASE_02_SUMMARY.md)** - Implementation summary
- **[src/README.md](src/README.md)** - Source code documentation
- **[tests/README.md](tests/README.md)** - Test documentation

## Implementation Details

### Architecture
```
SQL Source Code
    ↓
Lexer (Phase 01)
    ↓
Token Stream
    ↓
Parser (Phase 02)
    ↓
Parse Tree (AST)
    ↓
[Future: Semantic Analysis, Code Generation]
```

### Key Classes

- **Token**: Represents a single token (type, value, line, column)
- **Lexer**: Tokenizes SQL source code
- **ParseTreeNode**: Node in the abstract syntax tree
- **Parser**: Implements recursive descent parsing
- **SyntaxErrorInfo**: Error with full context

### Parsing Technique
- **Recursive Descent**: Direct implementation of grammar rules
- **Operator Precedence**: Iterative handling in expression parsing
- **Error Recovery**: Panic mode synchronization
- **Lookahead**: Minimal (0-1 tokens typically)

## Supported Grammar

The parser supports a comprehensive Context-Free Grammar (CFG) with:
- 50+ grammar rules
- 52 node types
- Full SQL expression syntax
- Complex boolean conditions
- All major SQL constructs

See [PARSER_DOCUMENTATION.md](PARSER_DOCUMENTATION.md) for complete grammar specification.

## Requirements

- Python 3.8+
- Streamlit (for web interface)
- No external parser generators (hand-written parser)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd MiniSQL_Compiler

# Install dependencies
pip install streamlit pandas

# Run web interface
cd src
streamlit run app.py
```

## Limitations & Future Work

### Current Limitations
- Subqueries: Partial support only
- Window functions: Not implemented
- CTEs (WITH clause): Not supported
- Array/JSON types: Not supported

### Planned Enhancements
1. **Semantic Analysis**
   - Type checking
   - Column existence validation
   - Constraint validation

2. **Optimization**
   - Query plan generation
   - Statistics-based optimization

3. **Extended SQL Support**
   - Subqueries in all positions
   - Window functions
   - Common Table Expressions
   - Set operations (UNION, INTERSECT, EXCEPT)

## Contributing

This is an educational project. Contributions welcome for:
- Bug fixes
- Documentation improvements
- Test cases
- Grammar enhancements

## License

MIT License - See [LICENSE](LICENSE) file

## Author

Omar (2025)

## Acknowledgments

Based on compiler design principles from:
- "Compilers: Principles, Techniques, and Tools" (Aho, Lam, Sethi, Ullman)
- Standard SQL-92 specification
- Recursive Descent Parsing techniques

---

## Status

✅ **Phase 01 (Lexer)**: Complete
✅ **Phase 02 (Parser)**: Complete

Ready for Phase 03 (Semantic Analysis) if needed.

**Last Updated**: December 2025

## Recent Fixes (December 2025)

### Bug Fixes
- ✅ **Fixed CREATE TABLE parsing**: Corrected DELIMITER type checking in `parse_data_type()` and `parse_column_definitions()`
- ✅ **Fixed comparison operators**: Resolved parsing issues with `>=` and `<=` operators in conditions
- ✅ **Fixed boolean conditions**: Added support for bare expressions (e.g., `NOT Active`) as valid conditions
- ✅ **Improved token type checking**: Replaced 7 incorrect `match()` calls with proper `match_type('DELIMITER')` checks throughout parser

### UI Improvements
- ✅ **Removed Text Tree view**: Simplified output display to show only Visual Tree and JSON Structure options
- ✅ **Enhanced parse tree visualization**: Interactive tree view with proper formatting

### Testing
- ✅ All test queries now parse without errors
- ✅ Verified complex WHERE conditions with multiple operators
- ✅ Tested arithmetic expressions in conditions (e.g., `Balance <= 5000 / 2`)

**Branch**: `fix/syntax-errors` with 4 focused commits documenting each fix

lexer = Lexer("SELECT * FROM users;")
while True:
    token = lexer.get_next_token()
    if token.type == 'EOF':
        break
    print(token)
```

## Token Types

- **KEYWORD**: SQL reserved words (SELECT, INSERT, WHERE, etc.)
- **IDENTIFIER**: Variable, table, and column names
- **STRING**: Text literals ('...')
- **INTEGER**: Whole numbers (123)
- **FLOAT**: Decimal numbers and scientific notation (1.5e-10)
- **OPERATOR**: Arithmetic operators (+, -, *, /, %)
- **COMPARISON**: Comparison operators (<, >, =, !=, <>, <=, >=)
- **DELIMITER**: Punctuation (,, (, ), ;)
- **DOT**: Qualified names (table.column)
- **EOF**: End of file

## Supported SQL Keywords

Core operations: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
Clauses: WHERE, FROM, JOIN, GROUP BY, ORDER BY, HAVING
Functions: COUNT, SUM, AVG, MIN, MAX, CAST, COALESCE, SUBSTR, LENGTH, UPPER, LOWER, ROUND, FLOOR, CEIL

## Error Detection

The lexer detects and reports:
- Invalid characters
- Unclosed strings
- Unclosed comments
- Invalid number formats
- Syntax errors with line and column information

## Testing

Multiple test files provided:
- **valid_queries.sql**: Valid SQL statements
- **invalid_queries.sql**: Invalid SQL for error testing
- **advanced_queries.sql**: Advanced features (scientific notation, escaping, etc.)

## Documentation

- **PROJECT_STRUCTURE.md**: Detailed project organization
- **src/README.md**: Source code documentation
- **tests/README.md**: Test files documentation

## Recent Improvements

- Fixed column position tracking bug
- Enhanced keyword fuzzy matching
- Added scientific notation support
- Added escaped string quote support
- Improved operator handling (multi-character, bitwise)
- Better error messages and recovery
- Comprehensive project structure and documentation

## Recent Fixes (December 2025)

### Bug Fixes
- ✅ **Fixed CREATE TABLE parsing**: Corrected DELIMITER type checking in `parse_data_type()` and `parse_column_definitions()`
- ✅ **Fixed comparison operators**: Resolved parsing issues with `>=` and `<=` operators in conditions
- ✅ **Fixed boolean conditions**: Added support for bare expressions (e.g., `NOT Active`) as valid conditions
- ✅ **Improved token type checking**: Replaced 7 incorrect `match()` calls with proper `match_type('DELIMITER')` checks throughout parser

### UI Improvements
- ✅ **Removed Text Tree view**: Simplified output display to show only Visual Tree and JSON Structure options
- ✅ **Enhanced parse tree visualization**: Interactive tree view with proper formatting

### Testing
- ✅ All test queries now parse without errors
- ✅ Verified complex WHERE conditions with multiple operators
- ✅ Tested arithmetic expressions in conditions (e.g., `Balance <= 5000 / 2`)

**Branch**: `fix/syntax-errors` with 4 focused commits documenting each fix

## Recent Fixes (December 2025)

### Bug Fixes
- ✅ **Fixed CREATE TABLE parsing**: Corrected DELIMITER type checking in `parse_data_type()` and `parse_column_definitions()`
- ✅ **Fixed comparison operators**: Resolved parsing issues with `>=` and `<=` operators in conditions
- ✅ **Fixed boolean conditions**: Added support for bare expressions (e.g., `NOT Active`) as valid conditions
- ✅ **Improved token type checking**: Replaced 7 incorrect `match()` calls with proper `match_type('DELIMITER')` checks throughout parser

### UI Improvements
- ✅ **Removed Text Tree view**: Simplified output display to show only Visual Tree and JSON Structure options
- ✅ **Enhanced parse tree visualization**: Interactive tree view with proper formatting

### Testing
- ✅ All test queries now parse without errors
- ✅ Verified complex WHERE conditions with multiple operators
- ✅ Tested arithmetic expressions in conditions (e.g., `Balance <= 5000 / 2`)

**Branch**: `fix/syntax-errors` with 4 focused commits documenting each fix

## Future Phases

- Phase 2: Parser (syntax analysis)
- Phase 3: Semantic Analyzer (semantic analysis)
- Phase 4: Code Generation

## License

See LICENSE file for details.
