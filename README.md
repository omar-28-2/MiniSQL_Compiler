# 📊 **MiniSQL Compiler – Phase 01, 02 & 03**  
*A Complete SQL Compiler Implementation with Lexical, Syntax, and Semantic Analysis*

---

## 📌 **Project Overview**
This project implements a full compiler frontend for a SQL-like language across three phases:

- **Phase 01** – Lexical Analysis (Tokenizer)  
- **Phase 02** – Syntax Analysis (Parser)  
- **Phase 03** – Semantic Analysis (Type & Scope Checking)

The compiler processes SQL statements, validates their structure and meaning, and outputs detailed analysis results via a modern **Streamlit web interface**.

---

## 🚀 **Features**

### ✅ **Phase 01: Lexical Analyzer**
- Tokenizes SQL statements into: `KEYWORD`, `IDENTIFIER`, `OPERATOR`, `DELIMITER`, `STRING`, `INTEGER`, `FLOAT`, `COMPARISON`, `DOT`, `EOF`
- Supports **60+ SQL keywords** and **multi-character operators** (`<>`, `!=`, `<=`, `>=`, `||`)
- Handles **scientific notation**, escaped strings, and comments (`--` and `##`)
- **Error recovery** with line/column reporting
- **Symbol table** generation

### ✅ **Phase 02: Syntax Analyzer**
- **Recursive Descent Parser** (hand-written, no generators)
- Supports **DDL** (`CREATE`, `ALTER`, `DROP`) and **DML** (`SELECT`, `INSERT`, `UPDATE`, `DELETE`)
- **Complex condition parsing**: `AND`, `OR`, `NOT`, `BETWEEN`, `IN`, `LIKE`, `IS NULL`
- **JOIN support**: `INNER`, `LEFT`, `RIGHT`, `FULL`, `CROSS`
- **Aggregate functions**: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- **Parse Tree generation** with interactive visualization
- **Panic-mode error recovery** – reports multiple errors per run

### ✅ **Phase 03: Semantic Analyzer**
- **Symbol Table management** with table/column metadata
- **Identifier validation** – ensures tables/columns exist
- **Type checking** – validates data type compatibility in `INSERT`, `WHERE`, comparisons
- **Constraint validation** – checks `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`, `DEFAULT`, `CHECK`
- **Scope resolution** – handles table aliases and qualified names (`table.column`)
- **Semantic error reporting** with context and suggestions

---

## 🧱 **Project Structure**

```
MiniSQL_Compiler/
├── src/
│   ├── __init__.py           # Package exports
│   ├── lexer.py              # Phase 01 – Lexical Analyzer
│   ├── parser.py             # Phase 02 – Syntax Analyzer
│   ├── semantic.py           # Phase 03 – Semantic Analyzer
│   ├── constants.py          # SQL keywords & data types
│   └── app.py               # Streamlit web interface
├── tests/
│   ├── valid_queries.sql
│   ├── invalid_queries.sql
│   ├── advanced_queries.sql
│   └── semantic_test.sql
├── screenshots/              # Output examples
├── README.md
├── LICENSE
└── requirements.txt
```

---

## 🖥️ **Web Interface (Streamlit)**
The interface provides four tabs for comprehensive analysis:

| Tab | Description |
|-----|-------------|
| **Input & Tokens** | Upload SQL file, view tokens, lexical errors |
| **Parse Tree** | Visual/JSON tree, syntax errors, tree statistics |
| **Semantic Analysis** | Symbol table, type annotations, semantic errors |
| **Analysis Summary** | Compilation dashboard, token stats, error breakdown |

---

## ⚙️ **Installation & Usage**

### 1. **Clone & Install**
```bash
git clone https://github.com/yourusername/MiniSQL_Compiler.git
cd MiniSQL_Compiler
pip install streamlit pandas
```

### 2. **Run Web Interface**
```bash
cd src
streamlit run app.py
```
Open browser at: `http://localhost:8501`

### 3. **Upload SQL File**
Use the file uploader to load `.sql` files. The compiler will automatically run all three phases.

---

## 📘 **Example SQL Supported**

```sql
-- DDL
CREATE TABLE Users (
    UserID INT PRIMARY KEY,
    UserName TEXT NOT NULL,
    Balance FLOAT,
    Active BOOLEAN,
    Salary_2025 INT
);

-- DML
INSERT INTO Users VALUES (101, 'Alice Smith', 5998.99, true, 75689);

UPDATE Users SET Balance = 99.99 
WHERE UserID = 101 AND UserName = 'Alice Smith';

SELECT UserName FROM Users WHERE UserID = 5;

DELETE FROM Users WHERE UserID = 100 OR Balance < 500;
```

