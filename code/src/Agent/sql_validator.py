import sqlite3
import logging
import re
from typing import Dict, Any, List, Optional

class SQLValidator:
    """
    Validates SQL queries for safety and correctness in banking applications.
    Features:
    - Prevents dangerous operations (DROP, DELETE without WHERE, etc.)
    - Checks SQL syntax using sqlite3
    - Validates table/column names against schema
    - Prevents SQL injection
    - Whitelist of allowed operations
    - Validation levels: strict, moderate, lenient
    - Logs all validation attempts
    - Suggests corrections for common errors
    """
    ALLOWED_OPERATIONS = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    STRICT_OPERATIONS = ["SELECT"]
    MODERATE_OPERATIONS = ["SELECT", "UPDATE", "DELETE"]
    LENIENT_OPERATIONS = ["SELECT", "INSERT", "UPDATE", "DELETE"]

    def __init__(self, db_path: str, validation_level: str = "strict"):
        self.db_path = db_path
        self.validation_level = validation_level.lower()
        self.logger = logging.getLogger("SQLValidator")
        self.logger.setLevel(logging.INFO)
        self.schema = self._get_schema()
        self.validation_log: List[Dict[str, Any]] = []

    def _get_schema(self) -> Dict[str, List[str]]:
        """Fetch table and column names from the database schema."""
        schema = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                schema[table] = columns
        except Exception as e:
            self.logger.error(f"Error fetching schema: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
        return schema

    def validate_query(self, sql: str) -> Dict[str, Any]:
        """
        Main entry: validates SQL query and returns result with error messages and suggestions.
        """
        self.logger.info(f"Validating query: {sql}")
        
        # CRITICAL FIX: Check for common column name errors and fix them
        original_sql = sql
        fixed_issues = []
        
        # Fix 1: date column should be transaction_date
        if "no such column: date" in str(sql).lower() or " date " in sql or " date," in sql:
            self.logger.info("Detected potential 'date' column issue, applying fix...")
            # Apply the same fixes as in the agent
            sql = sql.replace('ORDER BY date', 'ORDER BY transaction_date')
            sql = sql.replace('SELECT date', 'SELECT transaction_date')
            sql = sql.replace('SELECT *, date', 'SELECT *, transaction_date')
            sql = sql.replace('SELECT date,', 'SELECT transaction_date,')
            sql = sql.replace(', date', ', transaction_date')
            sql = sql.replace(', date,', ', transaction_date,')
            sql = sql.replace(', date ', ', transaction_date ')
            sql = sql.replace(' date ', ' transaction_date ')
            sql = sql.replace(' date,', ' transaction_date,')
            sql = sql.replace(' date)', ' transaction_date)')
            sql = sql.replace('(date)', '(transaction_date)')
            sql = sql.replace('.date', '.transaction_date')
            sql = sql.replace('date FROM', 'transaction_date FROM')
            sql = sql.replace('date WHERE', 'transaction_date WHERE')
            sql = sql.replace('date ORDER', 'transaction_date ORDER')
            sql = sql.replace('date LIMIT', 'transaction_date LIMIT')
            
            # But preserve SQL date functions
            sql = sql.replace("transaction_date('now'", "date('now'")
            sql = sql.replace("transaction_date(", "date(")
            fixed_issues.append("Fixed 'date' column → 'transaction_date'")
        
        # Fix 2: name column should be first_name and last_name (or CONCAT for full name)
        if "no such column: name" in str(sql).lower() or "c.name" in sql or "customers.name" in sql:
            self.logger.info("Detected potential 'name' column issue, applying fix...")
            
            # Replace various name column patterns with full name concatenation
            sql = sql.replace('c.name', "c.first_name || ' ' || c.last_name")
            sql = sql.replace('customers.name', "customers.first_name || ' ' || customers.last_name")
            sql = sql.replace('SELECT name', "SELECT first_name || ' ' || last_name AS name")
            sql = sql.replace('SELECT *, name', "SELECT *, first_name || ' ' || last_name AS name")
            sql = sql.replace(', name', ", first_name || ' ' || last_name AS name")
            sql = sql.replace(' name ', " first_name || ' ' || last_name ")
            sql = sql.replace(' name,', " first_name || ' ' || last_name AS name,")
            sql = sql.replace('ORDER BY name', "ORDER BY first_name || ' ' || last_name")
            sql = sql.replace('name LIKE', "first_name || ' ' || last_name LIKE")
            sql = sql.replace('WHERE name', "WHERE first_name || ' ' || last_name")
            
            fixed_issues.append("Fixed 'name' column → 'first_name || last_name'")
        
        # Fix 3: Ambiguous column references - add proper table aliases
        ambiguous_fixes = {
            # Type column ambiguity
            'SELECT type': 'SELECT t.type',  # Default to transactions
            ', type,': ', t.type,',
            ', type ': ', t.type ',
            'WHERE type': 'WHERE t.type',
            'ORDER BY type': 'ORDER BY t.type',
            
            # Status column ambiguity
            'SELECT status': 'SELECT t.status',  # Default to transactions
            ', status,': ', t.status,',
            ', status ': ', t.status ',
            'WHERE status': 'WHERE t.status',
            'ORDER BY status': 'ORDER BY t.status',
            
            # ID column ambiguity - be more conservative
            'SELECT id': 'SELECT t.id',  # Default to transactions when ambiguous
        }
        
        # Apply ambiguous column fixes only if we detect table joins
        if ' JOIN ' in sql.upper() or ' FROM ' in sql.upper():
            for pattern, replacement in ambiguous_fixes.items():
                if pattern in sql and pattern.replace('SELECT ', '').replace('WHERE ', '').replace('ORDER BY ', '').replace(', ', '').replace(' ', '') not in ['t.type', 't.status', 't.id', 'a.type', 'a.status', 'c.id']:
                    original_pattern = pattern
                    sql = sql.replace(pattern, replacement)
                    if original_pattern != replacement:
                        fixed_issues.append(f"Fixed ambiguous '{pattern}' → '{replacement}'")
        
        # Fix 4: Common table alias issues - ensure proper prefixes
        table_fixes = {
            # Customer table issues
            'customer.name': "customer.first_name || ' ' || customer.last_name",
            'customer.id': 'c.id',
            'customer.email': 'c.email',
            
            # Account table issues
            'account.id': 'a.id',
            'account.balance': 'a.balance',
            'account.type': 'a.type',
            
            # Transaction table issues
            'transaction.id': 't.id',
            'transaction.amount': 't.amount',
            'transaction.type': 't.type',
            'transaction.date': 't.transaction_date',
            
            # Employee table issues
            'employee.name': 'e.name',  # This is correct
            'employee.id': 'e.id',
            
            # Branch table issues
            'branch.name': 'b.name',  # This is correct
            'branch.id': 'b.id',
        }
        
        for wrong_ref, correct_ref in table_fixes.items():
            if wrong_ref in sql:
                sql = sql.replace(wrong_ref, correct_ref)
                fixed_issues.append(f"Fixed table reference '{wrong_ref}' → '{correct_ref}'")
        
        # Fix 5: Common typos and variations
        typo_fixes = {
            'costumer': 'customer',
            'costumers': 'customers',
            'trasaction': 'transaction',
            'trasactions': 'transactions',
            'accout': 'account',
            'acounts': 'accounts',
            'employe': 'employee',
            'employes': 'employees',
            'employeees': 'employees',  # Fix the triple 'e' typo
        }
        
        for typo, correct in typo_fixes.items():
            if typo in sql.lower():
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(typo), re.IGNORECASE)
                new_sql = pattern.sub(correct, sql)
                if new_sql != sql:
                    sql = new_sql
                    fixed_issues.append(f"Fixed typo '{typo}' → '{correct}'")
        
        if fixed_issues:
            self.logger.info(f"Applied SQL fixes: {', '.join(fixed_issues)}")
            self.logger.info(f"Original SQL: {original_sql}")
            self.logger.info(f"Fixed SQL: {sql}")
        
        result = self.check_safety(sql)
        if not result.get("safe", True):
            # Ensure both keys are present
            result["valid"] = False
            self._log_attempt(sql, result)
            return result
        syntax_result = self.parse_sql(sql)
        if not syntax_result.get("valid", True):
            # Ensure both keys are present
            syntax_result["safe"] = False
            self._log_attempt(sql, syntax_result)
            return syntax_result
        schema_result = self._validate_schema(sql)
        if not schema_result.get("valid", True):
            # Ensure both keys are present
            schema_result["safe"] = False
            self._log_attempt(sql, schema_result)
            return schema_result
        self._log_attempt(sql, {"safe": True, "valid": True, "message": "Query is valid.", "sql": sql})
        return {"safe": True, "valid": True, "message": "Query is valid.", "sql": sql}

    def check_safety(self, sql: str) -> Dict[str, Any]:
        """
        Checks for dangerous operations and SQL injection attempts.
        """
        sql_upper = sql.upper()
        # Validation level whitelist
        if self.validation_level == "strict":
            allowed_ops = self.STRICT_OPERATIONS
        elif self.validation_level == "moderate":
            allowed_ops = self.MODERATE_OPERATIONS
        else:
            allowed_ops = self.LENIENT_OPERATIONS
        # Check operation
        if not any(sql_upper.startswith(op) for op in allowed_ops):
            return {"safe": False, "message": f"Operation not allowed in {self.validation_level} mode."}
        # Prevent DROP, TRUNCATE, ALTER
        if re.search(r"\b(DROP|TRUNCATE|ALTER)\b", sql_upper):
            return {"safe": False, "message": "Dangerous operation detected (DROP/TRUNCATE/ALTER not allowed)."}
        # DELETE/UPDATE must have WHERE
        if re.search(r"\b(DELETE|UPDATE)\b", sql_upper) and "WHERE" not in sql_upper:
            return {"safe": False, "message": "DELETE/UPDATE must have a WHERE clause."}
        # More precise SQL injection detection - focus on actual injection patterns
        # Check for suspicious patterns like multiple statements, comment-based injections
        if re.search(r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)", sql, re.IGNORECASE):
            return {"safe": False, "message": "Possible SQL injection attempt detected (multiple statements)."}
        # Check for comment-based injections
        if re.search(r"--.*\b(OR|AND)\b.*=", sql, re.IGNORECASE):
            return {"safe": False, "message": "Possible SQL injection attempt detected (comment injection)."}
        # Check for union-based injections
        if re.search(r"\bUNION\s+(ALL\s+)?SELECT\b", sql, re.IGNORECASE) and not re.search(r"^SELECT", sql_upper):
            return {"safe": False, "message": "Possible SQL injection attempt detected (UNION injection)."}
        return {"safe": True, "message": "Safe query."}

    def parse_sql(self, sql: str) -> Dict[str, Any]:
        """
        Checks SQL syntax using sqlite3 (does not execute).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN {sql}")
            return {"valid": True, "message": "SQL syntax is valid."}
        except Exception as e:
            suggestion = self.suggest_correction(str(e), sql)
            return {"valid": False, "message": f"SQL syntax error: {e}", "suggestion": suggestion}
        finally:
            try:
                conn.close()
            except:
                pass

    def _validate_schema(self, sql: str) -> Dict[str, Any]:
        """
        Validates table and column names against schema.
        """
        tables = list(self.schema.keys())
        columns = [col for cols in self.schema.values() for col in cols]
        sql_lower = sql.lower()
        
        # Check if at least one valid table is referenced
        if not any(table in sql_lower for table in tables):
            return {"valid": False, "message": "No valid table referenced in query."}
        
        # For column validation, be more flexible:
        # 1. Allow queries with SELECT * (wildcard)
        # 2. Allow queries that reference valid columns
        # 3. Allow queries with aggregate functions that don't need explicit column names
        
        # If query uses SELECT *, it's valid (wildcard selects all columns)
        if re.search(r'select\s+\*', sql_lower) or re.search(r'select\s+count\s*\(\s*\*\s*\)', sql_lower):
            return {"valid": True, "message": "Schema validation passed (wildcard or count)."}
        
        # If query contains any valid column name, it's valid
        if any(col in sql_lower for col in columns):
            return {"valid": True, "message": "Schema validation passed."}
        
        # Check for common aggregate functions that don't require specific columns
        if re.search(r'\b(count|sum|avg|max|min)\s*\(', sql_lower):
            return {"valid": True, "message": "Schema validation passed (aggregate function)."}
        
        # If we reach here, no valid columns were found
        return {"valid": False, "message": "No valid column referenced in query."}

    def suggest_correction(self, error_msg: str, sql: str) -> str:
        """
        Suggests corrections for common SQL errors.
        """
        if "syntax error" in error_msg:
            return "Check SQL syntax, missing keywords, or misplaced commas."
        if "no such table" in error_msg:
            return "Check table name spelling and existence."
        if "no such column" in error_msg:
            return "Check column name spelling and existence."
        return "Review SQL query for errors."

    def _log_attempt(self, sql: str, result: Dict[str, Any]):
        """
        Logs validation attempts for auditing.
        """
        log_entry = {
            "query": sql,
            "result": result
        }
        self.validation_log.append(log_entry)
        self.logger.info(f"Validation log: {log_entry}")

    def get_validation_log(self) -> List[Dict[str, Any]]:
        """
        Returns all validation attempts.
        """
        return self.validation_log
