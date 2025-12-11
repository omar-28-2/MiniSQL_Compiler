-- Test: Unclosed string
SELECT * FROM users WHERE name = 'John;

-- Test: Invalid identifier with typo
SLECT id FROM users;

-- Test: Multiple decimal points
SELECT price * 1.2.5 FROM products;

-- Test: Unclosed comment
## This is an unclosed comment
SELECT * FROM users;

-- Test: Invalid character
SELECT * FROM users WHERE id = @invalid;