---

## 🔍 **Error Handling Examples**

### Lexical Error
```
Lexical Error at line 3, column 5: Invalid character '@'
```

### Syntax Error
```
Syntax Error at line 5, column 12: Expected 'FROM' but found 'WHERE'
```

### Semantic Error
```
Semantic Error at line 7, column 20: 
Column 'age' is defined as INT, but a STRING literal was provided.
```

---

## 📈 **Performance & Metrics**

| Metric | Value |
|--------|-------|
| Lines of Code (Total) | ~2,000 |
| Lexer Speed | O(n) |
| Parser Speed | O(n) |
| Semantic Analysis | O(n) |
| Max Tested Statements | 100+ |
| Web UI Response Time | < 200ms |

---

## 🧪 **Testing**
Test files included:
- `valid_queries.sql` – Valid SQL for all phases
- `invalid_queries.sql` – Syntax/semantic error cases
- `advanced_queries.sql` – Complex joins, aggregates
- `semantic_test.sql` – Type/compatibility edge cases

---

## 📚 **Formal Grammar (EBNF Excerpt)**

```ebnf
Program        = { Statement ";" } ;
Statement      = SelectStmt | InsertStmt | UpdateStmt | DeleteStmt 
               | CreateTable | AlterTable | DropTable ;
SelectStmt     = "SELECT" [ "DISTINCT" ] SelectList 
                 "FROM" TableRef { Join } 
                 [ "WHERE" Condition ] 
                 [ "GROUP" "BY" ColumnList ] 
                 [ "HAVING" Condition ] 
                 [ "ORDER" "BY" SortList ] 
                 [ "LIMIT" Integer ] ;
Condition      = AndCondition { "OR" AndCondition } ;
AndCondition   = NotCondition { "AND" NotCondition } ;
NotCondition   = [ "NOT" ] PrimaryCondition ;
PrimaryCondition = Comparison | Between | In | Like | IsNull | "(" Condition ")" ;
```

---

## 🛠 **Implementation Highlights**

### **Lexer (`lexer.py`)**
- Character-by-character scanning with lookahead
- Line/column tracking for precise error reporting
- Keyword similarity suggestion using `difflib`

### **Parser (`parser.py`)**
- Hand-written recursive descent with precedence climbing
- Parse tree nodes store source location
- Error recovery via synchronization tokens (`;`, `SELECT`, `CREATE`)

### **Semantic Analyzer (`semantic.py`)**
- Hierarchical symbol table with table/column metadata
- Type inference for literals and expressions
- Scope-aware column resolution

---

## 📄 **Report Summary**

### **Phase 01 – Lexical Analysis**
- **Tokens Generated**: 9 token types, 60+ keywords
- **Error Recovery**: Continues after errors, reports all
- **Symbol Table**: Unique identifiers with types
- **Challenges Solved**: Unclosed strings, comments, scientific notation

### **Phase 02 – Syntax Analysis**
- **Parsing Technique**: Recursive Descent
- **Grammar Coverage**: 50+ SQL constructs
- **Error Reporting**: Line, column, expected vs found
- **Output**: Parse tree with statistics (depth, nodes, terminals)

### **Phase 03 – Semantic Analysis**
- **Validation Types**: Existence, type compatibility, constraints
- **Symbol Table**: Persists across statements
- **Error Detection**: 11+ semantic rules enforced
- **Output**: Annotated tree with inferred types

---

## 🔮 **Future Enhancements**
1. **Query Optimization** – Cost-based optimization
2. **Intermediate Code Generation** – Three-address code
3. **Execution Engine** – Virtual machine for query execution
4. **Extended SQL** – Window functions, CTEs, transactions
5. **Database Integration** – SQLite/PostgreSQL backend

---


## 📅 **Last Updated**
December 27, 2025

---

## 🎯 **Status**
✅ **Phase 01**: Complete  
✅ **Phase 02**: Complete  
✅ **Phase 03**: Complete  
✅ **Web Interface**: Complete  
✅ **Documentation**: Complete  

---

*This project demonstrates a complete compiler frontend for SQL, implementing lexical, syntactic, and semantic analysis with professional error reporting and visualization.*
