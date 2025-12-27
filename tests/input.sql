-- 1. DDL: Create Tables and Views
CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    salary FLOAT,
    active BOOLEAN
);

CREATE VIEW HighValueUsers AS 
SELECT * FROM Users WHERE salary > 5000;

-- 2. DML: Insert Data
INSERT INTO Users (id, name, salary, active) VALUES (1, 'Omar', 15000.50, true);
INSERT INTO Users (id, name, salary, active) VALUES (2, 'Ahmed', 4500.00, false);

-- 3. Complex Selection with Boolean Logic and Math
-- Testing the boolean fix (NOT active) and arithmetic precedence
SELECT name, salary 
FROM Users 
WHERE (salary >= 10000 AND NOT active) 
   OR (salary <= 5000 / 2);

-- 4. Aggregations and Joins
SELECT u.name, COUNT(o.id) 
FROM Users u
LEFT JOIN Orders o ON u.id = o.user_id
GROUP BY u.name
HAVING COUNT(o.id) > 5;

-- 5. Syntax Error for Recovery Testing
-- The parser should detect the missing 'FROM', report it, and recover to parse the next line.
SELECT * WHERE id = 10; 

-- 6. Cleanup
DROP TABLE Users;