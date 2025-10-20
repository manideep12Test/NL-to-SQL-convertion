
import os
import sqlite3
import pandas as pd
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

class DatabaseManager:
    def get_tables(self) -> List[str]:
        """
        Returns a list of all table names in the database (alias for get_table_names).
        """
        return self.get_table_names()
    """
    Comprehensive DatabaseManager for banking NL-to-SQL system.
    Handles schema/data setup, query execution, validation, introspection, backup, and banking-specific analytics.
    """
    def __init__(self, db_path: str = "banking.db", schema_file: str = "banking_schema_sqlite.sql", data_file: str = "banking_data.sql"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_path)
        self.schema_file = os.path.join(base_dir, schema_file)
        self.data_file = os.path.join(base_dir, data_file)
        self.logger = self.setup_logging()
        self.query_cache = {}
        
        # Force close any existing connections to prevent file locking
        self.force_close_database_connections()
        
        # Check if database exists and is properly initialized
        if self.is_database_initialized():
            self.logger.info(f"Using existing database: {self.db_path}")
        else:
            self.logger.info(f"Setting up new database: {self.db_path}")
            self.setup_database()

    def get_table_info(self, table_name: str) -> dict:
        """
        Returns schema and row count for a given table.
        """
        return {
            "schema": self.get_table_schema(table_name),
            "row_count": self.get_table_row_count(table_name)
        }

    def get_row_count(self, table_name: str) -> int:
        """
        Returns the number of rows in a given table (alias for get_table_row_count).
        """
        return self.get_table_row_count(table_name)

    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Returns the column names for a given table (alias for get_column_names).
        """
        return self.get_column_names(table_name)

    # --- Logging ---
    def setup_logging(self):
        logger = logging.getLogger("DatabaseManager")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        if not logger.hasHandlers():
            logger.addHandler(handler)
        return logger

    def log_query_execution(self, query: str, execution_time: float, row_count: int):
        self.logger.info(f"Executed: {query} | Time: {execution_time:.2f}s | Rows: {row_count}")

    def log_error(self, error: Exception, context: str):
        self.logger.error(f"Error in {context}: {error}")

    # --- Setup & Initialization ---
    def force_close_database_connections(self):
        """
        Force close any existing database connections to prevent file locking issues.
        """
        try:
            import gc
            gc.collect()  # Force garbage collection to close any unreferenced connections
            
            # Additional cleanup if needed
            if hasattr(self, '_active_connections'):
                for conn in self._active_connections:
                    try:
                        conn.close()
                    except:
                        pass
                self._active_connections = []
                
        except Exception as e:
            self.log_error(e, "force_close_database_connections")

    def is_database_initialized(self) -> bool:
        """
        Check if the database exists and has the required tables with data.
        """
        try:
            if not os.path.exists(self.db_path):
                return False
            
            # Test connection
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Expected tables (you can modify this list based on your schema)
            expected_tables = ['customers', 'accounts', 'transactions', 'branches']
            
            # Check if all expected tables exist
            if not all(table in tables for table in expected_tables):
                self.close_connection(conn)
                return False
            
            # Check if tables have data
            for table in expected_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    self.close_connection(conn)
                    return False
            
            self.close_connection(conn)
            return True
            
        except Exception as e:
            self.log_error(e, "is_database_initialized")
            return False

    def setup_database(self):
        self.verify_sql_file_exists(self.schema_file)
        self.verify_sql_file_exists(self.data_file)
        self.create_database_from_schema()
        self.populate_database_with_data()
        self.verify_database_integrity()

    def verify_sql_file_exists(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            self.log_error(FileNotFoundError(f"File not found: {file_path}"), "verify_sql_file_exists")
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        return True

    def execute_sql_file(self, file_path: str):
        """
        Reads and executes SQL file with robust error handling and logging.
        """
        conn = None
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"SQL file not found: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            self.logger.info(f"Executed SQL file: {file_path}")
        except FileNotFoundError as fnf:
            self.log_error(fnf, f"execute_sql_file: {file_path}")
            raise
        except sqlite3.DatabaseError as db_err:
            self.log_error(db_err, f"execute_sql_file: {file_path}")
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            self.log_error(e, f"execute_sql_file: {file_path}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.close_connection(conn)

    def create_database_from_schema(self):
        """Create database schema, skipping if tables already exist"""
        try:
            self.execute_sql_file(self.schema_file)
        except sqlite3.DatabaseError as e:
            if "already exists" in str(e):
                self.logger.info("Database schema already exists, skipping creation")
            else:
                raise

    def populate_database_with_data(self):
        """Populate database with data, skipping if data already exists"""
        try:
            self.execute_sql_file(self.data_file)
        except sqlite3.DatabaseError as e:
            if "UNIQUE constraint failed" in str(e) or "already exists" in str(e):
                self.logger.info("Database data already exists, skipping population")
            else:
                raise

    def verify_database_integrity(self) -> bool:
        try:
            tables = self.get_table_names()
            for table in tables:
                if self.get_table_row_count(table) == 0:
                    self.log_error(Exception(f"No data in table: {table}"), "verify_database_integrity")
                    return False
            return True
        except Exception as e:
            self.log_error(e, "verify_database_integrity")
            return False

    # --- Connection Management ---
    def get_connection(self, retries: int = 3, delay: float = 1.0) -> sqlite3.Connection:
        """
        Returns SQLite connection with retry logic and connection pooling.
        """
        attempt = 0
        while attempt < retries:
            try:
                # Connection pooling: use a pool if available (for production, use SQLAlchemy or external pool)
                conn = sqlite3.connect(self.db_path, timeout=10)
                return conn
            except sqlite3.OperationalError as e:
                self.log_error(e, f"get_connection attempt {attempt+1}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
                attempt += 1
        raise sqlite3.OperationalError(f"Failed to connect to database after {retries} attempts.")

    def get_connection_with_row_factory(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close_connection(self, conn: sqlite3.Connection):
        try:
            conn.close()
        except Exception as e:
            self.log_error(e, "close_connection")

    def test_connection(self) -> bool:
        try:
            conn = self.get_connection()
            self.close_connection(conn)
            return True
        except Exception as e:
            self.log_error(e, "test_connection")
            return False

    # --- Query Execution ---
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            self.log_error(e, "execute_query")
            return pd.DataFrame()
        finally:
            self.close_connection(conn)

    def execute_non_query(self, query: str, params: Optional[Tuple] = None) -> int:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.log_error(e, "execute_non_query")
            return 0
        finally:
            self.close_connection(conn)

    def execute_query_with_metadata(self, query: str) -> Dict[str, Any]:
        start = time.time()
        df = self.execute_query(query)
        exec_time = time.time() - start
        row_count = len(df)
        self.log_query_execution(query, exec_time, row_count)
        return {"data": df, "execution_time": exec_time, "row_count": row_count}

    def execute_raw_sql(self, sql_statement: str):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executescript(sql_statement)
            conn.commit()
        except Exception as e:
            self.log_error(e, "execute_raw_sql")
            raise
        finally:
            self.close_connection(conn)

    # --- Introspection ---
    def get_table_names(self) -> List[str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        except Exception as e:
            self.log_error(e, "get_table_names")
            return []
        finally:
            self.close_connection(conn)

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
            return columns
        except Exception as e:
            self.log_error(e, "get_table_schema")
            return []
        finally:
            self.close_connection(conn)

    def get_database_schema(self) -> Dict[str, Any]:
        schema = {}
        for table in self.get_table_names():
            schema[table] = {
                "columns": self.get_table_schema(table),
                "sample_data": self.execute_query(f"SELECT * FROM {table} LIMIT 5")
            }
        return schema

    def get_table_row_count(self, table_name: str) -> int:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            self.log_error(e, "get_table_row_count")
            return 0
        finally:
            self.close_connection(conn)

    def get_column_names(self, table_name: str) -> List[str]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in cursor.fetchall()]
            return columns
        except Exception as e:
            self.log_error(e, "get_column_names")
            return []
        finally:
            self.close_connection(conn)

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            fks = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
            return fks
        except Exception as e:
            self.log_error(e, "get_foreign_keys")
            return []
        finally:
            self.close_connection(conn)

    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """
        Returns sample data from a table with the specified limit.
        """
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            self.log_error(e, "get_sample_data")
            return pd.DataFrame()

    def get_query_results_with_metadata(self, query: str) -> Dict[str, Any]:
        """
        Returns query results with execution metadata (alias for execute_query_with_metadata).
        """
        return self.execute_query_with_metadata(query)

    # --- Validation & Safety ---
    def validate_query_safety(self, query: str) -> bool:
        q = query.upper()
        if "DROP" in q or ("DELETE" in q and "WHERE" not in q):
            return False
        return True

    def validate_table_exists(self, table_name: str) -> bool:
        return table_name in self.get_table_names()

    def validate_columns_exist(self, table_name: str, columns: List[str]) -> bool:
        table_columns = self.get_column_names(table_name)
        return all(col in table_columns for col in columns)

    def sanitize_input(self, input_string: str) -> str:
        return input_string.replace("'", "''")

    def check_database_health(self) -> Dict[str, Any]:
        return {
            "connection": self.test_connection(),
            "integrity": self.verify_database_integrity(),
            "tables": self.get_table_names()
        }

# ...existing code...

if __name__ == "__main__":
    print("Initializing banking database...")
    db_manager = None
    try:
        db_manager = DatabaseManager()
    except Exception as e:
        print(f"Error during database initialization: {e}")
    if db_manager:
        health = db_manager.check_database_health()
        print(f"Database health: {health}")
        print("Database initialization complete.")

    # --- Data Management ---
    def backup_database(self, backup_path: str) -> bool:
        try:
            import shutil
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_file = f"{backup_path}/banking_backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_file)
            return True
        except Exception as e:
            self.log_error(e, "backup_database")
            return False

    def restore_database(self, backup_path: str) -> bool:
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            self.log_error(e, "restore_database")
            return False

    def export_table_to_csv(self, table_name: str, output_path: str) -> bool:
        try:
            df = self.execute_query(f"SELECT * FROM {table_name}")
            df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            self.log_error(e, "export_table_to_csv")
            return False

    def import_csv_to_table(self, csv_path: str, table_name: str) -> bool:
        try:
            df = pd.read_csv(csv_path)
            conn = self.get_connection()
            df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.commit()
            return True
        except Exception as e:
            self.log_error(e, "import_csv_to_table")
            return False
        finally:
            self.close_connection(conn)

    def reset_database(self):
        self.create_database_from_schema()
        self.populate_database_with_data()

    # --- Banking-Specific Methods ---
    def get_customer_summary(self) -> pd.DataFrame:
        query = """
        SELECT c.id, c.name, COUNT(a.id) as account_count, SUM(a.balance) as total_balance
        FROM customers c
        LEFT JOIN accounts a ON c.id = a.customer_id
        GROUP BY c.id, c.name
        """
        return self.execute_query(query)

    def get_account_balances(self) -> pd.DataFrame:
        query = """
        SELECT a.id, a.balance, c.name as customer_name
        FROM accounts a
        JOIN customers c ON a.customer_id = c.id
        """
        return self.execute_query(query)

    def get_recent_transactions(self, days: int = 7) -> pd.DataFrame:
        query = f"""
        SELECT * FROM transactions
        WHERE date >= DATE('now', '-{days} days')
        ORDER BY date DESC
        """
        return self.execute_query(query)

    def get_transaction_categories(self) -> List[str]:
        query = "SELECT DISTINCT type FROM transactions"
        df = self.execute_query(query)
        return df['type'].tolist() if not df.empty else []

    def get_spending_by_category(self) -> pd.DataFrame:
        query = """
        SELECT type, SUM(amount) as total_spent
        FROM transactions
        WHERE amount < 0
        GROUP BY type
        ORDER BY total_spent ASC
        """
        return self.execute_query(query)

    def get_large_transactions(self, threshold: float = 1000) -> pd.DataFrame:
        query = f"SELECT * FROM transactions WHERE ABS(amount) > {threshold} ORDER BY amount DESC"
        return self.execute_query(query)

    # --- Banking-Specific Helper Methods ---
    def get_customer_accounts(self, customer_id: int) -> pd.DataFrame:
        query = f"SELECT * FROM accounts WHERE customer_id = {customer_id}"
        return self.execute_query(query)

    def get_customer_transactions(self, customer_id: int) -> pd.DataFrame:
        query = f"SELECT t.* FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.customer_id = {customer_id}"
        return self.execute_query(query)

    def get_account_transactions(self, account_id: int) -> pd.DataFrame:
        query = f"SELECT * FROM transactions WHERE account_id = {account_id}"
        return self.execute_query(query)

    def get_top_customers_by_balance(self, top_n: int = 5) -> pd.DataFrame:
        query = f"SELECT c.id, c.name, SUM(a.balance) as total_balance FROM customers c JOIN accounts a ON c.id = a.customer_id GROUP BY c.id, c.name ORDER BY total_balance DESC LIMIT {top_n}"
        return self.execute_query(query)

    def get_transaction_summary(self) -> pd.DataFrame:
        query = "SELECT type, COUNT(*) as count, SUM(amount) as total FROM transactions GROUP BY type"
        return self.execute_query(query)
