-- Test: Scientific notation
SELECT value FROM measurements WHERE value = 1.5e-10;

-- Test: Escaped quotes in strings
SELECT 'O''Brien' AS name FROM employees;

-- Test: Multi-character operators
SELECT * FROM users WHERE age <= 25 AND balance >= 1000;

-- Test: Aggregate functions
SELECT COUNT(*), SUM(salary), AVG(age) FROM employees;

-- Test: Nested functions
SELECT UPPER(SUBSTR(name, 1, 3)) FROM users;

-- Test: Complex WHERE clause
SELECT * FROM orders WHERE (status <> 'cancelled' OR status != 'pending') AND total > 100;
