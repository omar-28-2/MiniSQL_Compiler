-- Correct statement
SELECT first_name, last_name, salary
FROM employees
WHERE salary >= 40000;
selec * FROM employees WHERE salary <>== 65;
-- Invalid identifier and keyword
INSER INTO employes (id, name) VALUES (102, 'Alice');

-- Unterminated string literal
INSERT INTO employees (id, name, salary) VALUES (103, 'Bob', 45000);

-- Invalid character
UPDATE employees SET salary = 50000 WHERE id = 104;

-- Unterminated multi-line comment

## SELECT * FROM employees WHERE salary <>== 65;
-- Missing closing parenthesis
SELECT name, salary FROM employees WHERE department_id = (SELECT department_id FROM departments;)

-- Invalid operator
selecc * FROM employees WHERE salary <>== 50000;
