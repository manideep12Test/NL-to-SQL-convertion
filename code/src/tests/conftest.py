import pytest
import os
import sqlite3
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys

# Add source directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

@pytest.fixture(scope="session")
def test_database():
    """Create a test database with sample banking data."""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    conn = sqlite3.connect(temp_db.name)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            type TEXT,
            balance REAL,
            open_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE transactions (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            type TEXT,
            amount REAL,
            date TEXT,
            description TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE branches (
            id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            manager_id TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE employees (
            id TEXT PRIMARY KEY,
            branch_id TEXT,
            name TEXT,
            position TEXT,
            hire_date TEXT,
            FOREIGN KEY (branch_id) REFERENCES branches (id)
        )
    ''')
    
    # Insert test data
    test_customers = [
        ('C001', 'John Smith', 'john.smith@email.com', '555-0101', '123 Main St'),
        ('C002', 'Jane Doe', 'jane.doe@email.com', '555-0102', '456 Oak Ave'),
        ('C003', 'Bob Johnson', 'bob.johnson@email.com', '555-0103', '789 Pine Rd'),
    ]
    
    test_accounts = [
        ('A001', 'C001', 'checking', 1500.00, '2023-01-15'),
        ('A002', 'C001', 'savings', 5000.00, '2023-01-15'),
        ('A003', 'C002', 'checking', 750.00, '2023-02-20'),
        ('A004', 'C003', 'savings', 10000.00, '2023-03-10'),
    ]
    
    test_transactions = [
        ('T001', 'A001', 'deposit', 1000.00, '2024-08-01', 'Initial deposit'),
        ('T002', 'A001', 'withdrawal', 200.00, '2024-08-15', 'ATM withdrawal'),
        ('T003', 'A002', 'deposit', 2000.00, '2024-08-20', 'Salary deposit'),
        ('T004', 'A003', 'withdrawal', 150.00, '2024-08-25', 'Grocery purchase'),
        ('T005', 'A001', 'withdrawal', 600.00, '2024-08-28', 'Rent payment'),
    ]
    
    cursor.executemany('INSERT INTO customers VALUES (?, ?, ?, ?, ?)', test_customers)
    cursor.executemany('INSERT INTO accounts VALUES (?, ?, ?, ?, ?)', test_accounts)
    cursor.executemany('INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)', test_transactions)
    
    conn.commit()
    conn.close()
    
    yield temp_db.name
    
    # Cleanup
    os.unlink(temp_db.name)

@pytest.fixture
def mock_gemini_llm():
    """Mock Gemini LLM for testing."""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "SELECT * FROM customers WHERE name LIKE '%Smith%' LIMIT 1000"
    mock_llm.invoke.return_value = mock_response
    return mock_llm

@pytest.fixture
def mock_google_api_key():
    """Mock Google API key for testing."""
    with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key'}):
        yield 'test_api_key'

@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return [
        "Show me all customers",
        "Find transactions over $500",
        "List account balances",
        "Show me transactions for customer with last name 'Smith'",
        "What is the total balance for all savings accounts?"
    ]

@pytest.fixture
def expected_sql_patterns():
    """Expected SQL patterns for sample queries."""
    return {
        "Show me all customers": "SELECT * FROM customers",
        "Find transactions over $500": "SELECT * FROM transactions WHERE amount > 500",
        "List account balances": "SELECT * FROM accounts",
        "Show me transactions for customer with last name 'Smith'": "SELECT.*FROM.*transactions.*JOIN.*customers.*Smith",
        "What is the total balance for all savings accounts?": "SELECT.*SUM.*balance.*FROM accounts.*WHERE.*type.*savings"
    }

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Create test fixtures directory
    fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    os.makedirs(fixtures_dir, exist_ok=True)
    
    yield
    
    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
