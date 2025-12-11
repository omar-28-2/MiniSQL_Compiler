-- Test: Basic SELECT statement
SELECT * FROM users;

-- Test: SELECT with WHERE clause
SELECT id, name, email FROM customers WHERE age > 18;

-- Test: INSERT statement
INSERT INTO products (id, name, price) VALUES (1, 'Laptop', 999.99);

-- Test: UPDATE statement
UPDATE employees SET salary = 5000 WHERE department = 'Sales';

-- Test: DELETE statement
DELETE FROM logs WHERE created_date < '2020-01-01';
