import difflib

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f'({self.type}, {self.value})'


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if text else None
        self.line = 1
        self.column = 1
        # SQL reserved words that should be classified as KEYWORD tokens
        self.keywords = {
            # Core DML / DDL / clauses
            'ADD', 'ALL', 'ALTER', 'AND', 'ANY', 'AS', 'ASC', 'BETWEEN', 'BY',
            'CASE', 'CHECK', 'COLUMN', 'CREATE', 'DATABASE', 'DEFAULT',
            'DELETE', 'DESC', 'DISTINCT', 'DROP', 'ELSE', 'EXISTS', 'FOREIGN',
            'FROM', 'FULL', 'GROUP', 'HAVING', 'IN', 'INDEX', 'INNER',
            'INSERT', 'INTERSECT', 'INTO', 'IS', 'JOIN', 'LEFT', 'LIKE',
            'LIMIT', 'NOT', 'NULL', 'ON', 'OR', 'ORDER', 'OUTER', 'PRIMARY',
            'REFERENCES', 'RIGHT', 'ROWNUM', 'SELECT', 'SET', 'TABLE', 'TOP',
            'UNION', 'UNIQUE', 'UPDATE', 'VALUES', 'VIEW', 'WHERE',

            # Additional control / structural keywords
            'AFTER', 'BEFORE', 'CASCADE', 'CONTINUE', 'CROSS',
            'CURRENT_TIME', 'DECLARE', 'DESCRIBE', 'EXCEPT', 'FETCH', 'FOR',
            'GRANT', 'GROUPING', 'IF', 'IGNORE', 'INDEXES', 'INTERVAL',
            'ISNULL', 'NATURAL', 'OFFSET', 'PARTITION', 'REPLACE',
            'RETURNING', 'ROLLUP', 'SOME', 'TRUNCATE', 'USING', 'WHEN',
            'WITH', 'WITHIN', 'GROUP'
        }

    def similar_to_keyword(self, identifier):
        """
        Check if an identifier is similar to any SQL keyword using fuzzy matching.
        Returns the closest keyword match if similarity is high enough.
        """
        identifier_upper = identifier.upper()
        
        # Exact match - it's a keyword
        if identifier_upper in self.keywords:
            return None  # No error, it's correct
        
        # Find close matches
        matches = difflib.get_close_matches(identifier_upper, self.keywords, n=1, cutoff=0.8)
        
        if matches:
            return matches[0]  # Return the closest keyword match
        return None

    def error(self, message):
        # Raise an error with a fully formatted message.
        # Call sites are responsible for including line and position information.
        raise Exception(message)

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
            self.column += 1
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        # Single-line comment
        if self.current_char == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '-':
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
            self.advance()  # Skip the newline character
        # Multi-line comment
        elif self.current_char == '#' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '#':
            start_line = self.line
            start_col = self.column
            self.advance()  # Skip first #
            self.advance()  # Skip second #
            
            while (self.current_char is not None and 
                   not (self.current_char == '#' and 
                        self.pos + 1 < len(self.text) and 
                        self.text[self.pos + 1] == '#')):
                self.advance()
                if self.current_char is None:
                    # Unterminated multi-line comment
                    self.error(f"Error: unclosed comment starting at line {start_line}, position {start_col}.")
            
            if self.current_char is not None:
                self.advance()  # Skip first #
                self.advance()  # Skip second #

    def get_number(self):
        result = ''
        is_float = False
        start_col = self.column
        
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_float:
                    self.error('Invalid number format')
                is_float = True
            result += self.current_char
            self.advance()
            
        return ('FLOAT' if is_float else 'INTEGER'), result

    def get_identifier(self):
        result = ''
        start_col = self.column
        
        while (self.current_char is not None and 
               (self.current_char.isalnum() or self.current_char == '_')):
            result += self.current_char
            self.advance()
        
        # Check if it's an exact keyword match
        if result.upper() in self.keywords:
            return 'KEYWORD', result.upper()
        
        # Check if it's similar to a keyword (potential misspelling)
        similar_keyword = self.similar_to_keyword(result)
        if similar_keyword:
            self.error(f"Error: invalid identifier '{result}' at line {self.line}, position {start_col}. Did you mean '{similar_keyword}'?")
        
        return 'IDENTIFIER', result

    def get_string(self):
        result = ''
        start_line = self.line
        start_col = self.column
        self.advance()  # Skip the opening quote
        
        while self.current_char is not None and self.current_char != "'":
            if self.current_char == '\n':
                # Unclosed string before end of line
                self.error(f"Error: unclosed string starting at line {start_line}, position {start_col}.")
            result += self.current_char
            self.advance()
        
        if self.current_char != "'":
            # End of file reached without closing quote
            self.error(f"Error: unclosed string starting at line {start_line}, position {start_col}.")
        
        self.advance()  # Skip the closing quote
        return 'STRING', f"'{result}'"

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            if self.current_char == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '-':
                self.skip_comment()
                continue
                
            if self.current_char == '#' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '#':
                self.skip_comment()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                token_type, token_value = self.get_identifier()
                return Token(token_type, token_value, self.line, self.column - len(token_value) + 1)

            if self.current_char.isdigit():
                token_type, token_value = self.get_number()
                return Token(token_type, token_value, self.line, self.column - len(token_value) + 1)

            if self.current_char == "'":
                token_type, token_value = self.get_string()
                return Token(token_type, token_value, self.line, self.column - len(token_value) + 1)

            # Handle operators and delimiters
            if self.current_char in '=<>!':
                start = self.column
                char = self.current_char
                self.advance()
                
                if self.current_char == '=':
                    operator = char + self.current_char
                    self.advance()
                    return Token('OPERATOR', operator, self.line, start)
                else:
                    if char == '=':
                        return Token('OPERATOR', '=', self.line, start)
                    return Token('OPERATOR', char, self.line, start)
            
            if self.current_char in '+-*/':
                token = Token('OPERATOR', self.current_char, self.line, self.column)
                self.advance()
                return token
                
            if self.current_char in '(),;':
                # Delimiters: symbols that separate SQL constructs
                # All of these share the same token type 'DELIMITER';
                # the specific symbol is stored in the value.
                token = Token('DELIMITER', self.current_char, self.line, self.column)
                self.advance()
                return token

            # Dot should be its own token so qualified names split: d . department
            if self.current_char == '.':
                token = Token('DOT', '.', self.line, self.column)
                self.advance()
                return token

            # If we get here, we have an unknown/invalid character
            self.error(
                f"Error: invalid character {self.current_char!r} at line {self.line}, position {self.column}."
            )

        return Token('EOF', None, self.line, self.column)


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python lexer.py <input_file>")
        return

    try:
        with open(sys.argv[1], 'r') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Error: File '{sys.argv[1]}' not found.")
        return

    lexer = Lexer(text)
    tokens = []
    errors = []

    while True:
        try:
            token = lexer.get_next_token()
            if token.type == 'EOF':
                break
            tokens.append(token)
            print(token)
        except Exception as e:
            errors.append(str(e))
            # Try to recover by advancing to the next character
            if lexer.current_char is not None:
                lexer.advance()
            continue

    print("\nSymbol Table:")
    symbols = {}
    for token in tokens:
        if token.type in ['IDENTIFIER', 'STRING', 'INTEGER', 'FLOAT']:
            if token.value not in symbols:
                symbols[token.value] = token.type

    for value, type_ in symbols.items():
        print(f"{value}: {type_}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"- {err}")


if __name__ == '__main__':
    main()