# SQL reserved words that should be classified as KEYWORD tokens
SQL_KEYWORDS = {
    # Core DML / DDL / clauses
    'ADD', 'ALL', 'ALTER', 'AND', 'ANY', 'AS', 'ASC', 'BETWEEN', 'BY',
    'CASE', 'CHECK', 'COLUMN', 'CREATE', 'DATABASE', 'DEFAULT',
    'DELETE', 'DESC', 'DISTINCT', 'DROP', 'ELSE', 'EXISTS', 'FOREIGN',
    'FROM', 'FULL', 'GROUP', 'HAVING', 'IN', 'INDEX', 'INNER',
    'INSERT', 'INTERSECT', 'INTO', 'IS', 'JOIN', 'KEY', 'LEFT', 'LIKE',
    'LIMIT', 'NOT', 'NULL', 'ON', 'OR', 'ORDER', 'OUTER', 'PRIMARY',
    'REFERENCES', 'RIGHT', 'ROWNUM', 'SELECT', 'SET', 'TABLE', 'TOP',
    'UNION', 'UNIQUE', 'UPDATE', 'VALUES', 'VIEW', 'WHERE',

    # Additional control / structural keywords
    'AFTER', 'BEFORE', 'CASCADE', 'CONTINUE', 'CROSS',
    'CURRENT_TIME', 'DECLARE', 'DESCRIBE', 'EXCEPT', 'FETCH', 'FOR',
    'GRANT', 'GROUPING', 'IF', 'IGNORE', 'INDEXES', 'INTERVAL',
    'ISNULL', 'NATURAL', 'OFFSET', 'PARTITION', 'REPLACE',
    'RETURNING', 'ROLLUP', 'SOME', 'TRUNCATE', 'USING', 'WHEN',
    'WITH', 'WITHIN',

    # Aggregate and built-in functions
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CAST', 'COALESCE',
    'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'ROUND', 'FLOOR', 'CEIL'
}

VALID_DATA_TYPES = {
    'INT', 'INTEGER', 'FLOAT', 'DOUBLE', 'VARCHAR', 'TEXT', 'CHAR', 'BOOLEAN', 'DATE', 'DECIMAL', 'NUMBER'
}
