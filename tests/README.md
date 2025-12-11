# Test SQL Files

This directory contains test SQL files for the MiniSQL Compiler lexer.

## Files

### `valid_queries.sql`
Contains valid SQL statements that should be tokenized without errors:
- Basic SELECT statements
- SELECT with WHERE clauses
- INSERT statements
- UPDATE statements
- DELETE statements

### `invalid_queries.sql`
Contains intentionally invalid SQL statements to test error handling:
- Unclosed string literals
- Invalid identifiers with typos
- Multiple decimal points in numbers
- Unclosed comments
- Invalid characters

### `advanced_queries.sql`
Contains advanced SQL features supported by the lexer:
- Scientific notation (1.5e-10)
- Escaped quotes in strings ('O''Brien')
- Multi-character operators (<>, !=, <=, >=)
- Aggregate functions (COUNT, SUM, AVG)
- Nested functions
- Complex WHERE clauses with compound operators

### `input.sql`
Mixed test file with both valid and invalid statements for comprehensive testing.

### `test_input.sql`
Standard test file with CREATE, INSERT, UPDATE, SELECT, and DELETE operations.

## Running Tests

To test the lexer with any of these files:

```bash
python src/lexer.py tests/valid_queries.sql
python src/lexer.py tests/invalid_queries.sql
python src/lexer.py tests/advanced_queries.sql
```

Or use the Streamlit interface:
```bash
streamlit run src/app.py
```
