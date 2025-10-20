# Test package initialization
import sys
import os

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Test constants
TEST_DB_PATH = os.path.join(current_dir, "fixtures", "test_banking.db")
MOCK_API_KEY = "test_api_key_for_testing"
