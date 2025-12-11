CREATE TABLE Users (UserID INT,UserName TEXT, Balance FLOAT, Active BOOLEAN, Salary_2025 INT);

INSERT INTO Users VALUES (101, 'Alice Smith', 'true');

UPDATE Users SET Balance = 99.99 WHERE UserID = 101 AND UserName = 'Alice Smith';

select name from users WHERE id = 5;

DELETE FROM Users WHERE UserID > 100 OR Balance < 500;

SELECT * FROM Users WHERE (Salary_2025 >= 10000 AND NOT Active) OR (Balance <= 5000 / 2);
