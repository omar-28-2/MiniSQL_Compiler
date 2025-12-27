import difflib
from constants import SQL_KEYWORDS


class LexerError(Exception):
    """Custom exception for lexer errors"""
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexical Error at line {line}, column {column}: {message}")


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
        self.token_start_col = 1  # Track where current token started
        # SQL reserved words that should be classified as KEYWORD tokens
        self.keywords = SQL_KEYWORDS
        
        # Multi-character operators
        self.multi_char_operators = {
            '==': 'OPERATOR',
            '<>': 'COMPARISON',
            '!=': 'COMPARISON',
            '<=': 'COMPARISON',
            '>=': 'COMPARISON',
            '||': 'OPERATOR',
            '<<': 'OPERATOR',  
            '>>': 'OPERATOR',  
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
        
        matches = difflib.get_close_matches(identifier_upper, self.keywords, n=1, cutoff=0.65)
        
        if matches:
            return matches[0]  # Return the closest keyword match
        return None

    def error(self, message):
        # Raise a custom lexer error with a fully formatted message.
        raise LexerError(message, self.line, self.column)

    def advance(self):
        """Move to the next character and properly track line/column position"""
        if self.current_char == '\n':
            self.line += 1
            self.column = 1  # Reset to 1, not 0
        else:
            self.column += 1
        
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comments(self):
        """Skip single line comments (--) and multi-line comments (##)"""
        # Multi-line comments ## ... ##
        if self.current_char == '#' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '#':
            start_line = self.line
            start_col = self.column
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
        """Parse numeric literals including integers, floats, and scientific notation"""
        result = ''
        is_float = False
        start_col = self.column
        
        # Parse the main number part
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_float:
                    self.error('Invalid number format: multiple decimal points')
                is_float = True
            result += self.current_char
            self.advance()
        
        # Handle scientific notation (e.g., 1.5e-10, 3E+5)
        if self.current_char is not None and self.current_char.lower() == 'e':
            is_float = True
            result += self.current_char
            self.advance()
            
            # Optional sign after 'e'
            if self.current_char is not None and self.current_char in '+-':
                result += self.current_char
                self.advance()
            
            # Exponent digits
            if self.current_char is None or not self.current_char.isdigit():
                self.error('Invalid number format: exponent requires digits after "e"')
            
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
        
        return ('FLOAT' if is_float else 'INTEGER'), result

    def get_identifier(self):
        """Parse identifiers and check for keywords"""
        result = ''
        start_col = self.column
        
        while (self.current_char is not None and 
               (self.current_char.isalnum() or self.current_char == '_')):
            result += self.current_char
            self.advance()
        
        # Check if it's an exact keyword match
        if result.upper() in self.keywords:
            return 'KEYWORD', result.upper()
        
        # Check if it's similar to a keyword (potential misspelling) - only warn, don't error
        similar_keyword = self.similar_to_keyword(result)
        if similar_keyword:
            # Store similar keyword info but don't throw error - let it be an identifier
            # This allows for domain-specific identifiers while providing a warning mechanism
            pass
        
        return 'IDENTIFIER', result 

    def get_string(self):
        """Parse string literals with support for escaped quotes"""
        result = ''
        start_line = self.line
        start_col = self.column
        self.advance()  # Skip the opening quote
        
        while self.current_char is not None:
            # Handle escaped quotes (SQL uses '' for a single quote inside a string)
            if self.current_char == "'" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "'":
                result += "'"
                self.advance()  # Skip first quote
                self.advance()  # Skip second quote
                continue
            
            # Check for closing quote
            if self.current_char == "'":
                break
                
            if self.current_char == '\n':
                # Unclosed string before end of line
                self.error(f"Unclosed string starting at line {start_line}, column {start_col}.")
            
            result += self.current_char
            self.advance()
        
        if self.current_char != "'":
            # End of file reached without closing quote
            self.error(f"Unclosed string starting at line {start_line}, column {start_col}.")
        
        self.advance()  # Skip the closing quote
        return 'STRING', f"'{result}'"

    def get_next_token(self):
        """Get the next token from the input"""
        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # Skip comments
            if self.current_char == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '-':
                self.skip_comments()
                continue
            
            if self.current_char == '#' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '#':
                self.skip_comments()
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == '_':
                self.token_start_col = self.column
                token_type, token_value = self.get_identifier()
                return Token(token_type, token_value, self.line, self.token_start_col)

            # Numbers (including scientific notation)
            if self.current_char.isdigit():
                self.token_start_col = self.column
                token_type, token_value = self.get_number()
                return Token(token_type, token_value, self.line, self.token_start_col)

            # Strings
            if self.current_char == "'":
                self.token_start_col = self.column
                token_type, token_value = self.get_string()
                return Token(token_type, token_value, self.line, self.token_start_col)

            # Multi-character operators (must check before single-char operators)
            if self.pos + 1 < len(self.text):
                two_char = self.current_char + self.text[self.pos + 1]
                if two_char in self.multi_char_operators:
                    self.token_start_col = self.column
                    self.advance()
                    self.advance()
                    return Token(self.multi_char_operators[two_char], two_char, self.line, self.token_start_col)
            
            # Single character operators and comparison operators
            if self.current_char in '=<>!':
                self.token_start_col = self.column
                char = self.current_char
                self.advance()
                
                # Determine operator type
                if char == '=':
                    return Token('OPERATOR', '=', self.line, self.token_start_col)
                else:
                    return Token('COMPARISON', char, self.line, self.token_start_col)
            
            # Arithmetic operators
            if self.current_char in '+-*':
                self.token_start_col = self.column
                token = Token('OPERATOR', self.current_char, self.line, self.token_start_col)
                self.advance()
                return token
            
            # Division and modulo
            if self.current_char == '/':
                self.token_start_col = self.column
                token = Token('OPERATOR', '/', self.line, self.token_start_col)
                self.advance()
                return token
            
            if self.current_char == '%':
                self.token_start_col = self.column
                token = Token('OPERATOR', '%', self.line, self.token_start_col)
                self.advance()
                return token
            
            # Bitwise operators
            if self.current_char in '&|^':
                self.token_start_col = self.column
                token = Token('OPERATOR', self.current_char, self.line, self.token_start_col)
                self.advance()
                return token
            
            # Delimiters
            if self.current_char in '(),;':
                self.token_start_col = self.column
                token = Token('DELIMITER', self.current_char, self.line, self.token_start_col)
                self.advance()
                return token

            # Dot for qualified names
            if self.current_char == '.':
                self.token_start_col = self.column
                token = Token('DOT', '.', self.line, self.token_start_col)
                self.advance()
                return token

            # Unknown character
            self.error(
                f"Invalid character '{self.current_char}' at line {self.line}, column {self.column}."
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
        except LexerError as e:
            errors.append(str(e))
            # Try to recover by advancing to the next character
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break

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
