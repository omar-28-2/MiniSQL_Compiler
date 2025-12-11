# MiniSQL Compiler - Phase 1: Lexical Analyzer

A SQL lexical analyzer (lexer) implemented in Python that breaks down SQL statements into meaningful tokens.

## Features

- ✅ Tokenizes SQL statements into KEYWORD, IDENTIFIER, OPERATOR, DELIMITER, and more
- ✅ Supports 70+ SQL keywords
- ✅ Handles scientific notation (1.5e-10)
- ✅ Supports escaped string quotes ('O''Brien')
- ✅ Multi-character operators (<>, !=, <=, >=, ||, <<, >>)
- ✅ Proper error handling with line/column reporting
- ✅ Web interface using Streamlit
- ✅ Comprehensive error recovery

## Project Structure

```
MiniSQL_Compiler/
├── src/
│   ├── __init__.py      # Package initialization
│   ├── lexer.py         # Lexer implementation
│   ├── app.py           # Streamlit web interface
│   └── README.md        # Source documentation
├── tests/
│   ├── valid_queries.sql
│   ├── invalid_queries.sql
│   ├── advanced_queries.sql
│   └── README.md        # Test documentation
├── .gitignore
├── PROJECT_STRUCTURE.md
└── README.md
```

## Quick Start

### Web Interface
```bash
streamlit run src/app.py
```

### Command Line
```bash
python src/lexer.py tests/valid_queries.sql
```

### As a Module
```python
from src import Lexer

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

## Future Phases

- Phase 2: Parser (syntax analysis)
- Phase 3: Semantic Analyzer (semantic analysis)
- Phase 4: Code Generation

## License

See LICENSE file for details.

## Author

Omar
